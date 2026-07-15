import assert from "node:assert/strict";
import test from "node:test";

import {
  createContractValidators,
  readFixture,
} from "../src/contract-validator.mjs";

const validators = createContractValidators();

const requestCases = [
  ["valid-first-request.json", true],
  ["valid-null-context.json", true],
  ["invalid-session-id.json", false, { keyword: "additionalProperties", path: "", property: "session_id" }],
].map(([fixture, valid, error]) => ({
  contract: "OpenAPI ChatRequest",
  fixture: `chat-request/${fixture}`,
  validate: validators.request,
  valid,
  error,
}));

const responseExpectations = [
  ["valid-success.json", true],
  ["invalid-success-empty-sources.json", false, { keyword: "minItems", path: "/sources" }],
  ["valid-followup.json", true],
  ["valid-fallback-no-office.json", true],
  ["valid-fallback-office.json", true],
  ["invalid-fallback-context.json", false, { keyword: "const", path: "/context_token" }],
  ["invalid-missing-context.json", false, { keyword: "required", path: "", property: "context_token" }],
  ["invalid-session-id.json", false, { keyword: "additionalProperties", path: "", property: "session_id" }],
  ["invalid-office-missing-id.json", false, { keyword: "required", path: "/fallback/office", property: "id" }],
  ["invalid-fallback-extra-property.json", false, { keyword: "additionalProperties", path: "/fallback", property: "provider_debug" }],
];

const responseCases = responseExpectations.flatMap(([fixture, valid, error]) => [
  {
    contract: "OpenAPI ChatResponse",
    fixture: `chat-response/${fixture}`,
    validate: validators.openApiResponse,
    valid,
    error,
  },
  {
    contract: "standalone ChatResponse",
    fixture: `chat-response/${fixture}`,
    validate: validators.standaloneResponse,
    valid,
    error,
  },
]);

const errorCases = [
  ["valid-service-unavailable.json", true],
  ["invalid-code.json", false, { keyword: "const", path: "/error/code" }],
  ["invalid-extra-property.json", false, { keyword: "additionalProperties", path: "/error", property: "provider" }],
  ["invalid-request-id.json", false, { keyword: "required", path: "/error", property: "request_id" }],
].map(([fixture, valid, error]) => ({
  contract: "OpenAPI ServiceUnavailableEnvelope",
  fixture: `errors/${fixture}`,
  validate: validators.serviceUnavailable,
  valid,
  error,
}));

const cases = [...requestCases, ...responseCases, ...errorCases];
assert.equal(cases.length, 27, "fixture matrix must contain exactly 27 validations");

function summarizeErrors(errors = []) {
  return errors.map(({ instancePath, keyword, params }) => ({
    instancePath,
    keyword,
    property: params?.missingProperty ?? params?.additionalProperty,
  }));
}

function hasExpectedError(errors, expected) {
  return errors.some(
    ({ instancePath, keyword, params }) =>
      keyword === expected.keyword &&
      instancePath === expected.path &&
      (expected.property === undefined ||
        params?.missingProperty === expected.property ||
        params?.additionalProperty === expected.property),
  );
}

for (const fixtureCase of cases) {
  test(`${fixtureCase.contract}: ${fixtureCase.fixture}`, () => {
    const payload = readFixture(fixtureCase.fixture);
    assert.match(
      JSON.stringify(payload),
      /시연용 샘플/,
      "contract fixtures must remain clearly marked synthetic samples",
    );
    const actual = fixtureCase.validate(payload);
    const errors = fixtureCase.validate.errors ?? [];

    assert.equal(
      actual,
      fixtureCase.valid,
      `unexpected validity: ${JSON.stringify(summarizeErrors(errors))}`,
    );
    if (!fixtureCase.valid) {
      assert.ok(
        hasExpectedError(errors, fixtureCase.error),
        `expected error semantics not found: ${JSON.stringify(summarizeErrors(errors))}`,
      );
    }
  });
}
