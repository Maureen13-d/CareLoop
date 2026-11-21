"use client";

import { CircleExclamationPoint, Volume2, VolumeX } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Wordmark } from "@/components/ui/brand";
import { controlClass, cx } from "@/components/ui";
import { simulatedCode } from "./actions";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const button =
  "min-h-14 w-full rounded-full bg-deep px-5 text-lg font-medium text-white transition-colors hover:bg-emerald disabled:opacity-55";
const choice =
  "min-h-14 w-full rounded-2xl border border-line bg-surface px-5 text-left text-lg font-medium text-ink transition-colors hover:border-teal hover:bg-mint";

type Reply = {
  reply_text: string;
  spoken_text?: string;
  escalation_label: string | null;
  quick_replies: { id: string; label: string }[];
  access_token?: string;
};

function Guide({ text, danger }: { text: string; danger: boolean }) {
  const [muted, setMuted] = useState(false);
  const spoken = text;
  if (danger) {
    return (
      <section aria-live="assertive" className="rounded-2xl border-2 border-danger bg-danger-bg p-5">
        <p className="text-sm text-danger">I am a guide, not a doctor. I help you get to care.</p>
        <p className="mt-3 flex gap-3 text-2xl font-semibold leading-snug text-danger">
          <CircleExclamationPoint aria-hidden="true" className="mt-1 size-7 shrink-0" />
          {spoken}
        </p>
      </section>
    );
  }
  return (
    <section aria-live="polite" className="rounded-2xl border border-line bg-surface p-5 shadow-raised">
      <div className="flex items-center gap-3">
        <span aria-hidden="true" className="relative flex size-12 items-center justify-center rounded-full bg-mint">
          <span
            className={cx(
              "size-5 rounded-full bg-teal",
              !muted && "motion-safe:animate-pulse",
            )}
          />
        </span>
        <p className="text-sm text-ink-2">I am a guide, not a doctor. I help you get to care.</p>
      </div>
      <p className="mt-4 text-xl leading-snug text-ink">{spoken}</p>
      <button
        type="button"
        className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-full px-2 text-[0.9375rem] font-medium text-teal-text hover:bg-mint"
        onClick={() => setMuted((value) => !value)}
      >
        {muted ? <VolumeX aria-hidden="true" className="size-5" /> : <Volume2 aria-hidden="true" className="size-5" />}
        {muted ? "Sound is off. Turn it on" : "Turn sound off"}
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

  async function start() {
    setError("");
    const res = await fetch(`${API}/api/v1/followup/access/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ public_id: publicId, client_key: "web-demo" }),
    });
    if (!res.ok) {
      setError("That ID or code was not accepted.");
      return;
    }
    const dev = await simulatedCode(publicId);
    setHint(dev ? `SIMULATED code: ${dev.simulated_code}` : "A code was sent. This demo can show it to staff.");
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
    const res = await fetch(`${API}/api/v1/followup/talk`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${bearer}` },
      body: JSON.stringify({ message, channel: "web", language: "en" }),
    });
    const body = (await res.json()) as Reply;
    setReply(body);
  }

  const danger = reply?.escalation_label === "danger_sign" || reply?.escalation_label === "worse";

  return (
    <div className="min-h-screen bg-canvas">
      <header className="bg-emerald">
        <div className="mx-auto flex h-16 max-w-md items-center justify-between px-4">
          <Wordmark tone="light" />
          <span className="text-sm text-on-dark-2">Synthetic demo</span>
        </div>
      </header>
      <main id="content" className="mx-auto max-w-md space-y-5 px-4 py-8 text-ink">
        <h1 className="text-[1.75rem]">Your card</h1>
        {!token ? (
          <div className="space-y-6">
            <p className="text-lg leading-relaxed text-ink-2">
              Type the ID printed on your card, then ask for a code to see your next step.
            </p>
            <div className="space-y-3">
              <label htmlFor="card-id" className="block text-lg font-medium">
                <span className="mr-2 inline-flex size-7 items-center justify-center rounded-full bg-deep text-sm text-white">1</span>
                ID on your card
              </label>
              <input
                id="card-id"
                value={publicId}
                onChange={(event) => setPublicId(event.target.value)}
                autoComplete="off"
                autoCapitalize="characters"
                className={cx(controlClass({ size: "lg" }), "tracking-wider")}
              />
              <button className={button} type="button" onClick={start} disabled={!publicId.trim()}>
                Send a code
              </button>
              {hint ? (
                <p role="status" className="rounded-2xl bg-mint px-4 py-3 text-[0.9375rem] text-teal-text">
                  {hint}
                </p>
              ) : null}
            </div>
            <div className="space-y-3">
              <label htmlFor="card-code" className="block text-lg font-medium">
                <span className="mr-2 inline-flex size-7 items-center justify-center rounded-full bg-deep text-sm text-white">2</span>
                Code
              </label>
              <input
                id="card-code"
                value={code}
                onChange={(event) => setCode(event.target.value)}
                inputMode="numeric"
                autoComplete="one-time-code"
                className={cx(controlClass({ size: "lg" }), "tracking-widest")}
              />
              <button className={button} type="button" onClick={check} disabled={!publicId.trim() || !code.trim()}>
                Continue
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            <Guide text={reply?.spoken_text || reply?.reply_text || "Your next step is to go to the clinic."} danger={Boolean(danger)} />
            <p className="text-lg font-medium">Have you been able to get to care?</p>
            <div className="grid grid-cols-1 gap-2">
              {(reply?.quick_replies ?? []).map((item) => (
                <button key={item.id} className={choice} type="button" onClick={() => say(token, item.id)}>
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        )}
        {error ? (
          <p role="alert" className="flex gap-3 rounded-2xl border border-danger/30 bg-danger-bg px-4 py-3 text-lg text-danger">
            <CircleExclamationPoint aria-hidden="true" className="mt-1 size-5 shrink-0" />
            {error}
          </p>
        ) : null}
        <p className="pt-4 text-center text-[0.9375rem]">
          <Link href="/login" className="font-medium text-teal-text underline-offset-2 hover:underline">
            Back to the demo sign-in
          </Link>
        </p>
      </main>
    </div>
  );
}
