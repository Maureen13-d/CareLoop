/** Time-based playback of a recorded packet. This file does not invent signs. */

export const BLEND_MS = 200;
export const SPEEDS = [0.75, 1];
export const HONESTY = "PLACEHOLDER MOTION: NOT ASL";
export const TEST_LABEL = "TEST_MOTION_NOT_SIGN";
export const PRESETS = [
  { id: "coast", skin: "#8d5524", cloth: "#0f6e6e" },
  { id: "highland", skin: "#c68642", cloth: "#1d4e89" },
  { id: "city", skin: "#e0ac69", cloth: "#3d348b" },
  { id: "clinic", skin: "#f1c27d", cloth: "#2e7d32" },
];

const HAND_OR_FACE = /hand|thumb|index|middle|ring|pinky|face|eye|jaw|mouth|brow|cheek|nose|tongue/;

export function slerp(left, right, amount) {
  const t = Math.min(1, Math.max(0, amount));
  let dot = 0;
  for (let index = 0; index < 4; index += 1) dot += left[index] * right[index];
  const use = dot < 0 ? right.map((value) => -value) : right;
  const theta = Math.acos(Math.min(1, Math.abs(dot)));
  if (theta < 1e-6) return left.slice();
  const scaleLeft = Math.sin((1 - t) * theta) / Math.sin(theta);
  const scaleRight = Math.sin(t * theta) / Math.sin(theta);
  return left.map((value, index) => value * scaleLeft + use[index] * scaleRight);
}

export function smoothJoint(name, previous, next, amount) {
  if (HAND_OR_FACE.test(name)) return next.slice();
  return next.map((value, index) => previous[index] + (value - previous[index]) * amount);
}

export function chooseFallback(hasAvatar, hasVideo, hasCaption) {
  if (hasAvatar) return "avatar";
  if (hasVideo) return "video";
  if (hasCaption) return "captions";
  return "human";
}

export function createCache(cap = 8) {
  const rows = new Map();
  return {
    put(id, clip) {
      if (rows.has(id)) rows.delete(id);
      rows.set(id, clip);
      while (rows.size > cap) rows.delete(rows.keys().next().value);
    },
    get(id) {
      return rows.get(id) || null;
    },
    size() {
      return rows.size;
    },
  };
}

export function testWave(frames = 8) {
  const body = [];
  for (let index = 0; index < frames; index += 1) {
    const wave = Math.sin(index / 8) * 35;
    const half = (wave * Math.PI) / 360;
    body.push({ upper_arm_r: [0, 0, Math.sin(half), Math.cos(half)] });
  }
  return {
    label: TEST_LABEL,
    fps: 30,
    caption: "This motion is a test wave. It is not American Sign Language.",
    frames: body,
  };
}

export function createPlayer(clip, options = {}) {
  const frames = clip?.frames || [];
  const fps = clip?.fps || 30;
  let phase = "idle";
  let speed = 1;
  let paused = false;
  let elapsed = 0;
  let frame = 0;
  let blendLeft = 0;
  const reduceMotion = Boolean(options.reduceMotion);

  function procedural() {
    return phase !== "signing" && phase !== "holding" && phase !== "step";
  }

  function pose() {
    const sample = frames.length ? frames[Math.min(frame, frames.length - 1)] : null;
    const label = clip?.label || "";
    return {
      phase,
      frame,
      speed,
      paused,
      blendLeft,
      procedural: procedural(),
      face: procedural() ? "procedural" : "clip",
      head: procedural() ? "procedural" : "clip",
      gaze: procedural() ? "procedural" : "clip",
      torso: procedural() ? "procedural" : "clip",
      body: sample,
      caption: clip?.caption || "",
      honesty: label === TEST_LABEL || label === HONESTY ? HONESTY : "",
    };
  }

  return {
    pose,
    play() {
      if (!frames.length) {
        phase = "idle";
        return pose();
      }
      blendLeft = BLEND_MS;
      elapsed = 0;
      frame = 0;
      paused = false;
      phase = reduceMotion ? "step" : "signing";
      return pose();
    },
    pause() {
      paused = true;
      return pose();
    },
    replay() {
      return this.play();
    },
    setSpeed(value) {
      if (!SPEEDS.includes(value)) throw new Error("speed must be 0.75 or 1");
      speed = value;
      return pose();
    },
    step() {
      if (!frames.length) return pose();
      frame = Math.min(frames.length - 1, frame + 1);
      phase = frame >= frames.length - 1 ? "holding" : "step";
      return pose();
    },
    listen() {
      phase = "attentive";
      return pose();
    },
    finishHold() {
      if (phase === "holding") phase = "returning";
      return pose();
    },
    returnIdle() {
      phase = "idle";
      frame = 0;
      return pose();
    },
    tick(dtMs) {
      if (blendLeft > 0) blendLeft = Math.max(0, blendLeft - dtMs);
      if (reduceMotion || paused || phase !== "signing") return pose();
      elapsed += dtMs * speed;
      const index = Math.floor((elapsed / 1000) * fps);
      if (index >= frames.length) {
        frame = frames.length - 1;
        phase = "holding";
      } else {
        frame = index;
      }
      return pose();
    },
  };
}
