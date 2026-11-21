"use client";

import { useEffect, useRef, useState } from "react";
import { ResearchAttribution } from "@/ksl/ResearchAttribution";
import { RESEARCH_LABEL } from "@/ksl/researchLabel.js";
import {
  BANNER_COLOR,
  PLAYBACK_FPS,
  avatarSegments,
  project,
  stickSegments,
} from "@/ksl/researchPose.js";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Frame = {
  pose: number[][];
  left_hand: number[][];
  right_hand: number[][];
  arms: {
    left?: { upper?: number[]; lower?: number[] };
    right?: { upper?: number[]; lower?: number[] };
  };
  hands?: { left?: Record<string, number[]>; right?: Record<string, number[]> };
  face?: { jawOpen?: number; eyeBlinkLeft?: number; eyeBlinkRight?: number };
};

type Clip = {
  word_label: string;
  source_id: string;
  fps: null;
  playback_fps: number;
  quality: number;
  frames: Frame[];
  label: string;
};

function paint(
  canvas: HTMLCanvasElement | null,
  frame: Frame | undefined,
  kind: "stick" | "avatar",
) {
  if (!canvas) return;
  const context = canvas.getContext("2d");
  if (!context) return;
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#f7f1e6";
  context.fillRect(0, 0, width, height);
  context.fillStyle = BANNER_COLOR;
  context.fillRect(0, 0, width, 48);
  context.fillStyle = "#ffffff";
  context.font = "14px sans-serif";
  context.fillText(RESEARCH_LABEL, 12, 30);
  if (!frame) return;
  const lines = kind === "stick" ? stickSegments(frame) : avatarSegments(frame);
  context.strokeStyle = "#102027";
  context.lineWidth = 4;
  context.lineCap = "round";
  context.beginPath();
  for (const [x1, y1, x2, y2] of lines) {
    const [ax, ay] = project(x1, y1, width / 2, 210, 78);
    const [bx, by] = project(x2, y2, width / 2, 210, 78);
    context.moveTo(ax, ay);
    context.lineTo(bx, by);
  }
  context.stroke();
  if (kind === "avatar") {
    const jaw = frame.face?.jawOpen ?? 0;
    const blink = ((frame.face?.eyeBlinkLeft ?? 0) + (frame.face?.eyeBlinkRight ?? 0)) / 2;
    context.beginPath();
    context.arc(width / 2, 150, 22, 0, Math.PI * 2);
    context.stroke();
    context.fillStyle = "#102027";
    context.fillRect(width / 2 - 10, 146, 4, Math.max(2, 6 * (1 - blink)));
    context.fillRect(width / 2 + 6, 146, 4, Math.max(2, 6 * (1 - blink)));
    context.fillRect(width / 2 - 6, 158, 12, 2 + jaw * 8);
  }
}

export default function ResearchSamplePage() {
  const stick = useRef<HTMLCanvasElement>(null);
  const avatar = useRef<HTMLCanvasElement>(null);
  const [clip, setClip] = useState<Clip | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API}/api/v1/dev/ksl-research/words/PAIN`)
      .then(async (response) => {
        if (!response.ok) throw new Error("The research sample is not available on this machine.");
        return response.json() as Promise<Clip>;
      })
      .then((body) => {
        if (!cancelled) setClip(body);
      })
      .catch((error: unknown) => {
        if (!cancelled) setProblem(error instanceof Error ? error.message : "The sample could not load.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const frames = clip?.frames ?? [];
    let index = 0;
    let last = 0;
    let handle = 0;
    const rate = clip?.playback_fps || PLAYBACK_FPS;
    const draw = (now: number) => {
      if (!last || now - last >= 1000 / rate) {
        last = now;
        const frame = frames[index];
        paint(stick.current, frame, "stick");
        paint(avatar.current, frame, "avatar");
        if (frames.length) index = (index + 1) % frames.length;
      }
      handle = requestAnimationFrame(draw);
    };
    handle = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(handle);
  }, [clip]);

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <header>
        <p className="text-sm text-clay">Kenyan Sign Language research sample. Not American Sign Language.</p>
        <h1 className="mt-1 font-serif text-4xl">One dataset word</h1>
        <p className="mt-2 max-w-2xl text-ink-soft">
          {clip
            ? `${clip.word_label} from ${clip.source_id}. The archive has no frame rate, so this plays at ${clip.playback_fps} frames per second for display.`
            : "A single gloss from the public pose archive. It is not a sentence and it is not a patient message."}
        </p>
      </header>
      {problem ? <p className="text-lg">{problem}</p> : null}
      <div className="grid gap-4 md:grid-cols-2">
        <figure className="space-y-2">
          <figcaption className="text-sm">Landmark stickman</figcaption>
          <canvas ref={stick} width={640} height={360} className="w-full rounded-2xl border border-line" />
        </figure>
        <figure className="space-y-2">
          <figcaption className="text-sm">Fixed-bone avatar</figcaption>
          <canvas ref={avatar} width={640} height={360} className="w-full rounded-2xl border border-line" />
        </figure>
      </div>
      <ResearchAttribution />
    </main>
  );
}
