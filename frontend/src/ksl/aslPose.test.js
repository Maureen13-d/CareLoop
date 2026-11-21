import assert from "node:assert/strict";
import test from "node:test";

import { ASL_LABEL, frameLines } from "./aslPose.js";

test("the ASL banner names the dataset and refuses a patient message", () => {
  assert.match(ASL_LABEL, /How2Sign/);
  assert.match(ASL_LABEL, /Not a patient message/);
});

test("an unverified hand is left out of the drawing", () => {
  const points = Array.from({ length: 55 }, (_, index) => [index, 0]);
  const lines = frameLines(points, true, false);
  assert.equal(lines.some((line) => line[0] === 25 || line[2] === 25), false);
  assert.equal(lines.some((line) => line[0] === 40 || line[2] === 40), true);
});
