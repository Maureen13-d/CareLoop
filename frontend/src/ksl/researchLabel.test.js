import assert from "node:assert/strict";
import test from "node:test";

import { RESEARCH_CITATION, RESEARCH_LABEL } from "./researchLabel.js";

test("research footer keeps the burned-in wording and the citation", () => {
  assert.equal(
    RESEARCH_LABEL,
    "RESEARCH SAMPLE: single word. Not a patient message. Not reviewed.",
  );
  assert.match(RESEARCH_CITATION, /10\.1016\/j\.dib\.2025\.111502/);
  assert.match(RESEARCH_CITATION, /10\.5281\/zenodo\.14974973/);
  assert.match(RESEARCH_CITATION, /Maina E\./);
});
