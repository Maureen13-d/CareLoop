"use client";

import { AslSample, SIGN_COUNT } from "@/ksl/AslSample";
import { useEffect, useState } from "react";
import { simulatedCode } from "./actions";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const button = "min-h-14 w-full rounded-2xl bg-lagoon px-4 text-lg text-white";
const answerButton = "min-h-12 rounded-2xl bg-lagoon px-3 text-base text-white";
const FALLBACK_ANSWERS = [
  { id: "been", label: "I have been" },
  { id: "not_yet", label: "Not yet" },
  { id: "worse", label: "I feel worse" },
  { id: "transport", label: "Transport" },
  { id: "fear", label: "Fear" },
];

type Reply = {
  reply_text: string;
  spoken_text?: string;
  escalation_label: string | null;
  quick_replies: { id: string; label: string }[];
  access_token?: string;
  template_id?: string;
  ksl?: { caption?: string; available?: boolean };
};

function Guide({ text, danger }: { text: string; danger: boolean }) {
  const [muted, setMuted] = useState(false);
  const spoken = text;
  if (danger) {
    return (
      <section className="rounded-2xl border border-line bg-white p-4">
        <p className="text-sm">I am a guide, not a doctor. I help you get to care.</p>
        <p className="mt-3 text-2xl">{spoken}</p>
      </section>
    );
  }
  return (
    <section className="rounded-2xl border border-line bg-white p-4">
      <div className="mb-3 h-16 w-16 rounded-full bg-lagoon motion-reduce:animate-none motion-safe:animate-pulse" />
      <p className="text-sm">I am a guide, not a doctor. I help you get to care.</p>
      <p className="mt-3 text-xl">{spoken}</p>
      <button type="button" className="mt-3 min-h-12 underline" onClick={() => setMuted((value) => !value)}>
        {muted ? "Sound is off" : "Turn sound off"}
      </button>
      <Speak text={spoken} muted={muted} />
    </section>
  );
}

function Speak({ text, muted }: { text: string; muted: boolean }) {
  useEffect(() => {
    if (muted || typeof window === "undefined" || !window.speechSynthesis) return;
    const utter = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
    return () => window.speechSynthesis.cancel();
  }, [text, muted]);
  return null;
}

export function EnterFlow() {
  const [publicId, setPublicId] = useState("");
  const [code, setCode] = useState("");
  const [token, setToken] = useState("");
  const [hint, setHint] = useState("");
  const [reply, setReply] = useState<Reply | null>(null);
  const [error, setError] = useState("");
  const [language, setLanguage] = useState<"en" | "ksl">("en");
  const [signStep, setSignStep] = useState(0);

  async function start() {
    setError("");
    setHint("");
    try {
      const res = await fetch(`${API}/api/v1/followup/access/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ public_id: publicId, client_key: "web-demo" }),
      });
      if (!res.ok) {
        setError("That ID was not accepted.");
        return;
      }
      const dev = await simulatedCode(publicId);
      setHint(
        dev
          ? `SIMULATED code: ${dev.simulated_code}`
          : "Sign in on the login page first, then send the code again.",
      );
    } catch {
      setError("The card could not reach the server.");
    }
  }

  async function check() {
    setError("");
    const res = await fetch(`${API}/api/v1/followup/access/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ public_id: publicId, code, client_key: "web-demo" }),
    });
    const body = (await res.json()) as Reply & { error?: { message?: string } };
    if (!res.ok || !body.access_token) {
      setError("That ID or code was not accepted.");
      return;
    }
    setToken(body.access_token);
    await say(body.access_token, "");
  }

  async function say(bearer: string, message: string) {
    const path = language === "ksl" ? "/api/v1/ksl/talk" : "/api/v1/followup/talk";
    const body =
      language === "ksl"
        ? { message, channel: "web" }
        : { message, channel: "web", language: "en" };
    const res = await fetch(`${API}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${bearer}` },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      setError("That answer was not accepted.");
      return false;
    }
    const payload = (await res.json()) as Reply;
    setReply(payload);
    setError("");
    return true;
  }

  const danger = reply?.escalation_label === "danger_sign" || reply?.escalation_label === "worse";
  const signing = Boolean(token) && language === "ksl";
  const answers = reply?.quick_replies?.length ? reply.quick_replies : FALLBACK_ANSWERS;

  async function answer(id: string) {
    const accepted = await say(token, id);
    if (accepted) setSignStep((value) => Math.min(value + 1, SIGN_COUNT - 1));
  }

  return (
    <main
      className={
        signing
          ? "flex h-dvh max-h-dvh flex-col overflow-hidden bg-[#f7f1e6] text-ink"
          : "mx-auto min-h-screen max-w-md space-y-4 bg-white px-4 py-6 text-ink"
      }
    >
      {signing ? null : (
        <>
          <p className="text-sm text-lagoon">SYNTHETIC</p>
          <h1 className="text-3xl">Your card</h1>
        </>
      )}
      {!token ? (
        <div className="space-y-3">
          <div className="grid grid-cols-1 gap-2">
            <button className={button} type="button" onClick={() => setLanguage("en")}>
              {language === "en" ? "English selected" : "English"}
            </button>
            <button className={button} type="button" onClick={() => setLanguage("ksl")}>
              {language === "ksl" ? "American Sign Language selected" : "American Sign Language"}
            </button>
          </div>
          <p className="rounded-2xl border border-line bg-paper-2 p-3 text-sm">
            The avatar signs one line. You answer underneath. Then it signs the next line.
          </p>
          <label className="block text-lg">
            ID
            <input
              value={publicId}
              onChange={(event) => setPublicId(event.target.value)}
              className="mt-1 min-h-14 w-full rounded-2xl border border-line px-3 text-lg"
            />
          </label>
          <button className={button} type="button" onClick={start}>
            Send a code
          </button>
          {hint ? <p className="rounded-2xl bg-paper-2 p-3 text-sm">{hint}</p> : null}
          <label className="block text-lg">
            Code
            <input
              value={code}
              onChange={(event) => setCode(event.target.value)}
              className="mt-1 min-h-14 w-full rounded-2xl border border-line px-3 text-lg"
            />
          </label>
          <button className={button} type="button" onClick={check}>
            Continue
          </button>
        </div>
      ) : (
        language === "ksl" ? (
          <>
            <AslSample step={signStep} />
            <div className="grid shrink-0 grid-cols-2 gap-2 bg-white px-3 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
              {answers.map((item, index) => (
                <button
                  key={item.id}
                  className={`${answerButton} ${index === answers.length - 1 && answers.length % 2 === 1 ? "col-span-2" : ""}`}
                  type="button"
                  onClick={() => answer(item.id)}
                >
                  {item.label}
                </button>
              ))}
              {error ? <p className="col-span-2 text-sm">{error}</p> : null}
            </div>
          </>
        ) : (
          <div className="space-y-3">
            <Guide
              text={reply?.spoken_text || reply?.reply_text || "Your next step is to go to the clinic."}
              danger={Boolean(danger)}
            />
            <p className="text-lg">Have you been able to get to care?</p>
            <div className="grid grid-cols-1 gap-2">
              {(reply?.quick_replies ?? []).map((item) => (
                <button key={item.id} className={button} type="button" onClick={() => say(token, item.id)}>
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        )
      )}
      {error && !signing ? <p className="text-lg">{error}</p> : null}
    </main>
  );
}
