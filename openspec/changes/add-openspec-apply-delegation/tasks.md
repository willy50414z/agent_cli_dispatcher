## 1. Installer CLI

- [x] 1.1 [codex-only] Add an `agent-dispatch install_delegant` command that targets the current project by default.
- [x] 1.2 [delegate:deepseek] Draft the project-local managed guidance block for OpenSpec delegation policy.
- [x] 1.3 [codex-only] Implement idempotent managed-block install/update behavior for the project guidance file.
- [x] 1.4 [delegate:test] Add CLI tests for project install, managed-block update, and no install side effects during package installation.

## 2. Delegation Levels

- [x] 2.1 [delegate:deepseek] Draft Level 1 guidance where Codex selectively delegates bounded low-risk tasks.
- [x] 2.2 [delegate:deepseek] Draft Level 2 guidance where submodels draft or implement all eligible non-`codex-only` tasks.
- [x] 2.3 [codex-only] Implement level selection in the installer, including interactive choice and safe non-interactive default behavior.
- [x] 2.4 [codex-only] Ensure both levels preserve Codex authority over integration, verification, and task checkbox completion.

## 3. Task Tagging Guidance

- [x] 3.1 [codex-only] Locate the durable instruction surface for OpenSpec propose/apply skill behavior in this environment.
- [x] 3.2 [delegate:deepseek] Draft task-generation guidance that adds lightweight delegation tags to suitable `tasks.md` entries.
- [x] 3.3 [codex-only] Integrate the delegation tag guidance into the OpenSpec propose workflow without changing existing checkbox parsing semantics.

## 4. Apply Delegation Workflow

- [x] 4.1 [delegate:deepseek] Draft the apply workflow rules for parsing `[delegate:*]` and `[codex-only]` tags from pending tasks.
- [x] 4.2 [codex-only] Implement the cost-first routing policy in the apply guidance, including Codex override authority.
- [x] 4.3 [delegate:deepseek] Draft minimal delegation prompt packet templates for implementation, test, review, and diagnosis modes.
- [x] 4.4 [codex-only] Add authority-boundary rules that prevent submodels from changing OpenSpec scope or marking task checkboxes complete.
- [x] 4.5 [delegate:optional] Add fallback behavior for unavailable targets and one-attempt escalation for unusable delegated output.

## 5. Verification And Documentation

- [x] 5.1 [delegate:test] Add focused fixtures or tests for tag parsing and routing if the implementation introduces executable helper code.
- [x] 5.2 [delegate:review] Review updated guidance against the `openspec-apply-delegation` spec scenarios.
- [x] 5.3 [delegate:deepseek] Draft README usage docs for `install_delegant`, Level 1, Level 2, and uninstall/restore behavior.
- [x] 5.4 [codex-only] Run OpenSpec status/instructions validation and confirm the change is apply-ready.
