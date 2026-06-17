from dataclasses import dataclass
from pathlib import Path


MANAGED_BLOCK_START = "<!-- agent-dispatch:openspec-delegation:start -->"
MANAGED_BLOCK_END = "<!-- agent-dispatch:openspec-delegation:end -->"
DEFAULT_GUIDANCE_FILE = "AGENTS.md"

VALID_MODES = ("main", "hybrid", "delegated-apply")


@dataclass(frozen=True)
class DelegationInstallResult:
    path: Path
    mode: str | None
    action: str


def install_project_guidance(project_dir: str | Path, mode: str) -> DelegationInstallResult:
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {', '.join(VALID_MODES)}")

    project_path = Path(project_dir).resolve()
    guidance_path = project_path / DEFAULT_GUIDANCE_FILE
    existing = guidance_path.read_text(encoding="utf-8") if guidance_path.exists() else ""
    block = build_guidance_block(mode)

    if MANAGED_BLOCK_START in existing or MANAGED_BLOCK_END in existing:
        updated = _replace_managed_block(existing, block)
        action = "updated"
    else:
        prefix = existing.rstrip()
        if prefix:
            updated = f"{prefix}\n\n{block}\n"
            action = "appended"
        else:
            updated = f"# Agent Guidance\n\n{block}\n"
            action = "created"

    guidance_path.write_text(updated, encoding="utf-8")
    return DelegationInstallResult(path=guidance_path, mode=mode, action=action)


def uninstall_project_guidance(project_dir: str | Path) -> DelegationInstallResult:
    project_path = Path(project_dir).resolve()
    guidance_path = project_path / DEFAULT_GUIDANCE_FILE
    if not guidance_path.exists():
        return DelegationInstallResult(path=guidance_path, mode=None, action="not-installed")

    existing = guidance_path.read_text(encoding="utf-8")
    if MANAGED_BLOCK_START not in existing and MANAGED_BLOCK_END not in existing:
        return DelegationInstallResult(path=guidance_path, mode=None, action="not-installed")

    updated = _replace_managed_block(existing, "").strip()
    if updated:
        guidance_path.write_text(f"{updated}\n", encoding="utf-8")
    else:
        guidance_path.unlink()
    return DelegationInstallResult(path=guidance_path, mode=None, action="removed")


def build_guidance_block(mode: str) -> str:
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {', '.join(VALID_MODES)}")

    mode_header = _mode_header(mode)
    mode_policy = _mode_policy(mode)
    return "\n".join(
        [
            MANAGED_BLOCK_START,
            "## OpenSpec Delegation Policy",
            "",
            mode_header,
            "",
            mode_policy,
            "",
            "When working on OpenSpec propose/apply tasks under a delegation-enabled mode:",
            "- During propose, use lightweight task tags in `tasks.md`:",
            "  `[delegate:deepseek]`, `[delegate:test]`, `[delegate:review]`,",
            "  `[delegate:optional]`, and `[codex-only]`.",
            "- During apply, inspect the current task tag before implementation.",
            "  `[codex-only]` stays in Codex. `[delegate:deepseek]` routes to",
            "  implementation drafts. `[delegate:test]` routes to test drafts.",
            "  `[delegate:review]` routes to review or failure diagnosis.",
            "  `[delegate:optional]` is delegated when the prompt packet is small.",
            "- Use lower-cost submodels only for bounded, low-risk, verifiable draft work.",
            "- Keep architecture, security, migrations, credentials, destructive operations,",
            "  and OpenSpec state changes in Codex unless the user explicitly says otherwise.",
            "- Build minimal delegation prompt packets: task text, relevant artifact excerpts,",
            "  relevant file excerpts, expected output format, and verification commands.",
            "- Use these output modes for prompt packets: `implementation-draft` returns a",
            "  patch or file-by-file edit plan; `test-draft` returns tests to add and run;",
            "  `review` returns findings against the diff/spec; `diagnosis` returns likely",
            "  root cause and next fix for a failing command.",
            "- Use `agent-dispatch run --target deepseek --prompt-file <packet>` for delegated",
            "  draft/review/diagnosis work unless a task packet names another target or",
            "  DeepSeek is unavailable.",
            "- Submodels must not change OpenSpec scope or mark `tasks.md` checkboxes complete.",
            "- Codex reviews delegated output, integrates changes, runs final verification,",
            "  and is the only actor that marks OpenSpec tasks complete.",
            "- If delegated output is unavailable, malformed, too broad, stale, or inconsistent,",
            "  Codex takes over after one unusable attempt unless the failure is mechanical.",
            "- Record delegation decisions or overrides near the relevant task in `tasks.md`",
            "  when the workflow uses delegated draft work.",
            "",
            "Propose-time task packets for submodel delegation:",
            "- Split delegate-friendly work into standalone tasks with enough local context",
            "  that a submodel can avoid reading all OpenSpec artifacts.",
            "- Use multi-line task entries for submodel-eligible work:",
            "  ```md",
            "  - [ ] 2.2 [delegate:test] Add CLI tests for `--mode hybrid`",
            "    - context: `tests/test_cli.py`, `llm_eval/openspec_delegation.py`",
            "    - output: focused tests for install/update behavior",
            "    - verify: `pytest tests/test_cli.py`",
            "  ```",
            "- The `context` field lists the minimal files or artifacts the submodel must read.",
            "- The `output` field describes what the submodel should produce.",
            "- The `verify` field gives the command or check that confirms the output is usable.",
            "- Keep the checkbox line in the standard `- [ ]` format so OpenSpec task parsing",
            "  remains intact. Put packet fields as indented notes under the checkbox.",
            "- Use multi-line packets only when they reduce submodel context load. Simple",
            "  `[codex-only]` or trivial tasks can remain one-line checkboxes.",
            MANAGED_BLOCK_END,
        ]
    )


def _mode_header(mode: str) -> str:
    if mode == "main":
        return "Delegation mode: main - no automatic submodel delegation."
    elif mode == "hybrid":
        return "Delegation mode: hybrid - propose-time task routing plus delegation-first apply for tagged work."
    return "Delegation mode: delegated-apply - main model delegates apply implementation to a submodel and verifies completion."


def _mode_policy(mode: str) -> str:
    if mode == "main":
        return "\n".join(
            [
                "Mode A / main: all OpenSpec apply work remains with the main model.",
                "Do not delegate any apply tasks to submodels unless the user explicitly",
                "asks for it on a specific task. This mode keeps all context in the main",
                "session and disables automatic delegation.",
            ]
        )
    elif mode == "hybrid":
        return "\n".join(
            [
                "Mode B / hybrid: the recommended delegation-first cost-control default.",
                "",
                "Main model owns:",
                "- OpenSpec artifact interpretation, scope, and architecture decisions.",
                "- Architecture, security, data migration, destructive operations,",
                "  credentials, and other high-risk decisions.",
                "- Integration of delegated output into the working tree.",
                "- Large feature acceptance and final tests.",
                "- `tasks.md` checkbox updates and OpenSpec state changes.",
                "",
                "Hybrid mandatory delegation rules:",
                "- This managed block supersedes older guidance that says delegation is only",
                "  cost-effective, preferred, advisable, or task-by-task optional.",
                "- In hybrid mode, `[delegate:deepseek]`, `[delegate:test]`, and",
                "  `[delegate:review]` mean mandatory delegation-attempt tags, not",
                "  eligibility hints.",
                "- During OpenSpec propose, Codex MUST call DeepSeek via",
                "  `agent-dispatch run --target deepseek --prompt-file <packet>` before",
                "  finalizing `proposal.md`, `design.md`, or `tasks.md` when the change",
                "  contains delegate-friendly implementation, test, review, documentation",
                "  extraction, repetitive edit, or diagnosis work.",
                "- The propose-time DeepSeek packet MUST ask for standalone delegate task",
                "  packets with `context`, `output`, and `verify` fields, not just ask",
                "  whether delegation is advisable.",
                "- Codex may skip the propose-time DeepSeek call only when the change has no",
                "  delegate-friendly work, the delegation backend is unavailable, or the",
                "  work is high-risk/broad-context; record the concrete reason in the",
                "  OpenSpec artifacts or final response.",
                "- During OpenSpec propose, Codex MUST assign delegate-friendly implementation,",
                "  test, review, documentation extraction, repetitive edit, and diagnosis work",
                "  to standalone delegate task packets informed by the DeepSeek response.",
                "- Delegate-friendly means bounded file scope, clear expected output, and an",
                "  independently verifiable command or review check.",
                "- During apply, Codex MUST attempt delegation for every `[delegate:deepseek]`,",
                "  `[delegate:test]`, and `[delegate:review]` task before implementing it directly.",
                "- A valid apply-time delegation attempt means Codex actually invokes",
                "  `agent-dispatch run --target deepseek --prompt-file <packet>` or records",
                "  a mechanical/backend failure from that command.",
                "- Do not skip a tagged delegate task merely because it is small, trivial, or",
                "  faster for Codex to do directly. Do not reinterpret tagged delegate tasks",
                "  as optional based on cost-effectiveness.",
                "- Codex may skip or take over only when the task is high-risk, needs broad repo",
                "  context, the delegation backend is unavailable, or one delegated attempt",
                "  returns unusable output.",
                "- Record the concrete skip/takeover reason near the relevant task in `tasks.md`.",
                "",
                "Submodels are assigned:",
                "- Implementation drafts with clear file scope.",
                "- Small-scope tests and test suggestions.",
                "- Documentation reading, extraction, and summaries.",
                "- Repetitive edits.",
                "- Failure diagnosis.",
                "- First-pass diff/spec review.",
            ]
        )
    return "\n".join(
        [
            "Mode C / delegated-apply: full delegated apply with main-model verification.",
            "",
            "The main model packages the apply request and delegates implementation to",
            "a submodel. The submodel may produce a patch or implementation report for",
            "the full eligible apply scope.",
            "",
            "The main model must:",
            "- Verify that tasks, tests, and spec alignment are complete before marking",
            "  tasks complete.",
            "- Take over if delegated output is incomplete, unsafe, too broad, or",
            "  unverifiable.",
            "- Not let submodels mark `tasks.md` checkboxes complete.",
            "",
            "Mode C is aggressive and may increase total token usage. Only use it for",
            "changes whose apply scope is well-defined, low-risk, and independently",
            "verifiable by the main model.",
        ]
    )


def _replace_managed_block(text: str, replacement: str) -> str:
    start = text.find(MANAGED_BLOCK_START)
    end = text.find(MANAGED_BLOCK_END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("managed OpenSpec delegation block is malformed")

    end += len(MANAGED_BLOCK_END)
    prefix = text[:start].rstrip()
    suffix = text[end:].lstrip()
    parts = [part for part in (prefix, replacement.strip(), suffix) if part]
    return "\n\n".join(parts) + ("\n" if parts else "")
