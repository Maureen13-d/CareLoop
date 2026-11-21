"use client";

import { PhoneCall, PhoneOff, SendHorizontal, TriangleExclamationPoint } from "lucide-react";
import { useEffect, useRef, useState, useTransition } from "react";
import { Badge, controlClass, cx } from "@/components/ui";
import { dial, markUndelivered, placeCall, sendSms, type CallTurn } from "./actions";
import type { Sms } from "./types";

const KEYS: [string, string][] = [
  ["1", ""],
  ["2", "ABC"],
  ["3", "DEF"],
  ["4", "GHI"],
  ["5", "JKL"],
  ["6", "MNO"],
  ["7", "PQRS"],
  ["8", "TUV"],
  ["9", "WXYZ"],
  ["*", ""],
  ["0", "+"],
  ["#", ""],
];

function SignalBars() {
  return (
    <span aria-hidden="true" className="inline-flex items-end gap-[2px]">
      {[4, 6, 8, 10].map((height) => (
        <span key={height} className="w-[3px] rounded-sm bg-lcd-ink/80" style={{ height }} />
      ))}
    </span>
  );
}

export function PhoneLab({ sessionId, initialMessages }: { sessionId: string; initialMessages: Sms[] }) {
  const [screen, setScreen] = useState("Press the green button.\nShort code *XYZ# is a placeholder.");
  const [messages, setMessages] = useState(initialMessages);
  const [ussdDraft, setUssdDraft] = useState("");
  const [smsDraft, setSmsDraft] = useState("");
  const [dialing, startDial] = useTransition();
  const [pending, startTransition] = useTransition();
  const [inCall, setInCall] = useState(false);
  const [call, setCall] = useState<CallTurn | null>(null);
  const [callError, setCallError] = useState("");
  const [sayDraft, setSayDraft] = useState("");
  const [calling, startCall] = useTransition();
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const node = audioRef.current;
    if (!inCall || !node || !call?.audio_base64) return;
    node.src = `data:${call.audio_type || "audio/wav"};base64,${call.audio_base64}`;
    void node.play().catch(() => undefined);
  }, [call, inCall]);

  function speak(text: string) {
    setInCall(true);
    setSayDraft("");
    startCall(async () => {
      const result = await placeCall(sessionId, text);
      if (!result.ok) {
        setCallError(result.message);
        return;
      }
      setCallError("");
      setCall(result.turn);
    });
  }

  function hangUp() {
    audioRef.current?.pause();
    setInCall(false);
  }

  function press(text: string) {
    startDial(async () => {
      setScreen(await dial(sessionId, text));
    });
  }

  function reply(text: string) {
    const clean = text.trim();
    if (!clean) return;
    setSmsDraft("");
    startTransition(async () => {
      setMessages(await sendSms(clean));
    });
  }

  const latestOut = [...messages].reverse().find((message) => message.direction === "out");

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]">
      {/* the handset */}
      <div className="rounded-[1.75rem] bg-mint px-4 py-8 sm:px-8">
        <div
          role="group"
          aria-label="Simulated feature phone"
          className="mx-auto w-full max-w-[18.5rem] rounded-[2.6rem] bg-gradient-to-b from-[#16312c] to-[#0b1c19] p-4 pb-5 text-white shadow-float ring-1 ring-black/40"
        >
          <span aria-hidden="true" className="mx-auto mb-3 block h-1.5 w-14 rounded-full bg-white/15" />
          <div className="lcd rounded-2xl p-3 shadow-[inset_0_2px_8px_rgb(0_0_0/0.5)]">
            <div className="mb-2 flex items-center justify-between font-sans text-[10px] tracking-wide text-lcd-ink/75">
              <SignalBars />
              <span>{inCall ? "Simulated call" : "CareLoop *XYZ#"}</span>
              <span aria-hidden="true" className="inline-block h-2.5 w-5 rounded-[2px] border border-lcd-ink/70 p-[1px]">
                <span className="block h-full w-3/4 bg-lcd-ink/80" />
              </span>
            </div>
            <div aria-live="polite" className="min-h-48 whitespace-pre-wrap text-[13px] leading-relaxed">
              {inCall
                ? calling
                  ? "Connecting…"
                  : callError || call?.spoken_text || "Say hello, or say the ID on your card."
                : dialing
                  ? "Please wait…"
                  : screen}
            </div>
          </div>

          {inCall ? (
            <div className="mt-4">
              <p className="text-[10px] tracking-wide text-white/55">Simulated phrases</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {(call?.phrases ?? []).map((phrase) => (
                  <button
                    key={phrase.id}
                    type="button"
                    disabled={calling}
                    onClick={() => speak(phrase.id)}
                    className="rounded-full bg-white/10 px-3 py-1.5 text-left text-xs leading-snug hover:bg-white/20 disabled:opacity-60"
                  >
                    {phrase.label}
                  </button>
                ))}
              </div>
              <form
                className="mt-3 flex gap-2"
                onSubmit={(event) => {
                  event.preventDefault();
                  speak(sayDraft);
                }}
              >
                <label className="sr-only" htmlFor="say-text">
                  Say a phrase
                </label>
                <input
                  id="say-text"
                  value={sayDraft}
                  onChange={(event) => setSayDraft(event.target.value)}
                  placeholder="Or say a phrase"
                  autoComplete="off"
                  className="min-h-10 min-w-0 flex-1 rounded-full bg-white/10 px-4 text-sm text-white placeholder:text-white/45 focus-visible:outline-on-dark"
                />
                <button
                  type="submit"
                  disabled={calling}
                  className="min-h-10 rounded-full bg-on-dark px-4 text-sm font-medium text-emerald hover:bg-white disabled:opacity-60"
                >
                  Say
                </button>
              </form>
              <div className="mt-3 flex gap-2">
                <button
                  type="button"
                  disabled={!call?.audio_base64}
                  onClick={() => void audioRef.current?.play().catch(() => undefined)}
                  className="flex h-12 flex-1 items-center justify-center rounded-full bg-white/10 text-sm font-medium hover:bg-white/20 disabled:opacity-50"
                >
                  Hear it
                </button>
                <button
                  type="button"
                  onClick={hangUp}
                  className="flex h-12 flex-1 items-center justify-center gap-2 rounded-full bg-[#9b3a3a] text-sm font-medium hover:bg-[#8a3333]"
                >
                  <PhoneOff aria-hidden="true" className="size-4" />
                  Hang up
                </button>
              </div>
              {call?.audio_error ? (
                <p className="mt-2 text-center text-[11px] text-white/60">
                  {call.audio_error} The words stay on the screen.
                </p>
              ) : null}
              <audio ref={audioRef} className="sr-only" />
            </div>
          ) : (
            <>
              <div className="mt-4 grid grid-cols-3 gap-2">
                {KEYS.map(([key, letters]) => (
                  <button
                    key={key}
                    type="button"
                    disabled={dialing}
                    aria-label={key === "*" || key === "#" ? `${key}, back to the menu` : `Key ${key}`}
                    onClick={() => press(key === "*" || key === "#" ? "" : key)}
                    className="flex h-12 flex-col items-center justify-center rounded-2xl bg-white/[0.08] leading-none transition-colors hover:bg-white/15 active:bg-white/25 disabled:opacity-60"
                  >
                    <span className="text-lg font-medium">{key}</span>
                    {letters ? <span className="mt-0.5 text-[9px] tracking-widest text-white/45">{letters}</span> : null}
                  </button>
                ))}
              </div>

              <div className="mt-3 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  disabled={dialing}
                  onClick={() => press("")}
                  className="flex h-12 items-center justify-center gap-2 rounded-full bg-[#2f8a4c] text-sm font-medium transition-colors hover:bg-[#2a7a44] disabled:opacity-60"
                >
                  <PhoneCall aria-hidden="true" className="size-4" />
                  Dial *XYZ#
                </button>
                <button
                  type="button"
                  onClick={() => speak("")}
                  className="flex h-12 items-center justify-center gap-2 rounded-full bg-white text-sm font-medium text-emerald transition-colors hover:bg-mint"
                >
                  <PhoneCall aria-hidden="true" className="size-4" />
                  Call
                </button>
              </div>

              <form
                className="mt-3 flex gap-2"
                onSubmit={(event) => {
                  event.preventDefault();
                  press(ussdDraft);
                  setUssdDraft("");
                }}
              >
                <label className="sr-only" htmlFor="ussd-text">
                  Type a USSD reply
                </label>
                <input
                  id="ussd-text"
                  value={ussdDraft}
                  onChange={(event) => setUssdDraft(event.target.value)}
                  placeholder="Type a question"
                  autoComplete="off"
                  className="min-h-10 min-w-0 flex-1 rounded-full bg-white/10 px-4 text-sm text-white placeholder:text-white/45 focus-visible:outline-on-dark"
                />
                <button
                  type="submit"
                  className="min-h-10 rounded-full bg-on-dark px-4 text-sm font-medium text-emerald hover:bg-white"
                >
                  Send
                </button>
              </form>
            </>
          )}
        </div>
        <p className="mx-auto mt-4 max-w-[18.5rem] text-center text-[0.8125rem] text-teal-text">
          A feature phone. Dial opens the menu. Call is a simulated voice check: the words stay on the screen.
        </p>
      </div>

      {/* the text inbox */}
      <section
        aria-labelledby="sms-heading"
        className="flex flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-raised"
      >
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-4">
          <div>
            <h2 id="sms-heading" className="text-lg">
              Text inbox
            </h2>
            <p className="text-[0.8125rem] text-ink-2">
              Handset {messages[0]?.phone_ref ?? "+254700000101"}. Nothing is actually sent.
            </p>
          </div>
          <Badge tone="outline">Simulated SMS</Badge>
        </header>

        <ol className="min-h-64 flex-1 space-y-3 bg-canvas/70 px-5 py-5" aria-live="polite">
          {messages.length === 0 ? <li className="text-sm text-ink-2">No messages yet.</li> : null}
          {messages.map((message) => {
            const out = message.direction === "out";
            return (
              <li key={message.id} className={cx("flex", out ? "justify-start" : "justify-end")}>
                <div
                  className={cx(
                    "max-w-sm rounded-2xl px-4 py-2.5 text-[0.9375rem] leading-relaxed",
                    out ? "rounded-tl-md border border-line bg-surface text-ink" : "rounded-tr-md bg-deep text-white",
                  )}
                >
                  <p>{message.body}</p>
                  <p className={cx("mt-1 text-[0.75rem]", out ? "text-ink-2" : "text-on-dark-2")}>
                    {out ? "From CareLoop" : "You"}, {message.status.replaceAll("_", " ")}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>

        <div className="space-y-3 border-t border-line px-5 py-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-ink-2">Quick replies</span>
            {[
              ["1", "Confirm"],
              ["2", "Change"],
              ["3", "Help"],
              ["STOP", "Stop messages"],
            ].map(([code, meaning]) => (
              <button
                key={code}
                type="button"
                disabled={pending}
                onClick={() => reply(code)}
                className="inline-flex min-h-9 items-center gap-1.5 rounded-full border border-line bg-surface px-3.5 text-sm text-ink hover:border-teal hover:bg-mint disabled:opacity-55"
              >
                <span className="font-semibold">{code}</span>
                <span className="text-ink-2">{meaning}</span>
              </button>
            ))}
          </div>
          {latestOut && latestOut.status !== "undelivered" ? (
            <button
              type="button"
              disabled={pending}
              onClick={() => startTransition(async () => setMessages(await markUndelivered(latestOut.id)))}
              className="inline-flex min-h-9 items-center gap-1.5 rounded-full px-1 text-sm font-medium text-warn hover:underline disabled:opacity-55"
            >
              <TriangleExclamationPoint aria-hidden="true" className="size-4" />
              Simulate: this text did not arrive
            </button>
          ) : null}
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              reply(smsDraft);
            }}
          >
            <label className="sr-only" htmlFor="sms-draft">
              Text message
            </label>
            <input
              id="sms-draft"
              value={smsDraft}
              onChange={(event) => setSmsDraft(event.target.value)}
              placeholder="Or type a message"
              autoComplete="off"
              className={cx(controlClass({ shape: "pill" }), "min-w-0 flex-1")}
            />
            <button
              type="submit"
              aria-label="Send text"
              disabled={pending}
              className="flex size-11 shrink-0 items-center justify-center rounded-full bg-deep text-white hover:bg-emerald disabled:opacity-55"
            >
              <SendHorizontal aria-hidden="true" className="size-5" />
            </button>
          </form>
          {pending ? <p className="text-[0.8125rem] text-ink-2">Sending…</p> : null}
        </div>
      </section>
    </div>
  );
}
