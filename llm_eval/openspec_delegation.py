from dataclasses import dataclass
from pathlib import Path


MANAGED_BLOCK_START = "<!-- agent-dispatch:openspec-delegation:start -->"
MANAGED_BLOCK_END = "<!-- agent-dispatch:openspec-delegation:end -->"
DEFAULT_GUIDANCE_FILE = "AGENTS.md"


@dataclass(frozen=True)
class DelegationInstallResult:
    path: Path
    level: int | None
    action: str


def install_project_guidance(project_dir: str | Path, level: int) -> DelegationInstallResult:
    if level not in (1, 2):
        raise ValueError("level must be 1 or 2")

    project_path = Path(project_dir).resolve()
    guidance_path = project_path / DEFAULT_GUIDANCE_FILE
    existing = guidance_path.read_text(encoding="utf-8") if guidance_path.exists() else ""
    block = build_guidance_block(level)

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
    return DelegationInstallResult(path=guidance_path, level=level, action=action)


def uninstall_project_guidance(project_dir: str | Path) -> DelegationInstallResult:
    project_path = Path(project_dir).resolve()
    guidance_path = project_path / DEFAULT_GUIDANCE_FILE
    if not guidance_path.exists():
        return DelegationInstallResult(path=guidance_path, level=None, action="not-installed")

    existing = guidance_path.read_text(encoding="utf-8")
    if MANAGED_BLOCK_START not in existing and MANAGED_BLOCK_END not in existing:
        return DelegationInstallResult(path=guidance_path, level=None, action="not-installed")

    updated = _replace_managed_block(existing, "").strip()
    if updated:
        guidance_path.write_text(f"{updated}\n", encoding="utf-8")
    else:
        guidance_path.unlink()
    return DelegationInstallResult(path=guidance_path, level=None, action="removed")


def build_guidance_block(level: int) -> str:
    if level not in (1, 2):
        raise ValueError("level must be 1 or 2")

    level_policy = _level_policy(level)
    return "\n".join(
        [
            MANAGED_BLOCK_START,
            "## OpenSpec Delegation Policy",
            "",
            f"Delegation level: {level}",
            "",
            level_policy,
            "",
            "When working on OpenSpec propose/apply tasks:",
            "- Add lightweight task tags in `tasks.md` when useful:",
            "  `[delegate:deepseek]`, `[delegate:test]`, `[delegate:review]`,",
            "  `[delegate:optional]`, and `[codex-only]`.",
            "- During apply, inspect the current task tag before implementation.",
            "  `[codex-only]` stays in Codex. `[delegate:deepseek]` is eligible for",
            "  implementation drafts. `[delegate:test]` is eligible for test drafts.",
            "  `[delegate:review]` is eligible for review or failure diagnosis.",
            "  `[delegate:optional]` is delegated only when the prompt packet is small.",
            "- Use lower-cost submodels only for bounded, low-risk, verifiable draft work.",
            "- Keep architecture, security, migrations, credentials, destructive operations,",
            "  and OpenSpec state changes in Codex unless the user explicitly says otherwise.",
            "- Build minimal delegation prompt packets: task text, relevant artifact excerpts,",
            "  relevant file excerpts, expected output format, and verification commands.",
            "- Use these output modes for prompt packets: `implementation-draft` returns a",
            "  patch or file-by-file edit plan; `test-draft` returns tests to add and run;",
            "  `review` returns findings against the diff/spec; `diagnosis` returns likely",
            "  root cause and next fix for a failing command.",
            "- Use `agent-dispatch run --target <target> --prompt-file <packet>` for delegated",
            "  draft/review/diagnosis work when a shell delegation backend is needed.",
            "- Submodels must not change OpenSpec scope or mark `tasks.md` checkboxes complete.",
            "- Codex reviews delegated output, integrates changes, runs final verification,",
            "  and is the only actor that marks OpenSpec tasks complete.",
            "- If delegated output is unavailable, malformed, too broad, stale, or inconsistent,",
            "  Codex takes over after one unusable attempt unless the failure is mechanical.",
            "- Record delegation decisions or overrides near the relevant task in `tasks.md`",
            "  when the workflow uses delegated draft work.",
            MANAGED_BLOCK_END,
        ]
    )


def _level_policy(level: int) -> str:
    if level == 1:
        return "\n".join(
            [
                "Level 1: Codex-routed selective delegation.",
                "Codex decides task-by-task whether delegation is cost-effective.",
                "Prefer delegation for tagged low-risk tasks, but skip it when the task is",
                "ambiguous, high-risk, trivial, or requires broad context.",
            ]
        )
    return "\n".join(
        [
            "Level 2: submodel-first implementation.",
            "Prefer submodel drafts for all eligible non-`codex-only` tasks.",
            "Codex still integrates, verifies, and marks tasks complete. Codex may override",
            "Level 2 when a task needs broad context, contains high-risk decisions, or",
            "delegated output is not directly usable.",
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
