import assert from "node:assert/strict";
import test from "node:test";

import { feedbackItems } from "../src/data.js";

test("fixture feedback has stable unique identifiers", () => {
  const ids = feedbackItems.map((item) => item.id);
  assert.equal(new Set(ids).size, feedbackItems.length);
});

test("fixture covers every displayed status", () => {
  assert.deepEqual(
    [...new Set(feedbackItems.map((item) => item.status))].sort(),
    ["closed", "open", "planned"],
  );
});
