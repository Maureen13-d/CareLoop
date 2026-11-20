// Same decision as the server. Thresholds match rules/maternal_triage.yaml.
// PENDING CLINICAL REVIEW. A colour is a label, never a diagnosis.

const RULES = {
  rules_version: "0.1-pending-clinical-review",
  thresholds: { severe_systolic: 160, severe_diastolic: 110, high_systolic: 140, high_diastolic: 90, stale_days: 14 },
  urine_rank: { neg: 0, trace: 1, "1+": 2, "2+": 3, "3+": 4 },
  red_signs: [
    "heavy_bleeding",
    "convulsion",
    "severe_abdominal_pain",
    "difficulty_breathing",
    "no_fetal_movement",
    "fever_severe_weakness",
    "leaking_fluid_fever",
  ],
  neuro_signs: ["headache_severe", "vision_blurred", "convulsion"],
  yellow_signs: [
    "swelling_face_hands",
    "reduced_fetal_movement",
    "missed_visit",
    "headache_only",
    "fever",
    "leaking_fluid",
  ],
  hb_red: ["severe"],
  hb_yellow: ["moderate"],
  hb_in_range: ["normal", "mild"],
  key_measurements: ["systolic", "diastolic", "urine_protein", "hb_band"],
  gestation_past_20: ["20-28w", "28-36w", "36w+"],
  prior_yellow_escalates: true,
};

const SMS = {
  red: "Please go to the nearest clinic now. A person will contact you.",
  yellow: "A navigator can call you about your check. Reply 1 if you want a call.",
  green: "Thanks. Next check-in is on the usual day. Reply HELP anytime.",
};

function number(value) {
  if (value === null || value === undefined || value === "" || typeof value === "boolean") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function present(reading, key) {
  const value = reading[key];
  if (key === "systolic" || key === "diastolic") return number(value) !== null;
  if (key === "urine_protein") return typeof value === "string" && value in RULES.urine_rank;
  if (key === "hb_band") {
    const known = new Set([...RULES.hb_red, ...RULES.hb_yellow, ...RULES.hb_in_range]);
    return typeof value === "string" && known.has(value);
  }
  return value !== null && value !== undefined && value !== "";
}

export function triageMaternal(reading, dangerSigns, context) {
  const rules = RULES;
  const row = reading || {};
  const signs = (dangerSigns || []).filter((sign) => typeof sign === "string" && sign);
  const ctx = context || {};
  const limits = rules.thresholds;
  const fired = [];
  const reasons = [];
  const add = (ruleId, reason) => {
    if (!fired.includes(ruleId)) {
      fired.push(ruleId);
      reasons.push(reason);
    }
  };
  if (ctx.sos) add("SOS", "SOS");
  for (const sign of signs) {
    if (rules.red_signs.includes(sign)) add("RED_SIGN", sign);
  }
  if (signs.includes("headache_severe") && signs.includes("vision_blurred")) {
    add("NEURO_PAIR", "headache_with_vision");
  }
  const sys = number(row.systolic);
  const dia = number(row.diastolic);
  const severe = (sys !== null && sys >= limits.severe_systolic) || (dia !== null && dia >= limits.severe_diastolic);
  const high = (sys !== null && sys >= limits.high_systolic) || (dia !== null && dia >= limits.high_diastolic);
  if (severe) add("SEVERE_BP", "SEVERE_BP");
  const urine = row.urine_protein;
  const rank = typeof urine === "string" ? rules.urine_rank[urine] : undefined;
  const neuro = signs.some((sign) => rules.neuro_signs.includes(sign));
  if (high && rank !== undefined && rank >= rules.urine_rank["2+"]) add("HIGH_BP_PROTEIN", "HIGH_BP_WITH_PROTEIN");
  if (high && neuro) add("HIGH_BP_NEURO", "HIGH_BP_WITH_NEURO");
  const hb = row.hb_band;
  if (rules.hb_red.includes(hb)) add("SEVERE_HB", "SEVERE_HB");
  const redIds = ["SOS", "RED_SIGN", "NEURO_PAIR", "SEVERE_BP", "HIGH_BP_PROTEIN", "HIGH_BP_NEURO", "SEVERE_HB"];
  let red = redIds.some((rule) => fired.includes(rule));
  if (high && !severe) add("HIGH_BP", "HIGH_BP");
  if (rank !== undefined && rank >= rules.urine_rank["1+"] && !high) add("PROTEIN", "PROTEIN");
  if (rules.hb_yellow.includes(hb)) add("MODERATE_HB", "MODERATE_HB");
  for (const sign of signs) {
    if (rules.yellow_signs.includes(sign)) add("YELLOW_SIGN", sign);
  }
  if (ctx.missed_visit) add("MISSED_VISIT", "MISSED_VISIT");
  const missing = rules.key_measurements.filter((key) => !present(row, key));
  if (missing.length) {
    add("INCOMPLETE_DATA", "INCOMPLETE_DATA");
    if (missing.length >= 2) add("TWO_MISSING", "TWO_MISSING");
  }
  if (row.taken_at && ctx.now) {
    const ageMs = new Date(ctx.now).getTime() - new Date(row.taken_at).getTime();
    const ageDays = ageMs / 86400000;
    const gestation = ctx.gestation_band || row.gestation_band;
    if (rules.gestation_past_20.includes(gestation) && ageDays > limits.stale_days) {
      add("STALE_READING", "STALE_READING");
    }
  }
  const yellowIds = ["HIGH_BP", "PROTEIN", "MODERATE_HB", "YELLOW_SIGN", "MISSED_VISIT", "INCOMPLETE_DATA", "TWO_MISSING", "STALE_READING"];
  const yellow = yellowIds.some((rule) => fired.includes(rule));
  if (rules.prior_yellow_escalates && ctx.prior_level === "yellow" && (yellow || signs.length) && !red) {
    add("PRIOR_YELLOW", "PRIOR_YELLOW");
    red = true;
  }
  let level;
  if (red) level = "red";
  else if (yellow || missing.length) level = "yellow";
  else {
    const inRange =
      sys !== null &&
      dia !== null &&
      sys < limits.high_systolic &&
      dia < limits.high_diastolic &&
      rank !== undefined &&
      rank <= rules.urine_rank.trace &&
      rules.hb_in_range.includes(hb) &&
      signs.length === 0 &&
      !ctx.sos &&
      !ctx.missed_visit;
    level = inRange ? "green" : "yellow";
    if (level === "green") add("IN_RANGE", "IN_RANGE");
    else if (!fired.includes("INCOMPLETE_DATA")) add("INCOMPLETE_DATA", "INCOMPLETE_DATA");
  }
  return { level, rule_ids: fired, reasons, rules_version: rules.rules_version };
}

export function renderSms(level) {
  return SMS[level] || SMS.yellow;
}

export function checksum(body) {
  let sum = 0;
  for (const char of body) sum += char.charCodeAt(0);
  return (sum % 256).toString(16).padStart(2, "0");
}

const PROTEIN = { neg: "0", trace: "t", "1+": "1", "2+": "2", "3+": "3", unknown: "u" };
const SIGN = {
  headache_severe: "H",
  vision_blurred: "S",
  heavy_bleeding: "B",
  convulsion: "C",
  severe_abdominal_pain: "A",
  difficulty_breathing: "D",
  no_fetal_movement: "F",
  fever_severe_weakness: "W",
  leaking_fluid_fever: "L",
  swelling_face_hands: "E",
  reduced_fetal_movement: "M",
};

export function encodeSms(deviceId, seq, reading, signs) {
  const marks = (signs || []).map((sign) => SIGN[sign] || "").join("");
  const protein = PROTEIN[reading.urine_protein] || "u";
  const head = `R|${deviceId}|${seq}|${reading.systolic}|${reading.diastolic}|${reading.pulse}|${protein}|${marks}`;
  return `${head}|${checksum(head)}`;
}
