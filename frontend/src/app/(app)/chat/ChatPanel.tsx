"use client";

import { useState, useTransition } from "react";
import { askAssistant, type AssistantReply } from "./actions";

const FLAG_LABEL: Record<string, string> = {
  fear_of_diagnosis: "Fear of bad news",
  fear_of_procedure_pain: "Fear or pain",
  cost: "Cost",
  transport_access: "Getting there",
  stigma_privacy: "Privacy",
  misconception: "A myth",
  no_info_where_to_go: "Not sure where to go",
  emotional_distress: "Distress",
  lack_of_support: "No one to go with",
};

const STARTERS = [
  "What happens at the visit?",
  "What should I bring?",
  "Can I bring someone with me?",
  "I cannot afford the bus fare",
];

type Turn = {
  id: string;
  from: "person" | "careloop";
  text: string;
  reply?: AssistantReply;
};

let turn = 0;
const nextId = () => `t${turn++}`;

export function ChatPanel() {
  const [messages, setMessages] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, startTransition] = useTransition();

  function pushPerson(text: string) {
    setMessages((current) => [...current, { id: nextId(), from: "person", text }]);
  }

  function send(text: string) {
    const clean = text.trim();
    if (!clean) return;
    pushPerson(clean);
    setDraft("");
    startTransition(async () => {
      const reply = await askAssistant({ text: clean });
      setMessages((current) => [
        ...current,
        { id: nextId(), from: "careloop", text: reply.reply_text, reply },
      ]);
    });
  }

  function confirm(flag: string) {
    startTransition(async () => {
      const reply = await askAssistant({ confirm_flag: flag });
      setMessages((current) => [
        ...current,
        { id: nextId(), from: "careloop", text: reply.reply_text, reply },
      ]);
    });
  }

  return (
    <div className="flex min-h-[32rem] flex-col rounded-[2rem] border border-line bg-paper-2">
      <div className="flex-1 space-y-4 px-5 py-6">
        <div className="max-w-lg">
          <p className="font-serif text-2xl leading-snug">
            Hello. This chat is private to this demo. I can explain a visit. I cannot tell you what a check means.
          </p>
          <p className="mt-2 text-sm text-ink-soft">
            If you feel unsafe, contact local emergency services. A placeholder helpline is not a real number.
          </p>
        </div>
        {messages.map((message) => (
          <div key={message.id} className={message.from === "person" ? "flex justify-end" : ""}>
            <div
              className={`max-w-lg rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                message.from === "person" ? "bg-lagoon text-white" : "bg-white"
              }`}
            >
              <p>{message.text}</p>
              {message.reply?.needs_human ? (
                <p className="mt-2 rounded-xl bg-[#f8efd4] px-3 py-2 text-ink">
                  A person will take this from here. Your words are not stored in the audit log.
                </p>
              ) : null}
              {message.reply?.barrier_flags
                .filter((flag) => flag.status === "suggested")
                .map((flag) => (
                  <div key={flag.flag} className="mt-3 rounded-xl border border-line px-3 py-2">
                    <p>This may be about {FLAG_LABEL[flag.flag] ?? flag.flag}. Share it with a navigator?</p>
                    <button
                      type="button"
                      onClick={() => confirm(flag.flag)}
                      className="mt-2 rounded-full bg-ink px-3 py-1 text-white"
                    >
                      Yes, tell a navigator
                    </button>
                  </div>
                ))}
              {message.reply?.sources?.length ? (
                <p className="mt-2 text-xs text-ink-soft">
                  Source: {message.reply.sources.join(" ")}
                  {message.reply.review_status.includes("draft") ? " · Draft, pending clinical review." : ""}
                </p>
              ) : null}
            </div>
          </div>
        ))}
        {pending ? <p className="text-sm text-ink-soft">Writing a reply…</p> : null}
      </div>
      <div className="border-t border-line px-4 py-4">
        <div className="mb-3 flex flex-wrap gap-2">
          {STARTERS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => send(prompt)}
              className="rounded-full border border-line bg-white px-3 py-1 text-left text-sm hover:border-lagoon"
            >
              {prompt}
            </button>
          ))}
        </div>
        <form
          className="flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            send(draft);
          }}
        >
          <label className="sr-only" htmlFor="chat-draft">
            Message
          </label>
          <input
            id="chat-draft"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="What is on your mind?"
            className="min-w-0 flex-1 rounded-full border border-line bg-white px-4 py-2 text-sm"
          />
          <button className="rounded-full bg-lagoon px-4 py-2 text-sm text-white hover:bg-lagoon-deep">
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
