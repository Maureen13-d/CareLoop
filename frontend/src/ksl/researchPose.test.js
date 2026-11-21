import assert from "node:assert/strict";
import test from "node:test";

import { avatarSegments, boneEnd, rotateVector, stickSegments } from "./researchPose.js";

test("an identity bone points along rest, which is image-down", () => {
  const end = boneEnd([0, 0], [0, 0, 0, 1], 2);
  assert.ok(Math.abs(end[0]) < 1e-6);
  assert.ok(Math.abs(end[1] - 2) < 1e-6);
});

test("a half-turn about x flips the rest direction", () => {
  const turned = rotateVector([1, 0, 0, 0], [0, 1, 0]);
  assert.ok(Math.abs(turned[1] + 1) < 1e-6);
});

test("the avatar keeps fixed shoulders while the stickman follows the landmarks", () => {
  const frame = {
    pose: Array.from({ length: 33 }, () => [0.2, 0.4]),
    left_hand: [],
    right_hand: [],
    arms: {
      left: {
        upper: [0, 0, 0, 1],
        lower: [0, 0, 0, 1],
      },
      right: {
        upper: [0, 0, 0, 1],
        lower: [0, 0, 0, 1],
      },
    },
  };
  frame.pose[11] = [-1.2, 0.3];
  frame.pose[12] = [1.2, 0.3];
  const stick = stickSegments(frame);
  const avatar = avatarSegments(frame);
  assert.equal(stick[0][0], -1.2);
  assert.equal(avatar[0][0], -0.55);
  assert.notEqual(stick[0][0], avatar[0][0]);
});
