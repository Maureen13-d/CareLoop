import assert from "node:assert/strict";
import test from "node:test";

import {
  BLEND_MS,
  HONESTY,
  PRESETS,
  chooseFallback,
  createCache,
  createPlayer,
  slerp,
  smoothJoint,
  testWave,
} from "./engine.js";

test("slerp stays on the identity when both poses match", () => {
  const identity = [0, 0, 0, 1];
  const mid = slerp(identity, identity, 0.5);
  assert.ok(Math.abs(mid[3] - 1) < 1e-6);
});

test("hands and face are not smoothed", () => {
  const previous = [0, 0, 0, 1];
  const next = [0, 0, 1, 0];
  assert.deepEqual(smoothJoint("thumb_tip", previous, next, 0.5), next);
  assert.deepEqual(smoothJoint("eyeBlinkLeft", previous, next, 0.5), next);
  const spine = smoothJoint("spine", previous, next, 0.5);
  assert.notDeepEqual(spine, next);
  assert.equal(spine[2], 0.5);
});

test("signing uses the clip and turns procedural channels off", () => {
  const player = createPlayer(testWave());
  const started = player.play();
  assert.equal(started.phase, "signing");
  assert.equal(started.procedural, false);
  assert.equal(started.face, "clip");
  assert.equal(started.head, "clip");
  assert.equal(started.gaze, "clip");
  assert.equal(started.torso, "clip");
  assert.equal(started.honesty, HONESTY);
  assert.equal(started.blendLeft, BLEND_MS);
  assert.ok(BLEND_MS >= 120 && BLEND_MS <= 250);
  const moved = player.tick(100);
  assert.equal(moved.frame, 3);
});

test("reduce motion steps instead of playing through a sign", () => {
  const player = createPlayer(testWave(), { reduceMotion: true });
  const started = player.play();
  assert.equal(started.phase, "step");
  const held = player.tick(1000);
  assert.equal(held.frame, 0);
  assert.equal(player.step().frame, 1);
  assert.ok(held.caption.length > 0);
});

test("pause, replay, speed, and the idle cycle", () => {
  const player = createPlayer(testWave());
  player.play();
  player.pause();
  assert.equal(player.tick(500).frame, 0);
  player.setSpeed(0.75);
  player.replay();
  const slow = player.tick(100);
  assert.equal(slow.frame, 2);
  player.listen();
  assert.equal(player.pose().phase, "attentive");
  assert.equal(player.pose().procedural, true);
  player.play();
  player.tick(10_000);
  assert.equal(player.pose().phase, "holding");
  player.finishHold();
  assert.equal(player.pose().phase, "returning");
  player.returnIdle();
  assert.equal(player.pose().phase, "idle");
});

test("fallback ladder and a small cache", () => {
  assert.equal(chooseFallback(true, true, true), "avatar");
  assert.equal(chooseFallback(false, true, true), "video");
  assert.equal(chooseFallback(false, false, true), "captions");
  assert.equal(chooseFallback(false, false, false), "human");
  const cache = createCache(2);
  cache.put("a", 1);
  cache.put("b", 2);
  cache.put("c", 3);
  assert.equal(cache.get("a"), null);
  assert.equal(cache.size(), 2);
  assert.ok(PRESETS.length >= 4);
});
