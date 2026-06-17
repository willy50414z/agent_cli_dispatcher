## Why

The first OpenSpec delegation change added a project-local installer and two numeric delegation levels, but the user-facing choice is still too vague for cost control. Users need an explicit interactive choice between main-model execution, hybrid delegation, and full delegated apply, and propose-time task splitting should reduce how much context submodels must read.

## What Changes

- Replace the numeric `--level 1/2` mental model with interactive A/B/C delegation modes:
  - A / `main`: all OpenSpec apply work stays with the main model.
  - B / `hybrid`: the main model plans, integrates, and validates; submodels handle simple token-heavy work such as small implementation drafts, small-scope tests, document reading, extraction, summaries, failure diagnosis, and first-pass review.
  - C / `delegated-apply`: the main model delegates the apply implementation to a submodel, then verifies that tasks, tests, and spec alignment are complete.
- Keep backward-compatible handling for existing `--level` installs where practical, mapping Level 1 to `hybrid` and Level 2 to `delegated-apply`.
- Update propose guidance so tasks intended for submodels are split into standalone, minimal-context task packets.
- Update README to explain the `hybrid` mode responsibility boundary in concrete terms.

## Capabilities

### New Capabilities
- `openspec-delegation-modes`: Interactive OpenSpec delegation mode selection and propose-time task packet splitting.

### Modified Capabilities
- None.

## Impact

- Affected CLI: `agent-dispatch install_delegant` mode selection and install output.
- Affected guidance: generated `AGENTS.md` OpenSpec delegation managed block.
- Affected OpenSpec planning: propose guidance should split delegate-friendly work into standalone tasks with minimal context requirements.
- Affected docs/tests: README and CLI tests for A/B/C modes and backward-compatible level handling.
