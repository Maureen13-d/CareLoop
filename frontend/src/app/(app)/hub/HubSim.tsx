"use client";

import { useMemo, useState } from "react";
import { sendHub } from "./actions";
import { encodeSms, renderSms, triageMaternal } from "@/lib/maternalTriage";

const SIGNS = [
  ["heavy_bleeding", "Heavy bleeding"],
  ["convulsion", "A fit"],
  ["severe_abdominal_pain", "Pain high in the belly"],
  ["difficulty_breathing", "Hard to breathe"],
  ["no_fetal_movement", "Movement has stopped"],
  ["fever_severe_weakness", "Fever and very weak"],
  ["leaking_fluid_fever", "Fluid and fever"],
  ["swelling_face_hands", "Swelling of the face or hands"],
  ["reduced_fetal_movement", "Less movement"],
  ["headache_severe", "Severe head pain"],
  ["vision_blurred", "Blurred vision"],
] as const;

const SW = {
  red: "Nenda kliniki iliyo karibu sasa. Mtu atakupigia.",
  yellow: "Mtu anaweza kupiga simu kuhusu hii. Jibu 1 kama unataka simu.",
  green: "Asante. Ukaguzi ujao ni siku ya kawaida. Jibu HELP wakati wowote.",
};

type Booklet = { ref: string; name: string };
type Link = "data" | "sms" | "offline";
type Result = { level: string; duplicate: boolean; via: string };

export function HubSim({ booklets }: { booklets: Booklet[] }) {
  const [sys, setSys] = useState(118);
  const [dia, setDia] = useState(76);
  const [pulse, setPulse] = useState(72);
  const [urine, setUrine] = useState("neg");
  const [hb, setHb] = useState("normal");
  const [signs, setSigns] = useState<string[]>([]);
  const [booklet, setBooklet] = useState(booklets[0]?.ref ?? "");
  const [link, setLink] = useState<Link>("data");
  const [language, setLanguage] = useState<"en" | "sw">("en");
  const [seq, setSeq] = useState(1);
  const [queue, setQueue] = useState<number[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const reading = useMemo(
    () => ({ systolic: sys, diastolic: dia, pulse, urine_protein: urine, hb_band: hb }),
    [sys, dia, pulse, urine, hb],
  );
  const local = triageMaternal(reading, signs, {});
  const reply = language === "sw" ? SW[local.level as keyof typeof SW] : renderSms(local.level);

  function toggle(sign: string) {
    setSigns((current) =>
      current.includes(sign) ? current.filter((item) => item !== sign) : [...current, sign],
    );
  }

  async function deliver(id: number, mode: "data" | "sms") {
    const clientId = `HUB-0007-${id}`;
    if (mode === "sms") {
      return sendHub("sms", {
        text: encodeSms("HUB-0007", id, reading, signs),
        pregnancy_ref: booklet,
      });
    }
    return sendHub("data", {
      device_id: "HUB-0007",
      client_reading_id: clientId,
      pregnancy_ref: booklet,
      systolic: sys,
      diastolic: dia,
      pulse,
      urine_protein: urine,
      hb_band: hb,
      danger_signs: signs,
      hub_local_level: local.level,
    });
  }

  async function submit(reuse: boolean) {
    setError(null);
    setResult(null);
    if (!booklet) {
      setError("Choose a booklet. Delete backend/careloop.db and restart the API if the list is empty.");
      return;
    }
    const id = reuse ? Math.max(1, seq - 1) : seq;
    if (link === "offline") {
      setQueue((current) => [...current, id]);
      if (!reuse) setSeq((current) => current + 1);
      setResult({ level: local.level, duplicate: false, via: "kept on the hub" });
      return;
    }
    setBusy(true);
    const sent = await deliver(id, link);
    setBusy(false);
    if (!sent.ok) {
      setError(sent.message);
      return;
    }
    if (!reuse) setSeq((current) => current + 1);
    setResult({ level: sent.level, duplicate: sent.duplicate, via: link === "sms" ? "SMS" : "data" });
  }

  async function flush() {
    setError(null);
    if (link === "offline" || queue.length === 0) return;
    setBusy(true);
    for (const id of queue) {
      const sent = await deliver(id, link);
      if (!sent.ok) {
        setBusy(false);
        setError(sent.message);
        return;
      }
      setResult({ level: sent.level, duplicate: sent.duplicate, via: "queued" });
    }
    setQueue([]);
    setBusy(false);
  }

  return (
    <div className="space-y-6">
      <fieldset className="space-y-3">
        <legend className="text-sm font-medium">Booklet</legend>
        <select
          className="min-h-12 w-full rounded-xl border border-line bg-white px-3"
          value={booklet}
          onChange={(event) => setBooklet(event.target.value)}
        >
          {booklets.length === 0 ? <option value="">No booklet seeded</option> : null}
          {booklets.map((item) => (
            <option key={item.ref} value={item.ref}>
              {item.ref} · {item.name}
            </option>
          ))}
        </select>
      </fieldset>

      <div className="grid gap-4 sm:grid-cols-3">
        <Slider label="Systolic" value={sys} min={80} max={200} onChange={setSys} />
        <Slider label="Diastolic" value={dia} min={40} max={140} onChange={setDia} />
        <Slider label="Pulse" value={pulse} min={40} max={160} onChange={setPulse} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">
          Urine protein
          <select className="mt-1 min-h-12 w-full rounded-xl border border-line bg-white px-3" value={urine} onChange={(event) => setUrine(event.target.value)}>
            {["neg", "trace", "1+", "2+", "3+", "unknown"].map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          Haemoglobin band
          <select className="mt-1 min-h-12 w-full rounded-xl border border-line bg-white px-3" value={hb} onChange={(event) => setHb(event.target.value)}>
            {["normal", "mild", "moderate", "severe", "unknown"].map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>

      <fieldset>
        <legend className="text-sm font-medium">Danger signs</legend>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {SIGNS.map(([id, label]) => (
            <label key={id} className="flex min-h-12 items-center gap-3 rounded-xl border border-line bg-white px-3">
              <input type="checkbox" checked={signs.includes(id)} onChange={() => toggle(id)} />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="text-sm font-medium">Link</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {(["data", "sms", "offline"] as Link[]).map((item) => (
            <label key={item} className="flex min-h-12 items-center gap-2 rounded-full border border-line bg-white px-4">
              <input type="radio" name="link" checked={link === item} onChange={() => setLink(item)} />
              {item === "data" ? "Data" : item === "sms" ? "SMS" : "Offline"}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid gap-2 sm:grid-cols-3" aria-label="On-device level">
        <Lamp word="Green · usual day" on={local.level === "green"} />
        <Lamp word="Yellow · navigator" on={local.level === "yellow"} />
        <Lamp word="Red · go now" on={local.level === "red"} />
      </div>
      <p className="text-sm">
        On-device label: {local.level}. {reply}
      </p>
      <label className="flex items-center gap-2 text-sm">
        Reply language
        <select className="min-h-12 rounded-xl border border-line bg-white px-3" value={language} onChange={(event) => setLanguage(event.target.value as "en" | "sw")}>
          <option value="en">English</option>
          <option value="sw">Swahili</option>
        </select>
      </label>

      <div className="flex flex-wrap gap-2">
        <button type="button" disabled={busy} onClick={() => submit(false)} className="min-h-12 rounded-full bg-lagoon px-4 text-white">
          Send reading
        </button>
        <button type="button" disabled={busy} onClick={() => submit(true)} className="min-h-12 rounded-full border border-line bg-white px-4">
          Send the same reading again
        </button>
        <button type="button" disabled={busy || queue.length === 0} onClick={flush} className="min-h-12 rounded-full border border-line bg-white px-4">
          Send {queue.length} queued
        </button>
      </div>
      {error ? <p className="text-sm text-danger">{error}</p> : null}
      {result ? (
        <p className="text-sm">
          Server label: {result.level}
          {result.duplicate ? " · duplicate ignored" : ""} · {result.via}. A colour is a label, not a diagnosis.
        </p>
      ) : null}
    </div>
  );
}

function Slider({ label, value, min, max, onChange }: { label: string; value: number; min: number; max: number; onChange: (value: number) => void }) {
  return (
    <label className="block text-sm">
      {label} · {value}
      <input className="mt-2 block w-full" type="range" min={min} max={max} value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}

function Lamp({ word, on }: { word: string; on: boolean }) {
  return (
    <p className={`min-h-12 rounded-2xl border-2 px-3 py-2 text-sm ${on ? "border-ink bg-white font-medium" : "border-line text-ink-soft"}`}>
      {word} · {on ? "on" : "off"}
    </p>
  );
}
