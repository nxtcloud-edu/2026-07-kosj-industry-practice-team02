import { readFileSync } from "node:fs";

import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { parse } from "yaml";

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

export function loadContracts() {
  const openApiPath = new URL("../../../contracts/openapi-v1.yaml", import.meta.url);
  const standalonePath = new URL(
    "../../../contracts/chat-response.schema.json",
    import.meta.url,
  );

  return {
    openApi: parse(readFileSync(openApiPath, "utf8")),
    standaloneChatResponse: readJson(standalonePath),
  };
}

function rewriteComponentRefs(value, schemaNames) {
  if (Array.isArray(value)) {
    return value.map((item) => rewriteComponentRefs(item, schemaNames));
  }
  if (value === null || typeof value !== "object") {
    return value;
  }

  const rewritten = {};
  for (const [key, child] of Object.entries(value)) {
    if (key !== "$ref") {
      rewritten[key] = rewriteComponentRefs(child, schemaNames);
      continue;
    }

    if (typeof child !== "string") {
      throw new TypeError("OpenAPI schema $ref must be a string");
    }
    const prefix = "#/components/schemas/";
    if (!child.startsWith(prefix)) {
      throw new Error(`Unsupported OpenAPI schema reference: ${child}`);
    }
    const referencedName = child.slice(prefix.length);
    if (!referencedName || !schemaNames.has(referencedName)) {
      throw new Error(`Unknown OpenAPI component schema: ${referencedName}`);
    }
    rewritten.$ref = `#/$defs/${referencedName}`;
  }
  return rewritten;
}

export function extractOpenApiSchema(openApi, schemaName) {
  const schemas = openApi?.components?.schemas;
  if (schemas === null || typeof schemas !== "object" || Array.isArray(schemas)) {
    throw new TypeError("OpenAPI components.schemas must be an object");
  }
  if (!Object.hasOwn(schemas, schemaName)) {
    throw new Error(`Unknown OpenAPI root schema: ${schemaName}`);
  }

  const schemaNames = new Set(Object.keys(schemas));
  const definitions = Object.fromEntries(
    Object.entries(schemas).map(([name, schema]) => [
      name,
      rewriteComponentRefs(schema, schemaNames),
    ]),
  );

  return {
    $schema: "https://json-schema.org/draft/2020-12/schema",
    ...definitions[schemaName],
    $defs: definitions,
  };
}

function invariantError(instancePath, message) {
  return {
    instancePath,
    schemaPath: "#/x-sejong-state-invariant",
    keyword: "x-sejong-state-invariant",
    params: {},
    message,
  };
}

function failedQuestionInvariant(item, instancePath) {
  const errors = [];
  const expectedEligibility = item.fallback_reason === "INSUFFICIENT_GROUNDING";
  if (item.candidate_eligible !== expectedEligibility) {
    errors.push(invariantError(`${instancePath}/candidate_eligible`, "eligibility does not match fallback reason"));
  }
  if (Date.parse(item.text_expires_at) !== Date.parse(item.created_at) + 30 * 24 * 60 * 60 * 1000) {
    errors.push(invariantError(`${instancePath}/text_expires_at`, "expiry is not exactly 30 days"));
  }
  if ((item.masked_question === null) !== (item.text_purged_at !== null)) {
    errors.push(invariantError(instancePath, "masked text and purge time must transition together"));
  }
  if (
    item.text_purged_at !== null &&
    Date.parse(item.text_purged_at) < Date.parse(item.text_expires_at)
  ) {
    errors.push(invariantError(`${instancePath}/text_purged_at`, "purge time precedes expiry"));
  }
  return errors;
}

function candidateInvariant(item, instancePath) {
  const errors = [];
  const reviewFields = [item.reviewed_by, item.review_comment];
  const activationFields = [item.approved_at, item.activated_kb_id];
  if (
    ["DRAFTED", "PENDING_APPROVAL"].includes(item.status) &&
    [...reviewFields, ...activationFields].some((value) => value !== null)
  ) {
    errors.push(invariantError(instancePath, "unreviewed candidate contains review outcome fields"));
  }
  if (["APPROVED", "REJECTED"].includes(item.status)) {
    if (reviewFields.some((value) => value === null)) {
      errors.push(invariantError(instancePath, "reviewed candidate lacks review evidence"));
    }
    if (item.reviewed_by === item.created_by) {
      errors.push(invariantError(`${instancePath}/reviewed_by`, "candidate creator cannot self-review"));
    }
  }
  if (item.status === "APPROVED" && activationFields.some((value) => value === null)) {
    errors.push(invariantError(instancePath, "approved candidate lacks activation evidence"));
  }
  if (item.status === "APPROVED" && item.data_origin !== "OFFICIAL") {
    errors.push(invariantError(`${instancePath}/data_origin`, "approved candidate is not official"));
  }
  if (item.status === "REJECTED" && activationFields.some((value) => value !== null)) {
    errors.push(invariantError(instancePath, "rejected candidate contains activation evidence"));
  }
  return errors;
}

function withInvariant(validate, check) {
  const wrapped = (data) => {
    if (!validate(data)) {
      wrapped.errors = validate.errors;
      return false;
    }
    const errors = check(data);
    wrapped.errors = errors.length > 0 ? errors : null;
    return errors.length === 0;
  };
  wrapped.errors = null;
  return wrapped;
}

export function createContractValidators() {
  const { openApi, standaloneChatResponse } = loadContracts();
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  addFormats(ajv);
  ajv.addKeyword({
    keyword: "x-sejong-state-invariant",
    schemaType: "string",
    valid: true,
  });

  const compile = (schemaName) =>
    ajv.compile(extractOpenApiSchema(openApi, schemaName));

  const failedQuestionList = compile("FailedQuestionListResponse");
  const failedQuestionDetail = compile("FailedQuestionDetailResponse");
  const candidateList = compile("KBCandidateListResponse");

  return {
    request: ajv.compile(extractOpenApiSchema(openApi, "ChatRequest")),
    openApiResponse: ajv.compile(
      extractOpenApiSchema(openApi, "ChatResponse"),
    ),
    standaloneResponse: ajv.compile(standaloneChatResponse),
    serviceUnavailable: ajv.compile(
      extractOpenApiSchema(openApi, "ServiceUnavailableEnvelope"),
    ),
    adminError: compile("AdminErrorEnvelope"),
    failedQuestionList: withInvariant(failedQuestionList, (data) =>
      data.items.flatMap((item, index) => failedQuestionInvariant(item, `/items/${index}`)),
    ),
    failedQuestionDetail: withInvariant(failedQuestionDetail, (data) =>
      failedQuestionInvariant(data.item, "/item"),
    ),
    reasonConfirmation: compile("ReasonConfirmationResponse"),
    candidateList: withInvariant(candidateList, (data) =>
      data.items.flatMap((item, index) => candidateInvariant(item, `/items/${index}`)),
    ),
    candidateCreate: compile("KBCandidateCreateResponse"),
    candidateSubmit: compile("KBCandidateSubmitResponse"),
    candidateReview: compile("KBCandidateReviewResponse"),
  };
}

export function readFixture(relativePath) {
  return readJson(new URL(`../../../contracts/fixtures/${relativePath}`, import.meta.url));
}
