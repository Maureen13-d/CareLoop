import assert from "node:assert/strict";
import test from "node:test";

import { SIGN_ORDER, SIGN_REPLIES } from "./signReplies.js";

test("Hi is answered with a greeting", () => {
  const labels = SIGN_REPLIES[SIGN_ORDER[0]].map((item) => item.label);
  assert.deepEqual(labels, ["Hello", "Hi, I'm here"]);
  assert.equal(SIGN_ORDER.length, 11);
  const pain = Object.values(SIGN_REPLIES)
    .flat()
    .map((item) => item.label);
  assert.equal(pain.includes("I'm in extreme pain"), true);
});
