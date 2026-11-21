"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Button = { id?: string; label?: string };
type Turn = { who: "you" | "guide"; text: string };

export function TelegramSim() {
  const [text, setText] = useState("");
  const [buttons, setButtons] = useState<Button[]>([]);
  const [turns, setTurns] = useState<Turn[]>([]);

  async function send(value: string, callback?: string) {
    const mine = value.trim();
    if (!mine && !callback) return;
    setTurns((current) => [...current, { who: "you", text: mine || callback || "" }]);
    setText("");
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
  }

  return (
    <div className="mx-auto max-w-md space-y-3">
      <p className="text-sm text-lagoon">Same menus as the bot. This page does not send to Telegram.</p>
      <ul className="min-h-64 space-y-2 rounded-2xl border border-line bg-white p-3">
        {turns.map((turn, index) => (
          <li key={`${turn.who}-${index}`} className={turn.who === "you" ? "text-right" : ""}>
            <span className="inline-block whitespace-pre-wrap rounded-2xl bg-paper-2 px-3 py-2">
              {turn.text}
            </span>
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-2">
        {buttons.map((button) => (
          <button
            key={`${button.id}-${button.label}`}
            className="min-h-12 rounded-full border border-line px-3"
            type="button"
            onClick={() => void send(button.label ?? "", button.id)}
          >
            {button.label}
          </button>
        ))}
      </div>
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void send(text);
        }}
      >
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          className="min-h-12 flex-1 rounded-full border border-line px-3"
          placeholder="Message"
        />
        <button className="min-h-12 rounded-full bg-lagoon px-4 text-white" type="submit">
          Send
        </button>
      </form>
    </div>
  );
}
