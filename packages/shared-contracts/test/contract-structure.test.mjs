import assert from "node:assert/strict";
import test from "node:test";

import {
  extractOpenApiSchema,
  loadContracts,
} from "../src/contract-validator.mjs";

const { openApi } = loadContracts();

test("readiness and chat share the approved 503 response reference", () => {
  const expected = "#/components/responses/ServiceUnavailable";
  assert.equal(openApi.paths["/ready"].get.responses["503"].$ref, expected);
  assert.equal(
    openApi.paths["/api/v1/chat"].post.responses["503"].$ref,
    expected,
  );
});

test("503 Retry-After is an integer of at least one second", () => {
  const retryAfter =
    openApi.components.responses.ServiceUnavailable.headers["Retry-After"].schema;
  assert.deepEqual(retryAfter, { type: "integer", minimum: 1 });
});

test("HTTP 200 chat status excludes SYSTEM_ERROR", () => {
  const statuses = openApi.components.schemas.ChatAnswerStatus.enum;
  assert.deepEqual(statuses, ["SUCCESS", "FOLLOWUP", "FALLBACK"]);
  assert.ok(!statuses.includes("SYSTEM_ERROR"));
});

test("OpenAPI extraction rejects external and unknown component references", () => {
  assert.throws(
    () =>
      extractOpenApiSchema(
        { components: { schemas: { Root: { $ref: "https://example.invalid/schema" } } } },
        "Root",
      ),
    /Unsupported OpenAPI schema reference/,
  );
  assert.throws(
    () =>
      extractOpenApiSchema(
        { components: { schemas: { Root: { $ref: "#\/components\/schemas\/Missing" } } } },
        "Root",
      ),
    /Unknown OpenAPI component schema/,
  );
});

test("OpenAPI extraction does not mutate its input", () => {
  const input = structuredClone(openApi);
  const before = structuredClone(input);
  extractOpenApiSchema(input, "ChatResponse");
  assert.deepEqual(input, before);
});
