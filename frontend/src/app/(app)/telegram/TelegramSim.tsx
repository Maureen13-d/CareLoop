"use client";

import { SendHorizontal } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Badge, BrandMark, controlClass, cx } from "@/components/ui";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Button = { id?: string; label?: string };
type Turn = { who: "you" | "guide"; text: string };

export function TelegramSim() {
  const [text, setText] = useState("");
  const [buttons, setButtons] = useState<Button[]>([]);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLLIElement>(null);

  useEffect(() => {
    if (turns.length) endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [turns.length]);

  async function send(value: string, callback?: string) {
    const mine = value.trim();
    if (!mine && !callback) return;
    setTurns((current) => [...current, { who: "you", text: mine || callback || "" }]);
    setText("");
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/v1/followup/telegram/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: "demo-chat",
          text: callback ? "" : mine,
          callback,
          update_id: `${Date.now()}`,
        }),
      });
      const body = (await res.json()) as { reply_text?: string; buttons?: Button[] };
      setButtons(body.buttons ?? []);
      setTurns((current) => [...current, { who: "guide", text: body.reply_text ?? "" }]);
    } catch {
      setTurns((current) => [...current, { who: "guide", text: `Could not reach the API at ${API}.` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      aria-label="Telegram chat simulator"
      className="mx-auto flex w-full max-w-xl flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-raised"
    >
      <header className="flex items-center gap-3 border-b border-line bg-emerald px-5 py-3.5 text-white">
        <span aria-hidden="true" className="flex size-9 items-center justify-center rounded-full bg-white/12">
          <BrandMark className="size-5 text-white" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-semibold">CareLoop guide</p>
          <p className="text-[0.8125rem] text-on-dark-2">Simulated chat, not a real Telegram account</p>
        </div>
      </header>
      <ol aria-live="polite" className="min-h-80 flex-1 space-y-3 bg-canvas/70 px-4 py-5">
        {turns.length === 0 ? (
          <li className="py-10 text-center text-sm text-ink-2">
            Say hello, or try “not yet”, “transport” or “I feel worse” to see the follow-up guide reply.
          </li>
        ) : null}
        {turns.map((turn, index) => (
          <li key={`${turn.who}-${index}`} className={cx("flex", turn.who === "you" ? "justify-end" : "justify-start")}>
            <p
              className={cx(
                "max-w-[85%] rounded-2xl px-4 py-2.5 text-[0.9375rem] leading-relaxed",
                turn.who === "you" ? "rounded-tr-md bg-deep text-white" : "rounded-tl-md border border-line bg-surface text-ink",
              )}
            >
              <span className="sr-only">{turn.who === "you" ? "You: " : "Guide: "}</span>
              {turn.text}
            </p>
          </li>
        ))}
        {busy ? (
          <li className="text-[0.8125rem] text-ink-2">
            <Badge tone="outline">Guide is replying…</Badge>
          </li>
        ) : null}
        <li ref={endRef} aria-hidden="true" />
      </ol>
      {buttons.length ? (
        <div className="flex flex-wrap gap-2 border-t border-line px-4 py-3">
          {buttons.map((button) => (
            <button
              key={`${button.id}-${button.label}`}
              className="min-h-11 rounded-full border border-line bg-surface px-4 text-sm font-medium text-ink hover:border-teal hover:bg-mint"
              type="button"
              onClick={() => void send(button.label ?? "", button.id)}
            >
              {button.label}
            </button>
          ))}
        </div>
      ) : null}
      <form
        className="flex gap-2 border-t border-line px-4 py-3"
        onSubmit={(event) => {
          event.preventDefault();
          void send(text);
        }}
      >
        <label htmlFor="telegram-text" className="sr-only">
          Message
        </label>
        <input
          id="telegram-text"
          value={text}
          onChange={(event) => setText(event.target.value)}
          className={cx(controlClass({ shape: "pill" }), "min-w-0 flex-1")}
          placeholder="Message"
          autoComplete="off"
        />
        <button
          type="submit"
          aria-label="Send"
          disabled={busy || !text.trim()}
          className="flex size-11 shrink-0 items-center justify-center rounded-full bg-deep text-white hover:bg-emerald disabled:opacity-55"
        >
          <SendHorizontal aria-hidden="true" className="size-5" />
        </button>
      </form>
    </section>
  );
}
