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

export function createContractValidators() {
  const { openApi, standaloneChatResponse } = loadContracts();
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  addFormats(ajv);

  return {
    request: ajv.compile(extractOpenApiSchema(openApi, "ChatRequest")),
    openApiResponse: ajv.compile(
      extractOpenApiSchema(openApi, "ChatResponse"),
    ),
    standaloneResponse: ajv.compile(standaloneChatResponse),
    serviceUnavailable: ajv.compile(
      extractOpenApiSchema(openApi, "ServiceUnavailableEnvelope"),
    ),
  };
}

export function readFixture(relativePath) {
  return readJson(new URL(`../../../contracts/fixtures/${relativePath}`, import.meta.url));
}
