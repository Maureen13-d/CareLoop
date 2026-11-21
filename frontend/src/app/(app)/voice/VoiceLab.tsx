"use client";

import { useRef, useState } from "react";
import { hearTurn, speakTurn, type VoiceCase, type VoiceTurn } from "./actions";

type Clip = { chunks: Float32Array[]; rate: number; stop: () => void };

function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const write = (offset: number, text: string) => {
    for (let index = 0; index < text.length; index += 1) {
      view.setUint8(offset + index, text.charCodeAt(index));
    }
  };
  write(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  write(8, "WAVE");
  write(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  write(36, "data");
  view.setUint32(40, samples.length * 2, true);
  let offset = 44;
  for (let index = 0; index < samples.length; index += 1) {
    const sample = Math.max(-1, Math.min(1, samples[index]));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    offset += 2;
  }
  return new Blob([buffer], { type: "audio/wav" });
}

export function VoiceLab({ cases }: { cases: VoiceCase[] }) {
  const [current, setCurrent] = useState<VoiceCase | null>(cases[0] ?? null);
  const [turn, setTurn] = useState<VoiceTurn | null>(null);
  const [text, setText] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  const clipRef = useRef<Clip | null>(null);

  async function apply(result: Awaited<ReturnType<typeof speakTurn>>) {
    if (!result.ok) {
      setNote(result.message);
      return;
    }
    setTurn(result.turn);
    setNote(result.turn.audio_error ?? "");
    setText("");
    window.setTimeout(() => {
      void audioRef.current?.play().catch(() => undefined);
    }, 0);
  }

  async function send(value: string) {
    if (!current) return;
    setBusy(true);
    try {
      await apply(await speakTurn(current.public_id, value));
    } finally {
      setBusy(false);
    }
  }

  async function startRecording() {
    if (!current || recording) return;
    setNote("");
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true }).catch(() => null);
    if (!stream) {
      setNote("The microphone is blocked. Type the words instead.");
      return;
    }
    const context = new AudioContext();
    const source = context.createMediaStreamSource(stream);
    const processor = context.createScriptProcessor(4096, 1, 1);
    const gain = context.createGain();
    gain.gain.value = 0;
    const chunks: Float32Array[] = [];
    processor.onaudioprocess = (event) => {
      chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
    };
    source.connect(processor);
    processor.connect(gain);
    gain.connect(context.destination);
    clipRef.current = {
      chunks,
      rate: context.sampleRate,
      stop: () => {
        processor.disconnect();
        source.disconnect();
        stream.getTracks().forEach((track) => track.stop());
        void context.close();
      },
    };
    setRecording(true);
  }

  async function stopRecording() {
    const clip = clipRef.current;
    clipRef.current = null;
    setRecording(false);
    if (!clip || !current) return;
    clip.stop();
    const length = clip.chunks.reduce((total, chunk) => total + chunk.length, 0);
    const samples = new Float32Array(length);
    let offset = 0;
    for (const chunk of clip.chunks) {
      samples.set(chunk, offset);
      offset += chunk.length;
    }
    if (!length) {
      setNote("No speech was heard. Say it again.");
      return;
    }
    const body = new FormData();
    body.set("public_id", current.public_id);
    body.set("file", encodeWav(samples, clip.rate), "turn.wav");
    setBusy(true);
    try {
      await apply(await hearTurn(body));
    } finally {
      setBusy(false);
    }
  }

  const audio =
    turn?.audio_base64 && current
      ? `data:${turn.audio_type || "audio/wav"};base64,${turn.audio_base64}`
      : "";

  return (
    <div className="grid items-start gap-8 lg:grid-cols-[18rem_1fr]">
      <ul className="space-y-2">
        {cases.length === 0 ? <li className="text-sm text-ink-soft">No voice test patients yet.</li> : null}
        {cases.map((item) => (
          <li key={item.public_id}>
            <button
              type="button"
              onClick={() => {
                setCurrent(item);
                setTurn(null);
                setNote("");
              }}
              className={`w-full rounded-2xl border px-3 py-3 text-left ${
                current?.public_id === item.public_id ? "border-lagoon bg-white" : "border-line bg-paper-2"
              }`}
            >
              <span className="block text-sm font-medium">{item.symptom}</span>
              <span className="mt-1 block text-xs text-ink-soft">
                {item.language === "sw" ? "Kiswahili" : "English"} · {item.area_label} · {item.age_band}
              </span>
            </button>
          </li>
        ))}
      </ul>

      {current ? (
        <section className="space-y-4 rounded-[2rem] border border-line bg-paper-2 p-5" aria-live="polite">
          <p className="text-sm text-ink-soft">Test script. Say, or type: “{current.say}”.</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="min-h-12 rounded-full bg-lagoon px-4 text-white"
              disabled={busy || recording}
              onClick={() => void send("")}
            >
              Start the check-in
            </button>
            <button
              type="button"
              className="min-h-12 rounded-full border border-line bg-white px-4"
              disabled={busy || recording}
              onClick={() => void send(current.say)}
            >
              Use the test phrase
            </button>
            <button
              type="button"
              className="min-h-12 rounded-full border border-line bg-white px-4"
              disabled={busy}
              onClick={() => void (recording ? stopRecording() : startRecording())}
            >
              {recording ? "Stop and send" : "Speak"}
            </button>
          </div>
          {turn ? (
            <div className="space-y-2 rounded-2xl bg-white p-4">
              {turn.heard_text ? <p className="text-sm text-ink-soft">Heard: {turn.heard_text}</p> : null}
              <p className="text-lg">{turn.spoken_text}</p>
              {audio ? <audio ref={audioRef} src={audio} controls className="mt-2 w-full" /> : null}
            </div>
          ) : (
            <p className="text-sm text-ink-soft">The check-in starts when you press the button. Captions stay on.</p>
          )}
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              void send(text);
            }}
          >
            <label className="sr-only" htmlFor="voice-reply">
              What the person says
            </label>
            <input
              id="voice-reply"
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="Or type what they say"
              className="min-h-12 min-w-0 flex-1 rounded-full border border-line bg-white px-4"
            />
            <button className="min-h-12 rounded-full bg-ink px-4 text-white" type="submit" disabled={busy}>
              Send
            </button>
          </form>
          {note ? <p className="text-sm text-clay">{note}</p> : null}
          {busy ? <p className="text-sm text-ink-soft">Listening…</p> : null}
        </section>
      ) : null}
    </div>
  );
}
