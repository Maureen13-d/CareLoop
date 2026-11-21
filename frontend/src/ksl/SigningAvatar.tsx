"use client";

import { useEffect, useMemo, useState } from "react";
import { PRESETS, createPlayer, testWave } from "./engine.js";

type Pose = ReturnType<ReturnType<typeof createPlayer>["pose"]>;

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function SigningAvatar({
  caption,
  danger,
  available = false,
}: {
  caption: string;
  danger: boolean;
  available?: boolean;
}) {
  const [preset, setPreset] = useState(PRESETS[0].id);
  const [playing, setPlaying] = useState(false);
  const [pose, setPose] = useState<Pose | null>(null);
  const player = useMemo(() => {
    const clip = available ? { frames: [], fps: 30, caption, label: "" } : { ...testWave(), caption };
    const next = createPlayer(clip, { reduceMotion: false });
    next.listen();
    return next;
  }, [caption, available]);
  const shown = pose?.caption === caption ? pose : player.pose();

  useEffect(() => {
    if (!playing || prefersReducedMotion()) return undefined;
    let last = performance.now();
    let frame = 0;
    const loop = (now: number) => {
      const next = player.tick(now - last);
      last = now;
      setPose(next);
      if (next.phase === "holding") {
        setPlaying(false);
        return;
      }
      frame = requestAnimationFrame(loop);
    };
    frame = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frame);
  }, [playing, player]);

  if (danger) {
    return (
      <section className="rounded-2xl border border-line bg-white p-4">
        <p className="text-sm">I am a guide, not a doctor. I help you get to care.</p>
        <p className="mt-3 text-2xl">{caption}</p>
      </section>
    );
  }

  const colours = PRESETS.find((item) => item.id === preset) ?? PRESETS[0];
  const wave = shown.body?.upper_arm_r?.[2] ?? 0;

  return (
    <section className="rounded-2xl border border-line bg-white p-4">
      <p className="text-sm font-semibold">{available ? "Approved clip" : shown.honesty || "Captions"}</p>
      {!available ? (
        <div className="mt-3 flex items-end gap-3" aria-hidden="true">
          <div className="h-16 w-10 rounded-full" style={{ background: colours.skin }} />
          <div
            className="h-3 w-16 rounded-full"
            style={{ background: colours.cloth, transform: `rotate(${wave * 40}deg)` }}
          />
        </div>
      ) : null}
      <p className="mt-3 text-sm">I am a guide, not a doctor. I help you get to care.</p>
      <p className="mt-3 text-xl">{shown.caption || caption}</p>
      <p className="mt-2 text-sm">Icons: clinic, person. Recognition not enabled in this build.</p>
      {!available ? (
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            className="min-h-12 underline"
            type="button"
            onClick={() => {
              if (prefersReducedMotion()) {
                setPlaying(false);
                setPose(player.step());
                return;
              }
              setPose(player.play());
              setPlaying(true);
            }}
          >
            Play test motion
          </button>
          <button
            className="min-h-12 underline"
            type="button"
            onClick={() => {
              setPlaying(false);
              setPose(player.pause());
            }}
          >
            Pause
          </button>
          <button
            className="min-h-12 underline"
            type="button"
            onClick={() => {
              setPose(player.replay());
              setPlaying(!prefersReducedMotion());
            }}
          >
            Replay
          </button>
          <button className="min-h-12 underline" type="button" onClick={() => setPose(player.step())}>
            Step
          </button>
          <button
            className="min-h-12 underline"
            type="button"
            onClick={() => setPose(player.setSpeed(shown.speed === 1 ? 0.75 : 1))}
          >
            Speed {shown.speed}
          </button>
        </div>
      ) : null}
      <label className="mt-3 block text-sm">
        Appearance
        <select
          className="mt-1 min-h-12 w-full rounded-2xl border border-line px-3"
          value={preset}
          onChange={(event) => setPreset(event.target.value)}
        >
          {PRESETS.map((item) => (
            <option key={item.id} value={item.id}>
              {item.id}
            </option>
          ))}
        </select>
      </label>
    </section>
  );
}
