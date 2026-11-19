"use client";

import { useState, useTransition } from "react";
import { dial, markUndelivered, sendSms } from "./actions";
import type { Sms } from "./types";

const KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"];

export function PhoneLab({ sessionId, initialMessages }: { sessionId: string; initialMessages: Sms[] }) {
  const [screen, setScreen] = useState("Press the green button.\nShort code *XYZ# is a placeholder.");
  const [messages, setMessages] = useState(initialMessages);
  const [ussdDraft, setUssdDraft] = useState("");
  const [smsDraft, setSmsDraft] = useState("");
  const [pending, startTransition] = useTransition();

  function press(text: string) {
    startTransition(async () => {
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
    <div className="grid items-start gap-8 lg:grid-cols-2">
      <div>
        <div className="mx-auto w-[300px] rounded-[2.2rem] bg-ink p-3 text-white shadow-xl">
          <div className="mb-2 flex items-center justify-between px-2 text-[10px] uppercase tracking-widest text-white/60">
            <span>CareLoop</span>
            <span>*XYZ#</span>
          </div>
          <div className="lcd min-h-56 rounded-2xl p-3 text-[13px] leading-relaxed" aria-live="polite">
            {screen}
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2">
            {KEYS.map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => press(key === "*" || key === "#" ? "" : key)}
                className="rounded-full bg-white/10 py-3 text-lg hover:bg-white/20"
              >
                {key}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => press("")}
            className="mt-3 w-full rounded-full bg-moss py-3 text-sm font-medium"
          >
            Dial *XYZ#
          </button>
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
              className="min-w-0 flex-1 rounded-full bg-white/10 px-3 py-2 text-sm text-white placeholder:text-white/40"
            />
            <button className="rounded-full bg-white px-3 py-2 text-sm text-ink">Send</button>
          </form>
        </div>
        <p className="mx-auto mt-3 max-w-[300px] text-center text-xs text-ink-soft">
          A feature phone. No data, no app. The menu never names a finding.
        </p>
      </div>

      <section aria-labelledby="sms-heading" className="rounded-[2rem] border border-line bg-paper-2 p-5">
        <h2 id="sms-heading" className="text-2xl">
          Text inbox
        </h2>
        <p className="mt-1 text-sm text-ink-soft">Handset {messages[0]?.phone_ref ?? "+254700000101"}. Nothing is actually sent.</p>
        <ol className="mt-4 space-y-3" aria-live="polite">
          {messages.length === 0 ? <li className="text-sm text-ink-soft">No messages yet.</li> : null}
          {messages.map((message) => (
            <li
              key={message.id}
              className={`max-w-sm rounded-2xl px-3 py-2 text-sm ${
                message.direction === "out" ? "bg-white" : "ml-auto bg-lagoon text-white"
              }`}
            >
              <p>{message.body}</p>
              <p className={`mt-1 text-xs ${message.direction === "out" ? "text-ink-soft" : "text-white/70"}`}>
                {message.direction === "out" ? "CareLoop" : "You"} · {message.status.replaceAll("_", " ")}
              </p>
            </li>
          ))}
        </ol>
        <div className="mt-4 flex flex-wrap gap-2">
          {["1", "2", "3", "STOP"].map((code) => (
            <button
              key={code}
              type="button"
              onClick={() => reply(code)}
              className="rounded-full border border-line bg-white px-3 py-1.5 text-sm"
            >
              Reply {code}
            </button>
          ))}
          {latestOut && latestOut.status !== "undelivered" ? (
            <button
              type="button"
              onClick={() => startTransition(async () => setMessages(await markUndelivered(latestOut.id)))}
              className="rounded-full border border-clay/40 px-3 py-1.5 text-sm text-clay"
            >
              This text did not arrive
            </button>
          ) : null}
        </div>
        <form
          className="mt-3 flex gap-2"
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
            className="min-w-0 flex-1 rounded-full border border-line bg-white px-4 py-2 text-sm"
          />
          <button className="rounded-full bg-lagoon px-4 py-2 text-sm text-white">Send</button>
        </form>
        {pending ? <p className="mt-2 text-xs text-ink-soft">Sending…</p> : null}
      </section>
    </div>
  );
}
