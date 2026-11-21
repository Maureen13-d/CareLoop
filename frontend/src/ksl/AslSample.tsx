"use client";

import { useEffect, useRef, useState } from "react";
import { frameLines } from "./aslPose.js";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SHOWCASE = [
  "--8pSDeC-fg_0-5",
  "1xKU91ggLeI_2-5",
  "--8pSDeC-fg_7-5",
  "--8pSDeC-fg_1-5",
  "g1HXoDkax5A_20-3",
  "-0N0jbyBW6g_11-5",
  "-F6vN4bOBWs_16-8",
];

export const SIGN_COUNT = SHOWCASE.length;

type Frame = {
  proj: number[][];
  left_hand: boolean;
  right_hand: boolean;
};

type Clip = {
  id: string;
  sentence: string;
  fps: number;
  frames: Frame[];
};

function paint(canvas: HTMLCanvasElement | null, clip: Clip | null, index: number) {
  if (!canvas) return;
  const context = canvas.getContext("2d");
  if (!context) return;
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#f7f1e6";
  context.fillRect(0, 0, width, height);
  const frame = clip?.frames[index];
  if (!frame) return;
  const points = frame.proj;
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const point of points) {
    minX = Math.min(minX, point[0]);
    minY = Math.min(minY, point[1]);
    maxX = Math.max(maxX, point[0]);
    maxY = Math.max(maxY, point[1]);
  }
  const caption = Math.round(height * 0.08);
  const scale = Math.min(
    (width * 0.78) / Math.max(maxX - minX, 1),
    ((height - caption) * 0.86) / Math.max(maxY - minY, 1),
  );
  const originX = width / 2 - ((minX + maxX) / 2) * scale;
  const originY = (height - caption) / 2 - ((minY + maxY) / 2) * scale;
  context.strokeStyle = "#102027";
  context.lineWidth = Math.max(4, width / 140);
  context.lineCap = "round";
  context.beginPath();
  for (const [x1, y1, x2, y2] of frameLines(points, !frame.left_hand, !frame.right_hand)) {
    context.moveTo(originX + x1 * scale, originY + y1 * scale);
    context.lineTo(originX + x2 * scale, originY + y2 * scale);
  }
  context.stroke();
  context.fillStyle = "#102027";
  context.font = `${Math.max(32, Math.round(width / 18))}px sans-serif`;
  context.textAlign = "center";
  context.fillText(clip?.sentence ?? "", width / 2, height - caption / 3);
}

export function AslSample({ step }: { step: number }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [problem, setProblem] = useState("");
  const clip = clips[Math.min(step, Math.max(clips.length - 1, 0))] ?? null;

  useEffect(() => {
    let cancelled = false;
    Promise.all(
      SHOWCASE.map(async (id) => {
        const response = await fetch(`${API}/api/v1/dev/asl-research/clips/${id}`);
        if (!response.ok) throw new Error("That ASL sentence is not available.");
        return response.json() as Promise<Clip>;
      }),
    )
      .then((body) => {
        if (!cancelled) setClips(body);
      })
      .catch((error: unknown) => {
        if (!cancelled) setProblem(error instanceof Error ? error.message : "The ASL sentence could not load.");
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
    const rate = clip?.fps || 24;
    const draw = (now: number) => {
      const node = canvas.current;
      if (node) {
        const rect = node.getBoundingClientRect();
        const ratio = window.devicePixelRatio || 1;
        const width = Math.max(1, Math.round(rect.width * ratio));
        const height = Math.max(1, Math.round(rect.height * ratio));
        if (node.width !== width || node.height !== height) {
          node.width = width;
          node.height = height;
        }
      }
      if (!last || now - last >= 1000 / rate) {
        last = now;
        paint(canvas.current, clip, frames.length ? index % frames.length : 0);
        if (frames.length) index = (index + 1) % frames.length;
      }
      handle = requestAnimationFrame(draw);
    };
    handle = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(handle);
  }, [clip]);

  return (
    <section className="relative min-h-0 flex-1">
      <canvas ref={canvas} className="block h-full w-full" />
      {problem ? <p className="absolute inset-x-4 bottom-4 text-center text-sm">{problem}</p> : null}
    </section>
  );
}
