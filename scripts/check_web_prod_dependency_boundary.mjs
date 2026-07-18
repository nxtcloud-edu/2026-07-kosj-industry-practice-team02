import { execFileSync } from "node:child_process";
import { mkdtempSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const repositoryRoot = resolve(import.meta.dirname, "..");
const forbiddenPackage = /(^|[^a-z-])(?:@playwright\/test|playwright-core|playwright)(?:@|$)/i;

function run(args) {
  const pnpmArgs = ["pnpm", ...args];
  const command =
    process.platform === "win32"
      ? ["corepack.cmd", ...pnpmArgs].join(" ")
      : ["corepack", ...pnpmArgs];
  const executable = process.platform === "win32" ? process.env.ComSpec ?? "cmd.exe" : command[0];
  const executableArgs =
    process.platform === "win32" ? ["/d", "/c", command] : command.slice(1);

  return execFileSync(executable, executableArgs, {
    cwd: repositoryRoot,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
}

const deployDirectory = mkdtempSync(join(tmpdir(), "sejong-web-prod-"));

try {
  const productionList = run(["--filter", "@sejong-ai/web", "list", "--prod", "--depth", "Infinity"]);
  const deployedOutput = run([
    "--filter",
    "@sejong-ai/web",
    "deploy",
    "--prod",
    "--legacy",
    "--ignore-scripts",
    deployDirectory,
  ]);
  const deployedPackages = readdirSync(join(deployDirectory, "node_modules", ".pnpm"));
  const violations = [
    ...productionList.split(/\r?\n/).filter((line) => forbiddenPackage.test(line)),
    ...deployedPackages.filter((directory) => /^(?:@playwright\+test|playwright-core|playwright)@/.test(directory)),
  ];

  if (violations.length > 0) {
    throw new Error(
      `Playwright must not be present in @sejong-ai/web production dependencies:\n${violations.join("\n")}`,
    );
  }

  if (deployedOutput.length === 0) {
    throw new Error("pnpm deploy produced no output.");
  }

  console.log("[PASS] web production dependency boundary: no Playwright packages");
} finally {
  rmSync(deployDirectory, { recursive: true, force: true });
}
