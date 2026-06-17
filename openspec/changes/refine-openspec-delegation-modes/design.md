## Context

The previous `add-openspec-apply-delegation` change introduced `agent-dispatch install_delegant`, project-local guidance in `AGENTS.md`, and numeric levels 1 and 2. The current behavior is directionally useful but still too abstract:

- Level 1 roughly means hybrid delegation, but the main-model and submodel responsibilities are not explicit enough and the guidance lets Codex skip delegation too easily.
- Level 2 means submodel-first drafts, but the user now wants a stronger mode where apply implementation is delegated and the main model verifies task completion.
- There is no explicit "main model only" mode for users who want the installer to document that delegation is disabled.
- Propose-time task splitting currently relies on tags, but not on standalone task packets that let submodels avoid reading all OpenSpec artifacts.

## Goals / Non-Goals

**Goals:**
- Replace the primary user-facing installer choice with A/B/C delegation modes.
- Make mode B (`hybrid`) the recommended default and document its delegation-first responsibility boundary clearly.
- Define mode C (`delegated-apply`) as full delegated apply implementation with main-model verification.
- Keep backward-compatible `--level` support where practical.
- Update propose guidance so delegate-friendly work is split into standalone tasks with minimal context fields.
- Update README to explain mode B's responsibilities concretely.

**Non-Goals:**
- Remove existing `install_delegant` command name.
- Let submodels mark OpenSpec tasks complete without main-model verification.
- Add a daemon, queue, or persistent worker service.
- Force delegation for OpenSpec changes that have no delegate-friendly implementation, test, review, documentation, repetitive edit, or diagnosis work.
- Implement direct multi-worktree merge automation in this refinement.

## Decisions

### Use named modes as the primary interface

The installer should support:

```bash
agent-dispatch install_delegant
agent-dispatch install_delegant --mode main
agent-dispatch install_delegant --mode hybrid
agent-dispatch install_delegant --mode delegated-apply
```

When `--mode` is omitted in an interactive terminal, the command should ask the user to choose:

- A. `main`: all apply work remains with the main model.
- B. `hybrid`: propose-time task routing plus delegation-first apply for tagged work; main model integrates and validates.
- C. `delegated-apply`: main model delegates the apply implementation to a submodel and verifies completion.

Alternative considered: keep `--level 1/2` and expand docs. That preserves compatibility, but the numeric model hides the real behavior and does not include the no-delegation option.

### Preserve `--level` as compatibility input

Existing users may already have scripts using `--level`. Keep it as a deprecated compatibility input:

- `--level 1` maps to `--mode hybrid`.
- `--level 2` maps to `--mode delegated-apply`.

The CLI should reject conflicting `--mode` and `--level` combinations. README should show `--mode`, not `--level`, as the main path.

### Define mode B as the delegation-first cost-control default

Mode B is the main cost-saving mode. It should be specific enough that Codex cannot silently decide to do tagged delegated work itself just because the task looks small. Propose creates the routing plan; apply follows that plan unless a concrete exception applies.

Main model owns:
- OpenSpec artifact interpretation, scope, and architecture decisions.
- High-risk exception decisions.
- Architecture, security, data migration, destructive operations, and credentials.
- Integration of delegated output.
- Large feature acceptance and final tests.
- `tasks.md` checkbox updates.

Submodels are assigned:
- Implementation drafts with clear file scope.
- Small-scope tests and test suggestions.
- Documentation reading, extraction, and summaries.
- Repetitive edits.
- Failure diagnosis.
- First-pass diff/spec review.

Hybrid apply behavior:

- During propose, delegate-friendly implementation, test, review, documentation extraction, repetitive edit, and diagnosis work must become standalone delegate task packets.
- During apply, tagged `[delegate:deepseek]`, `[delegate:test]`, and `[delegate:review]` tasks require one delegated attempt before direct main-model implementation.
- DeepSeek is the default shell delegation target via `agent-dispatch run --target deepseek --prompt-file <packet>` unless the task packet names another target.
- Codex may skip or take over only when the task is high-risk, needs broad repo context, the delegation backend is unavailable, or delegated output is unusable after one attempt.
- "It is faster for Codex" is not a valid skip reason for a tagged delegate task.
- Codex records the concrete skip or takeover reason near the relevant task in `tasks.md`.

### Define mode C as delegated apply with main-model verification

Mode C is deliberately more aggressive:

- The main model packages the apply request and delegates implementation to a submodel.
- The submodel may produce a patch or implementation report for the full eligible apply scope.
- The main model verifies that tasks, tests, and spec alignment are complete before marking tasks complete.
- The main model must take over if delegated output is incomplete, unsafe, too broad, or unverifiable.

Mode C is not the recommended default because the submodel may need broad context, which can reduce cost savings and increase integration risk.

### Split delegate-friendly work during propose

The propose workflow should create standalone tasks for delegate-friendly work instead of only tagging broad tasks. A good delegated task should include enough routing context that a submodel does not need to read the full proposal/design/spec bundle.

Recommended task shape:

```md
- [ ] 2.2 [delegate:test] Add CLI tests for `--mode hybrid`
  - context: `tests/test_cli.py`, `llm_eval/openspec_delegation.py`
  - output: focused tests for install/update behavior
  - verify: `pytest tests/test_cli.py`
```

Tasks can remain simple one-line checkboxes when they are `codex-only` or genuinely do not create useful delegated work. A task should not stay with Codex merely because Codex could do it quickly.

## Risks / Trade-offs

- Three modes can be harder to explain than two levels -> Use A/B/C labels in interactive prompts and named modes in scripts.
- Mode C can increase total token usage -> Document it as aggressive and require main-model verification.
- Multi-line task packet fields may stress simple task parsers -> Keep the checkbox line unchanged and put packet fields under it as indented notes.
- Backward-compatible `--level` can create two ways to do the same thing -> Mark it as compatibility-only in docs and tests.
- Propose-time task splitting can over-fragment plans -> Apply it to delegate-friendly implementation, test, review, documentation, repetitive edit, and diagnosis work, while keeping architecture, scope, security, migration, destructive, and broad-context work in Codex.

## Migration Plan

1. Add mode parsing and interactive A/B/C selection to `install_delegant`.
2. Map existing `--level` values to modes for compatibility.
3. Update managed guidance generation to use mode names and mode-specific responsibility text.
4. Update README to document `--mode` and mode B's responsibility split.
5. Update tests to cover A/B/C modes, compatibility level mapping, conflict handling, and task packet guidance text.
6. Keep existing installed managed blocks updateable in place.

## Open Questions

- Should non-interactive `--yes` continue to default to `hybrid`, or should it require an explicit `--mode` for all new installs?
- Should mode C initially use patch/report output only, or allow direct submodel edits in a future isolated worktree implementation?
