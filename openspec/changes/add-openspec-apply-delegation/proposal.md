## Why

Running OpenSpec apply entirely with the most capable Codex configuration spends premium model time on work that is often bounded, low-risk, and directly verifiable. We need an apply workflow that can route suitable implementation and testing draft work to lower-cost submodels while preserving Codex as the owner of scope, integration, verification, and OpenSpec task completion.

## What Changes

- Add a cost-first delegation policy for OpenSpec apply workflows.
- Allow `tasks.md` entries to declare delegation suitability with lightweight tags such as `[delegate:deepseek]`, `[delegate:test]`, `[delegate:review]`, `[delegate:optional]`, and `[codex-only]`.
- Require the apply workflow to classify pending tasks, build minimal delegation prompt packets, and use lower-cost submodels only for bounded, low-risk, verifiable work.
- Require Codex to retain final authority for applying changes, running final verification, and marking OpenSpec tasks complete.
- Add fallback and escalation behavior when the delegated target is unavailable or produces unusable output.
- Add an explicit CLI installer command, `install_delegant`, that installs project-local delegation guidance instead of changing Codex behavior during `pip install`.
- Let the installer offer two delegation levels:
  - Level 1: Codex routes selected tasks to submodels and keeps primary implementation ownership.
  - Level 2: submodels draft or implement all eligible non-`codex-only` tasks, with Codex acting as integrator and verifier.

## Capabilities

### New Capabilities
- `openspec-apply-delegation`: Cost-first task delegation rules for OpenSpec apply workflows.

### Modified Capabilities
- None.

## Impact

- Affected artifacts: OpenSpec skill/rule guidance for propose/apply task generation and execution.
- Affected CLI: `agent-dispatch` gains an explicit project installer command for OpenSpec delegation guidance.
- Affected workflow: `openspec-apply-change` should read delegation tags from `tasks.md` and selectively invoke submodels or `agent-dispatch` for draft work.
- Affected docs/tests: add focused tests or fixtures if the implementation introduces parsing helpers or command wrappers.
- Affected model usage: lower-cost targets may handle selected drafts, while Codex remains responsible for integration and final verification.
