import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import openapiTS, { astToString } from "openapi-typescript";
import { parse } from "yaml";

const OPENAPI_URL = new URL(
  "../../../contracts/openapi-v1.yaml",
  import.meta.url,
);
const GENERATED_URL = new URL("../src/generated/api.ts", import.meta.url);
const GENERATOR_PACKAGE_URL = new URL(
  "../node_modules/openapi-typescript/package.json",
  import.meta.url,
);
const DISPLAY_SOURCE = "contracts/openapi-v1.yaml";

function readVersionMetadata() {
  const openApi = parse(readFileSync(OPENAPI_URL, "utf8"));
  const generatorPackage = JSON.parse(
    readFileSync(GENERATOR_PACKAGE_URL, "utf8"),
  );

  if (typeof openApi?.info?.version !== "string") {
    throw new TypeError("OpenAPI info.version must be a string");
  }
  if (typeof generatorPackage?.version !== "string") {
    throw new TypeError("openapi-typescript package version must be a string");
  }

  return {
    openApiVersion: openApi.info.version,
    generatorVersion: generatorPackage.version,
  };
}

export async function renderGeneratedApi() {
  const { openApiVersion, generatorVersion } = readVersionMetadata();
  const ast = await openapiTS(OPENAPI_URL, {
    alphabetize: true,
    arrayLength: true,
    defaultNonNullable: false,
    silent: true,
  });
  const body = astToString(ast).replaceAll("\r\n", "\n").trimStart();
  const banner = [
    "/**",
    ` * source: ${DISPLAY_SOURCE}`,
    ` * OpenAPI: ${openApiVersion}; generator: openapi-typescript ${generatorVersion}`,
    " * Generated deterministically; do not edit by hand.",
    " */",
    "",
  ].join("\n");

  return `${banner}${body.endsWith("\n") ? body : `${body}\n`}`;
}

export async function writeGeneratedApi() {
  const output = await renderGeneratedApi();
  mkdirSync(dirname(fileURLToPath(GENERATED_URL)), { recursive: true });
  writeFileSync(GENERATED_URL, output, "utf8");
}

export async function checkGeneratedApi() {
  if (!existsSync(GENERATED_URL)) {
    return false;
  }
  const expected = await renderGeneratedApi();
  return readFileSync(GENERATED_URL, "utf8") === expected;
}

const isMain =
  process.argv[1] !== undefined &&
  import.meta.url === pathToFileURL(process.argv[1]).href;

if (isMain) {
  if (process.argv.includes("--check")) {
    if (!(await checkGeneratedApi())) {
      console.error(
        "Generated API types are missing or stale. Run the contracts generator.",
      );
      process.exitCode = 1;
    }
  } else {
    await writeGeneratedApi();
  }
}
