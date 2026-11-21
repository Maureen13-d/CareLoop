"use client";

import { ArrowLeft, FlaskConical } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Wordmark } from "@/components/ui/brand";
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
  context.fillStyle = "#e7f5f1";
  context.fillRect(0, 0, width, height);
  context.fillStyle = BANNER_COLOR;
  context.fillRect(0, 0, width, 48);
  context.fillStyle = "#ffffff";
  context.font = "14px sans-serif";
  context.fillText(RESEARCH_LABEL, 12, 30);
  if (!frame) return;
  const lines = kind === "stick" ? stickSegments(frame) : avatarSegments(frame);
  context.strokeStyle = "#183b38";
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
    context.fillStyle = "#183b38";
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
    <div className="min-h-dvh bg-canvas text-ink">
      <header className="bg-emerald">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-3 px-4">
          <Wordmark tone="light" />
          <Link
            href="/ksl"
            className="inline-flex min-h-10 items-center gap-2 rounded-full border border-white/30 px-4 text-sm font-medium text-white hover:bg-white/10"
          >
            <ArrowLeft aria-hidden="true" className="size-4" />
            Sign language clips
          </Link>
        </div>
      </header>
      <main id="content" className="mx-auto max-w-5xl space-y-6 px-4 py-8">
        <div>
          <p className="inline-flex items-center gap-2 rounded-full bg-warn-bg px-3 py-1 text-[0.8125rem] font-medium text-warn">
            <FlaskConical aria-hidden="true" className="size-4" />
            Kenyan Sign Language research sample. Not American Sign Language.
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">One dataset word</h1>
          <p className="mt-2 max-w-2xl text-ink-2">
            {clip
              ? `${clip.word_label} from ${clip.source_id}. The archive has no frame rate, so this plays at ${clip.playback_fps} frames per second for display.`
              : "A single gloss from the public pose archive. It is not a sentence and it is not a patient message. Development servers only."}
          </p>
        </div>
        {problem ? (
          <p role="status" className="rounded-xl border border-line bg-surface px-4 py-3 text-[0.9375rem] text-ink-2">
            {problem} The archive loads only after someone has verified its licence and fetched it locally.
          </p>
        ) : null}
        <div className="grid gap-4 md:grid-cols-2">
          <figure className="overflow-hidden rounded-2xl border border-line bg-surface shadow-raised">
            <canvas ref={stick} width={640} height={360} className="block w-full" aria-label="Landmark stickman signing the research word" role="img" />
            <figcaption className="border-t border-line px-4 py-2.5 text-sm font-medium">Landmark stickman</figcaption>
          </figure>
          <figure className="overflow-hidden rounded-2xl border border-line bg-surface shadow-raised">
            <canvas ref={avatar} width={640} height={360} className="block w-full" aria-label="Fixed-bone avatar signing the research word" role="img" />
            <figcaption className="border-t border-line px-4 py-2.5 text-sm font-medium">Fixed-bone avatar</figcaption>
          </figure>
        </div>
        <ResearchAttribution />
      </main>
    </div>
  );
}
