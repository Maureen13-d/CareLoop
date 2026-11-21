"use client";

import { useEffect, useRef, useState } from "react";
import { SIGN_ORDER } from "./signReplies.js";

const SKIN = "#d7a27a";
const HAND = "#8a5a3c";
const HAIR = "#3a2a22";
const SHIRT = "#1a6b63";
const PANTS = "#2c3338";
const SHOE = "#1b2428";
const INK = "#102027";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const SIGN_COUNT = SIGN_ORDER.length;

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
  const at = (joint: number) => [
    originX + points[joint][0] * scale,
    originY + points[joint][1] * scale,
  ];
  const span = Math.hypot(at(16)[0] - at(17)[0], at(16)[1] - at(17)[1]);
  const thick = Math.max(8, span * 0.22);
  const footL = at(10);
  const footR = at(11);
  context.fillStyle = "rgba(16,32,39,0.08)";
  context.beginPath();
  context.ellipse(
    (footL[0] + footR[0]) / 2,
    Math.max(footL[1], footR[1]),
    span * 0.85,
    span * 0.14,
    0,
    0,
    Math.PI * 2,
  );
  context.fill();
  const limb = (a: number, b: number, color: string, weight: number) => {
    const start = at(a);
    const end = at(b);
    context.strokeStyle = color;
    context.lineWidth = weight;
    context.lineCap = "round";
    context.beginPath();
    context.moveTo(start[0], start[1]);
    context.lineTo(end[0], end[1]);
    context.stroke();
  };
  limb(1, 4, PANTS, thick);
  limb(4, 7, PANTS, thick * 0.85);
  limb(7, 10, SHOE, thick * 0.55);
  limb(2, 5, PANTS, thick);
  limb(5, 8, PANTS, thick * 0.85);
  limb(8, 11, SHOE, thick * 0.55);
  limb(16, 18, SHIRT, thick * 0.72);
  limb(17, 19, SHIRT, thick * 0.72);
  limb(18, 20, SKIN, thick * 0.48);
  limb(19, 21, SKIN, thick * 0.48);
  const widen = (joint: number, away: number, extra: number) => {
    const point = at(joint);
    const other = at(away);
    const dx = point[0] - other[0];
    const dy = point[1] - other[1];
    const length = Math.hypot(dx, dy) || 1;
    return [point[0] + (dx / length) * extra, point[1] + (dy / length) * extra];
  };
  const leftShoulder = widen(16, 17, span * 0.08);
  const rightShoulder = widen(17, 16, span * 0.08);
  const leftHip = widen(1, 2, span * 0.06);
  const rightHip = widen(2, 1, span * 0.06);
  context.fillStyle = SHIRT;
  context.beginPath();
  context.moveTo(leftShoulder[0], leftShoulder[1]);
  context.lineTo(rightShoulder[0], rightShoulder[1]);
  context.lineTo(rightHip[0], rightHip[1]);
  context.lineTo(leftHip[0], leftHip[1]);
  context.closePath();
  context.fill();
  limb(12, 15, SKIN, thick * 0.42);
  const neck = at(12);
  const crown = at(15);
  const eyeL = at(23);
  const eyeR = at(24);
  const headR = Math.max(span * 0.28, Math.hypot(crown[0] - neck[0], crown[1] - neck[1]) * 0.72);
  const headX = crown[0] * 0.4 + (eyeL[0] + eyeR[0]) * 0.3;
  const headY = crown[1] * 0.4 + (eyeL[1] + eyeR[1]) * 0.3;
  context.fillStyle = SKIN;
  context.beginPath();
  context.ellipse(headX, headY, headR * 0.86, headR, 0, 0, Math.PI * 2);
  context.fill();
  context.save();
  context.beginPath();
  context.ellipse(headX, headY, headR * 0.86, headR, 0, 0, Math.PI * 2);
  context.clip();
  context.fillStyle = HAIR;
  context.fillRect(headX - headR, headY - headR * 1.15, headR * 2, headR * 0.7);
  context.restore();
  context.fillStyle = INK;
  context.beginPath();
  context.arc(eyeL[0], eyeL[1], Math.max(2, headR * 0.07), 0, Math.PI * 2);
  context.arc(eyeR[0], eyeR[1], Math.max(2, headR * 0.07), 0, Math.PI * 2);
  context.fill();
  const jaw = at(22);
  context.strokeStyle = "#6b3a32";
  context.lineWidth = Math.max(2, headR * 0.06);
  context.beginPath();
  context.arc(headX, (eyeL[1] + eyeR[1] + jaw[1]) / 3, headR * 0.22, 0.15 * Math.PI, 0.85 * Math.PI);
  context.stroke();
  const hand = (wrist: number, start: number, show: boolean) => {
    if (!show) return;
    context.strokeStyle = HAND;
    context.lineWidth = thick * 0.2;
    context.lineCap = "round";
    context.beginPath();
    for (let finger = 0; finger < 5; finger += 1) {
      const joint = start + finger * 3;
      const chain = [wrist, joint, joint + 1, joint + 2];
      for (let link = 0; link < chain.length - 1; link += 1) {
        const from = at(chain[link]);
        const to = at(chain[link + 1]);
        context.moveTo(from[0], from[1]);
        context.lineTo(to[0], to[1]);
      }
    }
    context.stroke();
    const palm = at(wrist);
    context.fillStyle = SKIN;
    context.beginPath();
    context.arc(palm[0], palm[1], thick * 0.28, 0, Math.PI * 2);
    context.fill();
  };
  hand(20, 25, frame.left_hand);
  hand(21, 40, frame.right_hand);
  context.fillStyle = INK;
  context.font = `${Math.max(32, Math.round(width / 18))}px sans-serif`;
  context.textAlign = "center";
  context.fillText(clip?.sentence ?? "", width / 2, height - caption / 3);
}

export function AslSample({
  step,
  onLines,
}: {
  step: number;
  onLines?: (ids: string[]) => void;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [problem, setProblem] = useState("");
  const clip = clips[Math.min(step, Math.max(clips.length - 1, 0))] ?? null;

  useEffect(() => {
    let cancelled = false;
    Promise.all(
      SIGN_ORDER.map(async (id) => {
        const response = await fetch(`${API}/api/v1/dev/asl-research/clips/${id}`);
        if (!response.ok) return null;
        return response.json() as Promise<Clip>;
      }),
    )
      .then((body) => {
        if (cancelled) return;
        const ready = body.filter((item): item is Clip => item !== null);
        setClips(ready);
        onLines?.(ready.map((item) => item.id));
        if (!ready.length) setProblem("The ASL sentences could not load.");
      })
      .catch((error: unknown) => {
        if (!cancelled) setProblem(error instanceof Error ? error.message : "The ASL sentence could not load.");
      });
    return () => {
      cancelled = true;
    };
  }, [onLines]);

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
