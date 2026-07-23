import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

const tscUrl = new URL("../../../apps/web/node_modules/typescript/bin/tsc", import.meta.url);
const configUrl = new URL("./type-fixtures/tsconfig.json", import.meta.url);

test("generated chat response is a real compile-time discriminated union", () => {
  const completed = spawnSync(
    process.execPath,
    [fileURLToPath(tscUrl), "--project", fileURLToPath(configUrl), "--pretty", "false"],
    { encoding: "utf8" },
  );
  assert.equal(completed.status, 0, `${completed.stdout}${completed.stderr}`);
});
