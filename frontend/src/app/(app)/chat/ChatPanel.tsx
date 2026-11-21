"use client";

import { BookOpen, HeartHandshake, SendHorizontal, ShieldCheck } from "lucide-react";
import { useEffect, useRef, useState, useTransition } from "react";
import { Badge, BrandMark, controlClass, cx } from "@/components/ui";
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

function GuideAvatar() {
  return (
    <span aria-hidden="true" className="flex size-8 shrink-0 items-center justify-center rounded-full bg-mint text-emerald">
      <BrandMark className="size-5" />
    </span>
  );
}

function GuideTurn({ message, onConfirm, busy }: { message: Turn; onConfirm: (flag: string) => void; busy: boolean }) {
  const reply = message.reply;
  const suggested = reply?.barrier_flags.filter((flag) => flag.status === "suggested") ?? [];
  return (
    <div className="flex items-start gap-2.5">
      <GuideAvatar />
      <div className="min-w-0 max-w-[34rem] space-y-2">
        <p className="sr-only">CareLoop guide said:</p>
        <div className="rounded-2xl rounded-tl-md border border-line bg-surface px-4 py-3 text-[0.9375rem] leading-relaxed text-ink">
          <p>{message.text}</p>
          {reply?.sources?.length ? (
            <p className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-line pt-2.5 text-[0.8125rem] text-ink-2">
              <BookOpen aria-hidden="true" className="size-3.5 shrink-0 text-teal-text" />
              <span>Source: {reply.sources.join(" ")}</span>
              {reply.review_status.includes("draft") ? <Badge tone="warn">Draft, pending clinical review</Badge> : null}
            </p>
          ) : null}
        </div>

        {reply?.needs_human ? (
          <div role="status" className="flex gap-3 rounded-2xl border border-warn/25 bg-warn-bg px-4 py-3 text-sm text-warn">
            <HeartHandshake aria-hidden="true" className="mt-0.5 size-[1.125rem] shrink-0" />
            <div>
              <p className="font-semibold">A person will take this from here.</p>
              <p className="mt-0.5">The guide has stopped. Your words are not stored in the audit log.</p>
            </div>
          </div>
        ) : null}

        {suggested.map((flag) => (
          <div key={flag.flag} className="rounded-2xl border border-mint-strong bg-mint px-4 py-3 text-sm text-ink">
            <p>
              This may be about <span className="font-semibold">{FLAG_LABEL[flag.flag] ?? flag.flag}</span>. Share it with a
              navigator? Only what you confirm reaches them.
            </p>
            <button
              type="button"
              disabled={busy}
              onClick={() => onConfirm(flag.flag)}
              className="mt-2.5 inline-flex min-h-9 items-center rounded-full bg-deep px-4 text-sm font-medium text-white hover:bg-emerald disabled:opacity-55"
            >
              Yes, tell a navigator
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, startTransition] = useTransition();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messages.length) endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages.length, pending]);

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
      setMessages((current) => [...current, { id: nextId(), from: "careloop", text: reply.reply_text, reply }]);
    });
  }

  function confirm(flag: string) {
    startTransition(async () => {
      const reply = await askAssistant({ confirm_flag: flag });
      setMessages((current) => [...current, { id: nextId(), from: "careloop", text: reply.reply_text, reply }]);
    });
  }

  return (
    <section
      aria-label="Support chat"
      className="flex min-h-[36rem] flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-raised lg:h-[calc(100dvh-10rem)] lg:min-h-[34rem]"
    >
      <header className="flex items-center gap-3 border-b border-line px-5 py-4">
        <GuideAvatar />
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-ink">CareLoop guide</p>
          <p className="text-[0.8125rem] text-ink-2">Explains the visit. Never says what a check means.</p>
        </div>
        <Badge tone="outline" icon={<ShieldCheck aria-hidden="true" />}>
          Private demo
        </Badge>
      </header>

      <div className="flex-1 space-y-5 overflow-y-auto bg-canvas/70 px-4 py-5 sm:px-5" aria-live="polite" aria-relevant="additions">
        <div className="flex items-start gap-2.5">
          <GuideAvatar />
          <div className="max-w-[34rem] space-y-2">
            <div className="rounded-2xl rounded-tl-md border border-line bg-surface px-4 py-3 text-[0.9375rem] leading-relaxed text-ink">
              Hello. This chat is private to this demo. I can explain a visit. I cannot tell you what a check means.
            </div>
            <p className="px-1 text-[0.8125rem] text-ink-2">
              If you feel unsafe, contact local emergency services. A placeholder helpline is not a real number.
            </p>
          </div>
        </div>

        {messages.map((message) =>
          message.from === "person" ? (
            <div key={message.id} className="flex justify-end">
              <p className="max-w-[30rem] rounded-2xl rounded-tr-md bg-deep px-4 py-3 text-[0.9375rem] leading-relaxed text-white">
                <span className="sr-only">You said: </span>
                {message.text}
              </p>
            </div>
          ) : (
            <GuideTurn key={message.id} message={message} onConfirm={confirm} busy={pending} />
          ),
        )}

        {pending ? (
          <div className="flex items-center gap-2.5">
            <GuideAvatar />
            <span className="inline-flex items-center gap-1 rounded-2xl border border-line bg-surface px-4 py-3.5">
              <span className="sr-only">Writing a reply</span>
              {[0, 1, 2].map((dot) => (
                <span
                  key={dot}
                  aria-hidden="true"
                  className="size-1.5 animate-bounce rounded-full bg-ink-3"
                  style={{ animationDelay: `${dot * 120}ms` }}
                />
              ))}
            </span>
          </div>
        ) : null}
        <div ref={endRef} />
      </div>

      <div className="border-t border-line bg-surface px-4 py-4 sm:px-5">
        <div className="mb-3 flex gap-2 overflow-x-auto pb-1 sm:flex-wrap sm:overflow-visible sm:pb-0">
          {STARTERS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={pending}
              onClick={() => send(prompt)}
              className="min-h-9 shrink-0 rounded-full border border-line bg-surface px-3.5 text-sm text-ink hover:border-teal hover:bg-mint disabled:opacity-55"
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
            autoComplete="off"
            className={cx(controlClass({ shape: "pill" }), "min-w-0 flex-1")}
          />
          <button
            type="submit"
            aria-label="Send"
            disabled={pending || !draft.trim()}
            className="flex size-11 shrink-0 items-center justify-center rounded-full bg-deep text-white hover:bg-emerald disabled:opacity-55"
          >
            <SendHorizontal aria-hidden="true" className="size-5" />
          </button>
        </form>
      </div>
    </section>
  );
}
