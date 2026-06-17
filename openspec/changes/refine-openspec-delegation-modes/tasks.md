## 1. Installer Mode Interface

- [x] 1.1 [delegate:test] Add CLI tests for `--mode main`, `--mode hybrid`, and `--mode delegated-apply`.
  - context: `tests/test_cli.py`, `llm_eval/openspec_delegation.py`, `llm_eval/cli.py`
  - output: focused tests that assert installed guidance includes the selected mode text
  - verify: `pytest tests/test_cli.py`
- [x] 1.2 [delegate:test] Add compatibility tests for `--level 1` -> `hybrid` and `--level 2` -> `delegated-apply`.
  - context: `tests/test_cli.py`
  - output: focused tests for legacy level mapping and CLI output
  - verify: `pytest tests/test_cli.py`
- [x] 1.3 [delegate:test] Add conflict and non-interactive tests for `--mode`, `--level`, and `--yes`.
  - context: `tests/test_cli.py`
  - output: tests that reject incompatible mode/level combinations without writing guidance
  - verify: `pytest tests/test_cli.py`
- [x] 1.4 [codex-only] Implement installer mode parsing, interactive A/B/C selection, and backward-compatible `--level` mapping.

## 2. Managed Guidance Content

- [x] 2.1 [delegate:deepseek] Draft managed guidance text for `main` mode.
  - context: `llm_eval/openspec_delegation.py`, `openspec/changes/refine-openspec-delegation-modes/design.md`
  - output: guidance text stating all OpenSpec apply work remains with the main model
- [x] 2.2 [delegate:deepseek] Draft managed guidance text for `hybrid` mode with a main-model/submodel responsibility split.
  - context: `llm_eval/openspec_delegation.py`, `openspec/changes/refine-openspec-delegation-modes/design.md`
  - output: guidance text listing main-model responsibilities and submodel-eligible work
- [x] 2.3 [delegate:deepseek] Draft managed guidance text for `delegated-apply` mode.
  - context: `llm_eval/openspec_delegation.py`, `openspec/changes/refine-openspec-delegation-modes/design.md`
  - output: guidance text describing full apply delegation plus main-model verification
- [x] 2.4 [codex-only] Integrate mode-specific guidance into `build_guidance_block` while preserving managed-block idempotency.

## 3. Propose-Time Task Packets

- [x] 3.1 [delegate:deepseek] Draft propose guidance for splitting delegate-friendly work into standalone tasks.
  - context: `openspec/changes/refine-openspec-delegation-modes/design.md`, `openspec/changes/refine-openspec-delegation-modes/specs/openspec-delegation-modes/spec.md`
  - output: guidance text for task packet fields: `context`, `output`, and `verify`
- [x] 3.2 [codex-only] Add task-packet guidance to the installed project delegation block without breaking OpenSpec checkbox parsing.
- [x] 3.3 [delegate:test] Add tests or assertions that generated guidance contains task-packet field instructions.
  - context: `tests/test_cli.py`, `llm_eval/openspec_delegation.py`
  - output: focused assertions for `context`, `output`, and `verify` task-packet guidance
  - verify: `pytest tests/test_cli.py`

## 4. README

- [x] 4.1 [delegate:deepseek] Draft README updates for `install_delegant --mode main|hybrid|delegated-apply`.
  - context: `README.md`, `openspec/changes/refine-openspec-delegation-modes/design.md`
  - output: README prose and table updates only
- [x] 4.2 [delegate:deepseek] Draft README responsibility table for `hybrid` mode.
  - context: `README.md`, `openspec/changes/refine-openspec-delegation-modes/design.md`
  - output: table listing main-model responsibilities and submodel-eligible work
- [x] 4.3 [codex-only] Integrate README updates and ensure deprecated `--level` is documented only as compatibility behavior.

## 5. Verification

- [x] 5.1 [codex-only] Run focused CLI tests.
- [x] 5.2 [codex-only] Run the non-live test suite used for this repo, excluding real Codex diagnostic tests if they hang.
- [x] 5.3 [delegate:review] Review implementation against `openspec-delegation-modes` spec scenarios.
  - context: `openspec/changes/refine-openspec-delegation-modes/specs/openspec-delegation-modes/spec.md`
  - output: findings or confirmation that scenarios are covered
- [x] 5.4 [codex-only] Run OpenSpec status/apply-instructions validation and confirm the change is ready to archive.
