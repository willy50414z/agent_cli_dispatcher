## Context

The project already has `agent-dispatch`, a CLI that can run raw model prompts, perform outcome-routed evaluation, check target health, and use ordered target fallback. The OpenSpec apply skill is currently linear: it selects a change, reads status and apply instructions, reads context files, implements pending tasks, updates task checkboxes, and reports status.

The cost problem is that a premium Codex configuration can spend tokens on routine implementation, test draft, and review work that is cheaper to delegate. The quality problem is that delegation must not blur ownership of OpenSpec state: a submodel must not decide that a task is complete, widen scope, or mark `tasks.md`.

## Goals / Non-Goals

**Goals:**
- Add a cost-first delegation policy for OpenSpec apply workflows.
- Add an explicit opt-in CLI installer that applies the policy to the current project.
- Let planning artifacts mark delegation suitability directly in `tasks.md`.
- Prefer lower-cost submodels for bounded, low-risk, verifiable draft work.
- Keep Codex responsible for routing, integration, final verification, and OpenSpec task completion.
- Provide fallback and escalation behavior when delegation is unavailable or produces unusable output.
- Keep prompt packets small enough that delegation can actually save money.

**Non-Goals:**
- Replace Codex as the OpenSpec apply owner.
- Require every task to be delegated.
- Add a background job system, queue, or persistent worker daemon.
- Change the existing `agent-dispatch run`, `evaluate`, or `health` CLI contracts.
- Install Codex behavior changes during `pip install`.
- Let submodels directly mark `tasks.md` complete.

## Decisions

### Use task-level delegation tags

`tasks.md` is the right place to record delegation suitability because it is already the apply loop's unit of work. The proposal uses lightweight inline tags:

```md
- [ ] 2.1 [delegate:deepseek] Add parser tests for `--foo`
- [ ] 2.2 [delegate:test] Add regression tests for status resolution
- [ ] 2.3 [delegate:review] Review the final diff against the spec
- [ ] 2.4 [delegate:optional] Update README examples
- [ ] 2.5 [codex-only] Decide architecture and permission boundaries
```

Alternatives considered:
- Separate YAML metadata file: more structured, but adds synchronization risk with `tasks.md`.
- No tags, classify at apply time only: simpler artifact format, but costs more premium-model reasoning during apply and makes delegation less predictable.

### Install delegation with an explicit project command

The Python package installation should only install package code and console scripts. Delegation policy changes should be explicit because they alter how Codex spends model budget and how OpenSpec apply work is routed.

Add an installer command exposed by `agent-dispatch`, with `install_delegant` as the single user-facing command name. No alias is provided; a second command with identical behavior adds maintenance surface without value.

The command should install project-local guidance by default rather than editing global Codex skills. A project-local install may write or update a managed block in a repo instruction file such as `AGENTS.md` or an equivalent Codex project rule surface.

The command should be idempotent:
- detect an existing managed block,
- update it in place,
- avoid duplicating guidance,
- report the installed level and target file.

Alternatives considered:
- Install during `pip install`: surprising and too broad, because dependency installation would change agent behavior.
- Patch global skill files by default: powerful, but applies across projects and is harder to review.
- Only document manual setup: safest, but loses the main usability benefit.

### Offer two delegation levels

The installer should let the user choose one of two project-local levels:

**Level 1: Codex-routed selective delegation**
- Codex decides whether each task is worth delegating.
- Delegation is preferred for tagged low-risk tasks and skipped when the context packet is too large.
- This is the recommended default because it optimizes cost without heavily changing ownership.

**Level 2: submodel-first implementation**
- Submodels draft or implement all eligible non-`codex-only` work.
- Codex still integrates, verifies, and marks tasks complete.
- This is more aggressive and may reduce premium-model implementation time, but increases integration risk and submodel context cost.

### Codex remains the router and verifier

The apply workflow may use submodels for draft work, but Codex keeps authority over:
- whether to delegate a task,
- which target to use,
- whether output is usable,
- how to integrate changes,
- which tests are sufficient,
- when to mark the OpenSpec task complete.

Alternatives considered:
- Let the submodel own a full task end-to-end: cheaper in the short term, but creates self-certification risk and makes task completion less trustworthy.

### Delegation prompt packets must be minimal

Delegation only saves cost when the submodel receives a focused packet:
- the specific task text,
- relevant spec/design/proposal excerpts,
- relevant file paths or small file excerpts,
- allowed output format,
- explicit prohibitions against scope changes and task checkbox updates,
- requested verification commands when known.

The apply workflow should skip delegation if the packet would need broad repo context comparable to Codex doing the work directly.

### Prefer draft and review modes over unsupervised mutation

Initial implementation should prefer submodel outputs that Codex can inspect:
- patch suggestions,
- file-by-file edit plans,
- test draft suggestions,
- failure diagnosis,
- diff review findings.

Direct submodel mutation should only be allowed in an isolated workspace or worktree with explicit review before merge.

### Escalate after one unusable delegated attempt

If a delegated attempt is unavailable, malformed, too broad, inconsistent with the repo, or fails verification, Codex should take over rather than repeatedly spending tokens on retries. A single targeted follow-up is acceptable only when the error is mechanical and the fix is obvious.

## Risks / Trade-offs

- Delegation overhead can exceed savings -> Skip delegation when the required context packet is too large or the task is trivial.
- Submodel output can be plausible but wrong -> Require Codex review, final tests, and no submodel task completion authority.
- Tags can become stale -> Allow Codex to override tags when implementation context changes and record the override.
- Parallel writers can conflict -> Prefer patch suggestions or isolated workspaces; define disjoint write scopes before direct delegated edits.
- Lower-cost models may miss architecture constraints -> Keep architecture, security, migration, and OpenSpec state tasks as `codex-only`.
- Level 2 can spend more total tokens if every task needs large context -> Require prompt packet size checks and Codex override authority.
- Project-local install may not affect globally installed OpenSpec skills outside this repo -> Make the installer output explicit about scope.

## Migration Plan

1. Add the `agent-dispatch install_delegant` project installer command.
2. Make the installer write an idempotent managed project guidance block with the selected level.
3. Update task-generation guidance so new `tasks.md` files may include delegation tags.
4. Update apply guidance to parse tags, classify tasks, and selectively delegate.
5. Add focused tests or fixtures for installer behavior, tag parsing, and routing if implemented as code.
6. Keep existing untagged tasks valid; untagged means Codex decides locally using the cost-first policy.

Rollback is to run the installer uninstall mode or remove the managed project guidance block. Existing OpenSpec changes remain readable because tags are inline task text.

### Use `agent-dispatch` as the delegation execution surface

The apply skill instructs Codex to call `agent-dispatch run --target <target> --prompt-file <packet>` to execute a delegated task. This reuses existing target routing, health-check, and fallback logic without duplicating it in the apply guidance. Native subagent invocation is deferred until `agent-dispatch` proves insufficient.

### Delegation audit notes go into `tasks.md`

`tasks.md` is written and maintained by the main agent. Sub-agents are only mentioned within it via delegation tags; they do not write to it. Because the main agent already owns the file, appending delegation audit notes to `tasks.md` after each delegated task keeps all task-state information in one place without requiring a separate artifact.

### Defer direct submodel mutation

The first implementation supports draft and review modes only: patch suggestions, edit plans, test drafts, and diagnosis findings. Direct submodel mutation of repo files is deferred until an isolated worktree workflow exists. This aligns with the "Prefer draft and review modes over unsupervised mutation" decision above.
