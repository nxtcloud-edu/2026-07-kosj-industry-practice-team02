from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GITHUB_ROOT = REPOSITORY_ROOT / ".github"

PINNED_ACTIONS = {
    "actions/checkout": "de0fac2e4500dabe0009e67214ff5f5447ce83dd",  # v6.0.2
    "actions/setup-node": "48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e",  # v6.4.0
    "actions/setup-python": "a309ff8b426b58ec0e2a45f0f869d46889d02405",  # v6.2.0
}


class GitHubCollaborationConfigTests(unittest.TestCase):
    maxDiff = None

    def read_required(self, relative_path: str) -> str:
        path = REPOSITORY_ROOT / relative_path
        self.assertTrue(path.is_file(), f"missing required collaboration file: {relative_path}")
        return path.read_text(encoding="utf-8")

    def workflow(self, name: str) -> str:
        return self.read_required(f".github/workflows/{name}")

    def test_policy_workflow_always_triggers_without_path_filter(self) -> None:
        text = self.workflow("collaboration-policy.yml")
        for token in (
            "pull_request:",
            "opened",
            "synchronize",
            "reopened",
            "ready_for_review",
            "push:",
            "branches: [main]",
            "workflow_dispatch:",
        ):
            self.assertIn(token, text)
        self.assertNotRegex(text, r"(?m)^\s+paths(?:-ignore)?:")
        self.assertNotIn("pull_request_target", text)

    def test_workflows_are_read_only_secret_free_and_disable_checkout_credentials(self) -> None:
        for name in ("collaboration-policy.yml", "frontend-ci.yml"):
            with self.subTest(workflow=name):
                text = self.workflow(name)
                self.assertRegex(text, r"(?ms)^permissions:\s*\n\s+contents:\s*read\s*$")
                self.assertNotRegex(text, r"(?m)^\s+(?:actions|checks|contents|deployments|issues|packages|pull-requests|statuses):\s*write\s*$")
                self.assertNotIn("${{ secrets.", text)
                self.assertIn("persist-credentials: false", text)
                self.assertNotIn("pull_request_target", text)

    def test_official_actions_use_reviewed_full_commit_pins(self) -> None:
        combined = "\n".join(
            self.workflow(name)
            for name in ("collaboration-policy.yml", "frontend-ci.yml")
        )
        uses = re.findall(r"uses:\s*(actions/(?:checkout|setup-node|setup-python))@([0-9a-f]{40})", combined)
        self.assertTrue(uses, "expected official GitHub actions pinned to full commit SHAs")
        for action, sha in uses:
            self.assertEqual(PINNED_ACTIONS[action], sha)
        for action, sha in PINNED_ACTIONS.items():
            self.assertIn(f"uses: {action}@{sha}", combined)

    def test_policy_uses_pr_author_not_actor_and_argument_safe_inputs(self) -> None:
        text = self.workflow("collaboration-policy.yml")
        for token in (
            "github.event.pull_request.user.login",
            "github.event.pull_request.base.sha",
            "github.event.pull_request.head.sha",
            "vars.FRONTEND_COLLABORATOR_LOGIN",
            "PR_AUTHOR:",
            "BASE_SHA:",
            "HEAD_SHA:",
            "FRONTEND_LOGIN:",
            '--base-sha "$BASE_SHA"',
            '--head-sha "$HEAD_SHA"',
            '--pr-author "$PR_AUTHOR"',
            '--frontend-login "$FRONTEND_LOGIN"',
        ):
            self.assertIn(token, text)
        self.assertNotIn("github.actor ==", text)
        self.assertNotIn("github.actor !=", text)

    def test_policy_executes_trusted_base_checkers_against_candidate(self) -> None:
        text = self.workflow("collaboration-policy.yml")
        for token in (
            "path: trusted",
            "path: candidate",
            "fetch-depth: 0",
            "../trusted/scripts/check_collaboration_scope.py",
            "trusted/scripts/check_repository_docs.py",
            "trusted/scripts/check_secret_patterns.ps1",
            "-RepositoryRoot candidate",
            "candidate",
        ):
            self.assertIn(token, text)

    def test_policy_runs_all_static_gates_and_always_reports(self) -> None:
        text = self.workflow("collaboration-policy.yml")
        for token in (
            "check_collaboration_scope.py",
            "check_repository_docs.py",
            "check_secret_patterns.ps1",
            "@sejong-ai/shared-contracts generate:check",
            "if: always()",
            "needs:",
            "policy-summary",
        ):
            self.assertIn(token, text)
        self.assertNotRegex(text, r"(?i)(docker|supabase\s+(?:start|db)|deepseek|deploy)")

    def test_frontend_gate_is_frozen_complete_and_has_an_always_summary(self) -> None:
        text = self.workflow("frontend-ci.yml")
        for token in (
            "pull_request:",
            "push:",
            "workflow_dispatch:",
            "--frozen-lockfile --ignore-scripts",
            "@sejong-ai/shared-contracts generate:check",
            "@sejong-ai/shared-contracts test",
            "@sejong-ai/web lint",
            "@sejong-ai/web typecheck",
            "@sejong-ai/web test",
            "@sejong-ai/web build",
            "check_web_bundle_secrets.mjs apps/web/.next",
            "check_web_prod_dependency_boundary.mjs",
            "playwright install --with-deps chromium",
            "--dir tools/web-e2e test",
            "NEXT_TELEMETRY_DISABLED: \"1\"",
            "if: always()",
            "frontend-summary",
        ):
            self.assertIn(token, text)
        self.assertNotIn("upload-artifact", text)
        self.assertNotRegex(text, r"(?i)(docker|supabase\s+(?:start|db)|deepseek[^_])")

    def test_frontend_diff_detection_distinguishes_changes_from_git_errors(self) -> None:
        text = self.workflow("frontend-ci.yml")
        for token in (
            "DIFF_STATUS=$?",
            'if [[ "$DIFF_STATUS" -eq 0 ]]',
            'elif [[ "$DIFF_STATUS" -eq 1 ]]',
            'exit 2',
        ):
            self.assertIn(token, text)

    def test_frontend_detection_includes_every_gate_input(self) -> None:
        text = self.workflow("frontend-ci.yml")
        for token in (
            ".npmrc",
            ".github/workflows/frontend-ci.yml",
            "scripts/check_web_bundle_secrets.mjs",
            "scripts/check_web_prod_dependency_boundary.mjs",
        ):
            self.assertIn(token, text)

    def test_build_uses_only_equal_fixed_synthetic_sentinels(self) -> None:
        text = self.workflow("frontend-ci.yml")
        sentinel = "synthetic-ci-bundle-sentinel-not-a-secret"
        self.assertGreaterEqual(text.count(sentinel), 6)
        for name in (
            "SEJONG_WEB_SECRET_SENTINEL",
            "DATABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "LLM_API_KEY",
            "CONTEXT_TOKEN_SECRET",
            "DEEPSEEK_API_KEY",
        ):
            self.assertIn(f"{name}: {sentinel}", text)
        self.assertNotIn("${{ secrets.", text)

    def test_templates_and_ownership_document_the_human_boundary(self) -> None:
        pr = self.read_required(".github/PULL_REQUEST_TEMPLATE.md")
        issue = self.read_required(".github/ISSUE_TEMPLATE/contract-gap.yml")
        ownership = self.read_required(".github/OWNERSHIP.md")
        for token in ("TASK ID", "구현 노트", "테스트", "비밀", "자가 병합"):
            self.assertIn(token, pr)
        for token in ("[CONTRACT]", "expected contract", "workaround"):
            self.assertIn(token, issue)
        for token in (
            "apps/web/src/**",
            "tools/web-e2e/e2e/**",
            "OWNER_REVIEW_REQUIRED",
            "GitHub Free",
            "direct `main` push",
        ):
            self.assertIn(token, ownership)


if __name__ == "__main__":
    unittest.main()
