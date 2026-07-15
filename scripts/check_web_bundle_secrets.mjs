import { lstat, readdir, readFile } from "node:fs/promises";
import path from "node:path";


const markerNames = [
  ["SUPABASE", "SERVICE_ROLE_KEY"].join("_"),
  ["LLM", "API_KEY"].join("_"),
  ["CONTEXT_TOKEN", "SECRET"].join("_"),
  ["DATABASE", "URL"].join("_"),
];
const markerBuffers = markerNames.map((marker) => Buffer.from(marker, "utf8"));
const sentinel = process.env.SEJONG_WEB_SECRET_SENTINEL;
const sentinelBuffer = sentinel ? Buffer.from(sentinel, "utf8") : null;


function displayPath(value) {
  return value.split(path.sep).join("/");
}


function countOccurrences(content, needle) {
  let count = 0;
  let offset = 0;
  while (offset <= content.length - needle.length) {
    const index = content.indexOf(needle, offset);
    if (index === -1) {
      break;
    }
    count += 1;
    offset = index + Math.max(needle.length, 1);
  }
  return count;
}


async function isDirectory(literalPath) {
  try {
    const item = await lstat(literalPath);
    return item.isDirectory() && !item.isSymbolicLink();
  } catch {
    return false;
  }
}


async function collectFiles(root, includeFile, files) {
  if (!(await isDirectory(root))) {
    return;
  }
  const entries = await readdir(root, { withFileTypes: true });
  entries.sort((left, right) => left.name.localeCompare(right.name, "en"));
  for (const entry of entries) {
    if (entry.isSymbolicLink()) {
      continue;
    }
    const literalPath = path.join(root, entry.name);
    if (entry.isDirectory()) {
      await collectFiles(literalPath, includeFile, files);
    } else if (entry.isFile() && includeFile(entry.name)) {
      files.push(literalPath);
    }
  }
}


function addResult(results, relativePath, rule, count) {
  results.push({ path: relativePath, rule, count });
}


function writeResults(results) {
  results.sort((left, right) => {
    const leftKey = `${left.path}|${left.rule}`;
    const rightKey = `${right.path}|${right.rule}`;
    return leftKey.localeCompare(rightKey, "en");
  });
  for (const result of results) {
    process.stdout.write(`${result.path} rule=${result.rule} count=${result.count}\n`);
  }
}


async function scanBuild(buildArgument) {
  const buildRoot = path.resolve(buildArgument);
  if (!(await isDirectory(buildRoot))) {
    writeResults([
      { path: displayPath(buildArgument), rule: "BUILD_DIRECTORY_MISSING", count: 1 },
    ]);
    return 2;
  }

  const files = [];
  await collectFiles(path.join(buildRoot, "static"), () => true, files);
  await collectFiles(
    path.join(buildRoot, "server", "app"),
    (name) => name.endsWith(".html") || name.endsWith(".rsc"),
    files,
  );
  await collectFiles(
    path.join(buildRoot, "server", "pages"),
    (name) => name.endsWith(".html"),
    files,
  );

  if (files.length === 0) {
    writeResults([
      { path: displayPath(buildArgument), rule: "NO_BROWSER_ARTIFACTS", count: 1 },
    ]);
    return 2;
  }

  const findings = [];
  const operationalResults = [];
  for (const literalPath of files) {
    const relativePath = displayPath(path.relative(buildRoot, literalPath));
    try {
      const item = await lstat(literalPath);
      if (!item.isFile() || item.isSymbolicLink()) {
        continue;
      }
      const content = await readFile(literalPath);
      const markerCount = markerBuffers.reduce(
        (total, marker) => total + countOccurrences(content, marker),
        0,
      );
      if (markerCount > 0) {
        addResult(findings, relativePath, "SERVER_SECRET_NAME", markerCount);
      }
      if (sentinelBuffer !== null) {
        const sentinelCount = countOccurrences(content, sentinelBuffer);
        if (sentinelCount > 0) {
          addResult(findings, relativePath, "SECRET_SENTINEL", sentinelCount);
        }
      }
    } catch {
      addResult(operationalResults, relativePath, "FILE_READ_ERROR", 1);
    }
  }

  writeResults([...operationalResults, ...findings]);
  if (operationalResults.length > 0) {
    return 2;
  }
  return findings.length > 0 ? 1 : 0;
}


const buildArgument = process.argv[2];
if (!buildArgument) {
  writeResults([{ path: "<missing>", rule: "BUILD_DIRECTORY_MISSING", count: 1 }]);
  process.exitCode = 2;
} else {
  try {
    process.exitCode = await scanBuild(buildArgument);
  } catch {
    writeResults([{ path: displayPath(buildArgument), rule: "SCANNER_ERROR", count: 1 }]);
    process.exitCode = 2;
  }
}
