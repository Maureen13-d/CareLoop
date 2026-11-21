"use client";

import { useMemo, useState } from "react";
import { controlClasses } from "@/components/ui/field";
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
      setError(
        booklets.length === 0
          ? "No booklet is linked to this account, so this reading is not sent. If you feel unwell, go to the nearest clinic."
          : "Choose a booklet.",
      );
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

  const LAMPS = [
    { level: "green", word: "Green", meaning: "A usual day", dot: "bg-[#2f8a4c]" },
    { level: "yellow", word: "Yellow", meaning: "A navigator may call", dot: "bg-[#d99a1e]" },
    { level: "red", word: "Red", meaning: "Go to a clinic now", dot: "bg-danger" },
  ];

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,24rem)]">
      <section aria-labelledby="reading-heading" className="space-y-6 rounded-2xl border border-line bg-surface p-5 shadow-raised sm:p-6">
        <h2 id="reading-heading" className="text-lg">
          The reading
        </h2>
        {booklets.length > 1 ? (
          <div className="space-y-1.5">
            <label htmlFor="hub-booklet" className="block text-sm font-medium text-ink">
              Booklet
            </label>
            <select
              id="hub-booklet"
              className={controlClasses}
              value={booklet}
              onChange={(event) => setBooklet(event.target.value)}
            >
              {booklets.map((item) => (
                <option key={item.ref} value={item.ref}>
                  {item.ref}, {item.name}
                </option>
              ))}
            </select>
          </div>
        ) : booklets.length === 1 ? (
          <p className="text-sm text-ink-2">
            Sending to {booklets[0].name.toLowerCase()}, <span className="font-medium text-ink">{booklets[0].ref}</span>. The light
            updates as you move the reading.
          </p>
        ) : (
          <p className="text-sm text-ink-2">The light updates as you move the reading. No booklet is linked to this account.</p>
        )}

        <div className="grid gap-5 sm:grid-cols-3">
          <Slider label="Systolic" unit="mmHg" value={sys} min={80} max={200} onChange={setSys} />
          <Slider label="Diastolic" unit="mmHg" value={dia} min={40} max={140} onChange={setDia} />
          <Slider label="Pulse" unit="bpm" value={pulse} min={40} max={160} onChange={setPulse} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label htmlFor="hub-urine" className="block text-sm font-medium text-ink">
              Urine protein
            </label>
            <select id="hub-urine" className={controlClasses} value={urine} onChange={(event) => setUrine(event.target.value)}>
              {["neg", "trace", "1+", "2+", "3+", "unknown"].map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <label htmlFor="hub-hb" className="block text-sm font-medium text-ink">
              Haemoglobin band
            </label>
            <select id="hub-hb" className={controlClasses} value={hb} onChange={(event) => setHb(event.target.value)}>
              {["normal", "mild", "moderate", "severe", "unknown"].map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </div>
        </div>

        <fieldset>
          <legend className="text-sm font-medium text-ink">Danger signs</legend>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {SIGNS.map(([id, label]) => (
              <label
                key={id}
                className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border border-line bg-surface px-3 text-sm has-[:checked]:border-danger/40 has-[:checked]:bg-danger-bg"
              >
                <input type="checkbox" className="size-4 accent-deep" checked={signs.includes(id)} onChange={() => toggle(id)} />
                {label}
              </label>
            ))}
          </div>
        </fieldset>
      </section>

      <section
        aria-labelledby="device-heading"
        className="on-dark space-y-5 rounded-2xl bg-emerald p-5 text-white shadow-float sm:p-6 lg:sticky lg:top-6"
      >
        <div className="flex items-center justify-between gap-2">
          <h2 id="device-heading" className="text-lg text-white">
            Hub HUB-0007
          </h2>
          <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-[0.8125rem] text-on-dark">Simulated</span>
        </div>

        <ul className="space-y-2" aria-label="On-device light">
          {LAMPS.map((lamp) => {
            const on = local.level === lamp.level;
            return (
              <li
                key={lamp.level}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 ${on ? "bg-white text-ink" : "bg-white/[0.06] text-on-dark-2"}`}
              >
                <span
                  aria-hidden="true"
                  className={`size-3.5 shrink-0 rounded-full ${on ? `${lamp.dot} ring-4 ring-black/5` : "bg-white/20"}`}
                />
                <span className="text-sm">
                  <span className="font-semibold">{lamp.word}</span>, {lamp.meaning.toLowerCase()}
                </span>
                <span className="ml-auto text-[0.75rem] font-medium">{on ? "On" : "Off"}</span>
              </li>
            );
          })}
        </ul>

        <div className="rounded-xl bg-black/20 px-4 py-3 text-sm">
          <p className="text-on-dark-2">Reply the person would get</p>
          <p className="mt-1 text-white">{reply}</p>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="hub-language" className="block text-sm text-on-dark">
            Reply language
          </label>
          <select
            id="hub-language"
            className="min-h-10 w-full rounded-xl border border-white/20 bg-white/10 px-3 text-sm text-white [&>option]:text-ink"
            value={language}
            onChange={(event) => setLanguage(event.target.value as "en" | "sw")}
          >
            <option value="en">English</option>
            <option value="sw">Swahili</option>
          </select>
        </div>

        <fieldset>
          <legend className="text-sm text-on-dark">Link</legend>
          <div className="mt-2 grid grid-cols-3 gap-1 rounded-full bg-black/20 p-1">
            {(["data", "sms", "offline"] as Link[]).map((item) => (
              <label
                key={item}
                className="flex min-h-9 cursor-pointer items-center justify-center rounded-full text-sm text-on-dark has-[:checked]:bg-white has-[:checked]:font-medium has-[:checked]:text-emerald has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-on-dark"
              >
                <input type="radio" name="link" className="sr-only" checked={link === item} onChange={() => setLink(item)} />
                {item === "data" ? "Data" : item === "sms" ? "SMS" : "Offline"}
              </label>
            ))}
          </div>
        </fieldset>

        <div className="space-y-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => submit(false)}
            className="min-h-11 w-full rounded-full bg-on-dark text-[0.9375rem] font-medium text-emerald hover:bg-white disabled:opacity-60"
          >
            {busy ? "Sending…" : "Send reading"}
          </button>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => submit(true)}
              className="min-h-10 rounded-full border border-white/25 text-sm text-white hover:bg-white/10 disabled:opacity-60"
            >
              Send it again
            </button>
            <button
              type="button"
              disabled={busy || queue.length === 0}
              onClick={flush}
              className="min-h-10 rounded-full border border-white/25 text-sm text-white hover:bg-white/10 disabled:opacity-50"
            >
              Send {queue.length} queued
            </button>
          </div>
        </div>

        <div aria-live="polite" className="space-y-2">
          {error ? <p className="rounded-xl bg-danger-bg px-3 py-2 text-sm text-danger">{error}</p> : null}
          {result ? (
            <p className="rounded-xl bg-white/10 px-3 py-2 text-sm text-white">
              Server label: <span className="font-semibold">{result.level}</span>
              {result.duplicate ? ", duplicate ignored" : ""}, sent by {result.via}. A colour is a label, not a diagnosis.
            </p>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function Slider({
  label,
  unit,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  unit: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  const id = `hub-${label.toLowerCase()}`;
  return (
    <div>
      <label htmlFor={id} className="flex items-baseline justify-between text-sm font-medium text-ink">
        {label}
        <span className="text-lg font-semibold tabular-nums">
          {value} <span className="text-[0.75rem] font-normal text-ink-2">{unit}</span>
        </span>
      </label>
      <input
        id={id}
        className="mt-2 block w-full accent-deep"
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </div>
  );
}
