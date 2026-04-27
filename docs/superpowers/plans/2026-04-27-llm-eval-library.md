# llm_eval Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing FastAPI service with a pure Python library (`llm_eval`) that runs a structured LLM task, routes to typed outcome callbacks based on which status file the LLM creates, and cleans up its workspace.

**Architecture:** `evaluate()` is the single public entry point — it builds a prompt, runs the LLM CLI in an isolated workspace directory, scans for a `status_<name>` file, validates declared output files exist, then calls the matching `Outcome.callback` with a `JobResult`. No threads, no queue, no persistence.

**Tech Stack:** Python 3.11+, stdlib only (`dataclasses`, `pathlib`, `subprocess`, `shutil`, `uuid`, `time`, `logging`). `pytest` for tests.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `llm_eval/__init__.py` | Create | `evaluate()` function; re-exports `Outcome`, `JobResult` |
| `llm_eval/job.py` | Create | `Outcome` and `JobResult` dataclasses |
| `llm_eval/prompt_builder.py` | Create | Builds full LLM prompt from purpose + outcomes |
| `llm_eval/workspace.py` | Create | Creates and removes per-call workspace directory |
| `llm_eval/status_resolver.py` | Create | Scans workspace for status file; validates output files; builds `JobResult` |
| `llm_eval/llm_target.py` | Create | `LLMTarget` enum (moved from `llm_agent/`) |
| `llm_eval/llm_svc.py` | Create | `run_once()` (moved from `llm_agent/`, import fixed, dead code removed) |
| `tests/__init__.py` | Create | Empty — marks tests as package |
| `tests/test_job.py` | Create | Unit tests for dataclasses |
| `tests/test_prompt_builder.py` | Create | Unit tests for prompt construction |
| `tests/test_workspace.py` | Create | Unit tests for workspace creation/cleanup |
| `tests/test_status_resolver.py` | Create | Unit tests for status file scanning and validation |
| `tests/test_evaluate.py` | Create | Integration tests for `evaluate()` with mocked `run_once` |
| `pyproject.toml` | Create | Minimal packaging metadata |
| `main.py` | Delete | FastAPI service — removed |
| `requirements.txt` | Delete | No Python package deps for the library |
| `Dockerfile` | Delete | No longer a container service |
| `llm_agent/` | Delete | Entire directory — moved into `llm_eval/` |

---

### Task 1: Dataclasses (`job.py`)

**Files:**
- Create: `llm_eval/__init__.py` (empty placeholder)
- Create: `llm_eval/job.py`
- Create: `tests/__init__.py`
- Create: `tests/test_job.py`

- [ ] **Step 1: Install pytest if not present**

```bash
pip install pytest
```

- [ ] **Step 2: Create package skeleton**

Create `llm_eval/__init__.py` (empty for now):
```python
```

Create `tests/__init__.py` (empty):
```python
```

- [ ] **Step 3: Write failing tests for `job.py`**

Create `tests/test_job.py`:
```python
from llm_eval.job import Outcome, JobResult


def test_outcome_stores_fields():
    called = []
    cb = lambda r: called.append(r)
    o = Outcome(
        status="complete",
        description="All good",
        output_files=["notes.txt"],
        callback=cb,
    )
    assert o.status == "complete"
    assert o.description == "All good"
    assert o.output_files == ["notes.txt"]
    assert o.callback is cb


def test_outcome_default_output_files_is_empty():
    o = Outcome(status="ok", description="fine", output_files=[], callback=lambda r: None)
    assert o.output_files == []


def test_job_result_stores_all_fields():
    r = JobResult(
        job_id="abc123",
        status="complete",
        target="claude",
        duration_seconds=3.5,
        files={"notes.txt": "hello"},
        stdout="raw output",
    )
    assert r.job_id == "abc123"
    assert r.status == "complete"
    assert r.target == "claude"
    assert r.duration_seconds == 3.5
    assert r.files == {"notes.txt": "hello"}
    assert r.stdout == "raw output"
```

- [ ] **Step 4: Run tests to confirm they fail**

```bash
python -m pytest tests/test_job.py -v
```

Expected: `ModuleNotFoundError: No module named 'llm_eval.job'`

- [ ] **Step 5: Create `llm_eval/job.py`**

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class Outcome:
    status: str
    description: str
    output_files: list[str]
    callback: Callable[["JobResult"], None]


@dataclass
class JobResult:
    job_id: str
    status: str
    target: str
    duration_seconds: float
    files: dict[str, str]
    stdout: str
```

- [ ] **Step 6: Run tests to confirm they pass**

```bash
python -m pytest tests/test_job.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add llm_eval/__init__.py llm_eval/job.py tests/__init__.py tests/test_job.py
git commit -m "feat: add Outcome and JobResult dataclasses"
```

---

### Task 2: LLMTarget enum (`llm_target.py`)

**Files:**
- Create: `llm_eval/llm_target.py`
- Create: `tests/test_llm_target.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_llm_target.py`:
```python
import pytest
from llm_eval.llm_target import LLMTarget


def test_all_targets_accessible():
    assert LLMTarget.CLAUDE.value == "claude"
    assert LLMTarget.GEMINI.value == "gemini"
    assert LLMTarget.CODEX.value == "codex"
    assert LLMTarget.OPENCODE.value == "opencode"
    assert LLMTarget.COPILOT.value == "copilot"


def test_lookup_by_string():
    assert LLMTarget("claude") == LLMTarget.CLAUDE


def test_invalid_string_raises():
    with pytest.raises(ValueError):
        LLMTarget("unknown")
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_llm_target.py -v
```

Expected: `ModuleNotFoundError: No module named 'llm_eval.llm_target'`

- [ ] **Step 3: Create `llm_eval/llm_target.py`**

```python
from enum import Enum


class LLMTarget(Enum):
    CLAUDE   = "claude"
    GEMINI   = "gemini"
    CODEX    = "codex"
    OPENCODE = "opencode"
    COPILOT  = "copilot"
```

- [ ] **Step 4: Run to confirm passing**

```bash
python -m pytest tests/test_llm_target.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add llm_eval/llm_target.py tests/test_llm_target.py
git commit -m "feat: add LLMTarget enum (moved from llm_agent)"
```

---

### Task 3: Move and clean `llm_svc.py`

**Files:**
- Create: `llm_eval/llm_svc.py` (from `llm_agent/llm_svc.py` with fixes)

No unit tests for `run_once()` itself — it shells out to real CLI tools. Integration testing is done in Task 7 via mocking.

- [ ] **Step 1: Create `llm_eval/llm_svc.py`**

Copy `llm_agent/llm_svc.py` content with these changes:
1. Fix import: `from llm_eval.llm_target import LLMTarget`
2. Remove `_REPO_ROOT` constant and its usage in the CODEX branch (CODEX now uses the workspace `cwd` like all other targets)
3. Remove `_get_codex_workspace()` and `_ensure_codex_trusted()` (dead code — only called from deleted `main.py`)

Full `llm_eval/llm_svc.py`:

```python
import json
import logging
import os
import re
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from llm_eval.llm_target import LLMTarget

logger = logging.getLogger(__name__)

_QUOTA_ERROR_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"exceeded your monthly token limit",
        r"exceeded your current quota",
        r"insufficient.quota",
        r"quota.exceeded",
        r"billing hard limit",
        r"credit balance is too low",
        r"out of credits",
        r"rate.limit.exceeded",
        r"429",
        r"payment required",
    ]
]

_QUOTA_RETRY_INTERVAL_SECONDS: int = int(os.getenv("LLM_QUOTA_RETRY_INTERVAL", "300"))
_QUOTA_MAX_RETRIES: int = int(os.getenv("LLM_QUOTA_MAX_RETRIES", "288"))

_ALLOW_ALL_OPENCODE_PERMISSION = {
    "bash": "allow", "read": "allow", "edit": "allow", "task": "allow",
    "glob": "allow", "grep": "allow", "list": "allow",
    "external_directory": "allow", "todowrite": "allow", "todoread": "allow",
    "question": "allow", "webfetch": "allow", "websearch": "allow",
    "codesearch": "allow", "lsp": "allow", "doom_loop": "allow", "skill": "allow",
}


def _is_quota_error(text: str) -> bool:
    for pattern in _QUOTA_ERROR_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _resolve_cli(command_name: str) -> str:
    if os.name == "nt":
        cmd_candidate = shutil.which(f"{command_name}.cmd")
        if cmd_candidate:
            return cmd_candidate
    resolved = shutil.which(command_name)
    return resolved if resolved else command_name


def run_once(
    target: LLMTarget,
    prompt: str,
    *,
    model: str | None = None,
    cwd: str | None = None,
    timeout: float | None = 1800,
    encoding: str = "utf-8",
    quota_retry_interval: int | None = None,
    quota_max_retries: int | None = None,
) -> str:
    if not prompt.strip():
        raise ValueError("prompt must not be empty.")

    _retry_interval = quota_retry_interval if quota_retry_interval is not None else _QUOTA_RETRY_INTERVAL_SECONDS
    _max_retries    = quota_max_retries    if quota_max_retries    is not None else _QUOTA_MAX_RETRIES

    work_dir = str(Path(cwd).resolve()) if cwd else None
    effective_dir = work_dir or str(Path.cwd())

    run_id = uuid.uuid4().hex[:8]
    io_dir = Path(effective_dir) / ".llm_io"
    io_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = io_dir / f"prompt_{run_id}.txt"
    output_file = io_dir / f"output_{run_id}.txt"
    prompt_file.write_text(prompt, encoding=encoding)

    stdin_input: str | None = None
    env = dict(os.environ)

    try:
        if target == LLMTarget.CLAUDE:
            command = [_resolve_cli("claude"), "--print", "--dangerously-skip-permissions"]
            if model:
                command.extend(["--model", model])
            stdin_input = prompt_file.read_text(encoding=encoding)

        elif target == LLMTarget.GEMINI:
            command = [_resolve_cli("gemini"), "--approval-mode", "auto_edit",
                       "--prompt", prompt_file.read_text(encoding=encoding)]

        elif target == LLMTarget.CODEX:
            command = [_resolve_cli("codex"), "exec", "--dangerously-bypass-approvals-and-sandbox",
                       prompt_file.read_text(encoding=encoding).strip().replace("\n", " ")]

        elif target == LLMTarget.OPENCODE:
            env.setdefault("OPENCODE_PERMISSION", json.dumps(_ALLOW_ALL_OPENCODE_PERMISSION))
            runtime_root = Path(effective_dir).resolve() / "data" / "tool-runtime" / "opencode"
            for subdir in ("config", "data", "state"):
                (runtime_root / subdir).mkdir(parents=True, exist_ok=True)
            env.setdefault("XDG_CONFIG_HOME", str(runtime_root / "config"))
            env.setdefault("XDG_DATA_HOME",   str(runtime_root / "data"))
            env.setdefault("XDG_STATE_HOME",  str(runtime_root / "state"))
            command = [_resolve_cli("opencode"), "run",
                       "--dir", effective_dir, "--format", "json", "-"]
            stdin_input = prompt_file.read_text(encoding=encoding)

        elif target == LLMTarget.COPILOT:
            command = [_resolve_cli("copilot"), "-p", prompt_file.read_text(encoding=encoding),
                       "--allow-all", "--no-ask-user", "--output-format", "text", "--silent",
                       "--add-dir", effective_dir]
            if model:
                command.extend(["--model", model])

        else:
            raise ValueError(f"Unsupported LLM target: {target}")

        logger.info("run_once [%s] cwd=%s", target.value, work_dir or "(inherit)")
        logger.debug("run_once [%s] prompt_file=%s\n%s", target.value, prompt_file, prompt)

        completed = None
        for quota_attempt in range(_max_retries + 1):
            try:
                completed = subprocess.run(
                    command,
                    input=stdin_input,
                    capture_output=True,
                    text=True,
                    encoding=encoding,
                    cwd=work_dir,
                    env=env,
                    timeout=timeout,
                )
            except Exception as e:
                logger.error("execute cmd exception: %s", e)
                raise

            if completed.returncode != 0:
                stderr = (completed.stderr or "").strip()
                stdout = (completed.stdout or "").strip()
                parts = [s for s in [stderr, stdout] if s]
                detail = "\n".join(parts) if parts else "(no output)"

                if _is_quota_error(detail):
                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    logger.warning(
                        "[QUOTA EXHAUSTED] %s | attempt=%d/%d | Retrying in %ds. Detail: %s",
                        target.value, quota_attempt + 1, _max_retries, _retry_interval, detail[:300],
                    )
                    if quota_attempt < _max_retries:
                        time.sleep(_retry_interval)
                        continue
                    raise RuntimeError(
                        f"{target.value} quota exhausted after {_max_retries} retries. "
                        f"Last error: {detail[:300]}"
                    )

                raise RuntimeError(
                    f"{target.value} CLI failed (exit {completed.returncode}): {detail[:500]}"
                )

            break

        raw_stdout = (completed.stdout or "").strip()

        if target == LLMTarget.OPENCODE and raw_stdout:
            try:
                chunks = []
                for line in raw_stdout.splitlines():
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if event.get("type") == "error":
                        msg = (event.get("error") or {}).get("data", {}).get("message", "")
                        raise RuntimeError(str(msg))
                    message = event.get("message")
                    if isinstance(message, dict):
                        for item in (message.get("content") or []):
                            if isinstance(item, dict) and item.get("type") == "text":
                                chunks.append(str(item["text"]))
                if chunks:
                    raw_stdout = "\n".join(chunks).strip()
            except json.JSONDecodeError:
                pass

        logger.info("run_once [%s] done. stdout_len=%d", target.value, len(raw_stdout))
        output_file.write_text(raw_stdout, encoding=encoding)
        return output_file.read_text(encoding=encoding)

    finally:
        prompt_file.unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)
```

- [ ] **Step 2: Verify import works**

```bash
python -c "from llm_eval.llm_svc import run_once; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add llm_eval/llm_svc.py
git commit -m "feat: add run_once (moved from llm_agent, fixed import, removed dead code)"
```

---

### Task 4: Prompt builder (`prompt_builder.py`)

**Files:**
- Create: `llm_eval/prompt_builder.py`
- Create: `tests/test_prompt_builder.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_prompt_builder.py`:
```python
from llm_eval.job import Outcome
from llm_eval.prompt_builder import build_prompt


def _noop(r):
    pass


def test_prompt_starts_with_purpose():
    outcomes = [Outcome("complete", "All done", [], _noop)]
    prompt = build_prompt("Review this doc.", outcomes)
    assert prompt.startswith("Review this doc.")


def test_prompt_contains_all_status_file_names():
    outcomes = [
        Outcome("complete",   "Spec is complete", [], _noop),
        Outcome("incomplete", "Spec has gaps",    [], _noop),
    ]
    prompt = build_prompt("Review.", outcomes)
    assert "status_complete" in prompt
    assert "status_incomplete" in prompt


def test_prompt_contains_outcome_descriptions():
    outcomes = [Outcome("complete", "Spec is complete", [], _noop)]
    prompt = build_prompt("Review.", outcomes)
    assert "Spec is complete" in prompt


def test_output_files_listed_only_for_their_outcome():
    outcomes = [
        Outcome("complete",   "All good", [],               _noop),
        Outcome("incomplete", "Has gaps", ["questions.txt"], _noop),
    ]
    prompt = build_prompt("Review.", outcomes)
    assert "questions.txt" in prompt
    # questions.txt mention comes after the incomplete outcome mention
    assert prompt.index("questions.txt") > prompt.index("incomplete")


def test_no_output_files_section_when_none_declared():
    outcomes = [Outcome("complete", "All good", [], _noop)]
    prompt = build_prompt("Review.", outcomes)
    assert "also write" not in prompt


def test_prompt_contains_single_file_rule():
    outcomes = [Outcome("complete", "All good", [], _noop)]
    prompt = build_prompt("Review.", outcomes)
    assert "Do not create more than one status file" in prompt
    assert "Do not write anything inside the status file" in prompt
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_prompt_builder.py -v
```

Expected: `ModuleNotFoundError: No module named 'llm_eval.prompt_builder'`

- [ ] **Step 3: Create `llm_eval/prompt_builder.py`**

```python
from llm_eval.job import Outcome


def build_prompt(purpose: str, outcomes: list[Outcome]) -> str:
    lines = [
        purpose,
        "",
        "---",
        "",
        "After completing your analysis, you MUST create exactly one of the following "
        "empty files in your current working directory to signal your conclusion. "
        "This must be the last action you take.",
        "",
        "Status files (create exactly one, leave it empty):",
    ]

    for outcome in outcomes:
        lines.append(f"  status_{outcome.status:<20} — {outcome.description}")

    lines.append("")

    for outcome in outcomes:
        if outcome.output_files:
            lines.append(f'If the outcome is "{outcome.status}", also write these files:')
            for filename in outcome.output_files:
                lines.append(f"  {filename}")
            lines.append("")

    lines.append("Do not create more than one status file.")
    lines.append("Do not write anything inside the status file.")

    return "\n".join(lines)
```

- [ ] **Step 4: Run to confirm passing**

```bash
python -m pytest tests/test_prompt_builder.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add llm_eval/prompt_builder.py tests/test_prompt_builder.py
git commit -m "feat: add prompt_builder"
```

---

### Task 5: Workspace management (`workspace.py`)

**Files:**
- Create: `llm_eval/workspace.py`
- Create: `tests/test_workspace.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_workspace.py`:
```python
from pathlib import Path
from llm_eval.workspace import create_workspace, cleanup_workspace


def test_create_workspace_returns_job_id_and_path(tmp_path):
    job_id, ws = create_workspace(str(tmp_path))
    assert isinstance(job_id, str)
    assert len(job_id) == 8
    assert ws.exists()
    assert ws.is_dir()


def test_workspace_path_contains_job_id(tmp_path):
    job_id, ws = create_workspace(str(tmp_path))
    assert job_id in str(ws)


def test_workspace_nested_under_llm_eval(tmp_path):
    _, ws = create_workspace(str(tmp_path))
    assert ws.parent.name == ".llm_eval"


def test_create_workspace_uses_cwd_when_base_dir_none(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _, ws = create_workspace(None)
    assert ws.exists()
    cleanup_workspace(ws)


def test_cleanup_removes_workspace(tmp_path):
    _, ws = create_workspace(str(tmp_path))
    cleanup_workspace(ws)
    assert not ws.exists()


def test_cleanup_ignores_missing_directory(tmp_path):
    ws = tmp_path / "nonexistent"
    cleanup_workspace(ws)  # must not raise


def test_two_calls_produce_different_job_ids(tmp_path):
    id1, ws1 = create_workspace(str(tmp_path))
    id2, ws2 = create_workspace(str(tmp_path))
    assert id1 != id2
    cleanup_workspace(ws1)
    cleanup_workspace(ws2)
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_workspace.py -v
```

Expected: `ModuleNotFoundError: No module named 'llm_eval.workspace'`

- [ ] **Step 3: Create `llm_eval/workspace.py`**

```python
import shutil
import uuid
from pathlib import Path


def create_workspace(base_dir: str | None) -> tuple[str, Path]:
    job_id = uuid.uuid4().hex[:8]
    base = Path(base_dir) if base_dir else Path.cwd()
    workspace = base / ".llm_eval" / job_id
    workspace.mkdir(parents=True, exist_ok=True)
    return job_id, workspace


def cleanup_workspace(workspace: Path) -> None:
    shutil.rmtree(workspace, ignore_errors=True)
```

- [ ] **Step 4: Run to confirm passing**

```bash
python -m pytest tests/test_workspace.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add llm_eval/workspace.py tests/test_workspace.py
git commit -m "feat: add workspace management"
```

---

### Task 6: Status resolver (`status_resolver.py`)

**Files:**
- Create: `llm_eval/status_resolver.py`
- Create: `tests/test_status_resolver.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_status_resolver.py`:
```python
import logging
import pytest
from pathlib import Path
from llm_eval.job import Outcome, JobResult
from llm_eval.status_resolver import resolve


def _noop(r):
    pass


def _outcomes(*statuses):
    return [Outcome(s, f"desc {s}", [], _noop) for s in statuses]


def test_resolve_detects_status_file(tmp_path):
    (tmp_path / "status_complete").touch()
    outcomes = _outcomes("complete", "error")
    matched, result = resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")
    assert result.status == "complete"
    assert matched.status == "complete"


def test_resolve_raises_when_no_status_file_and_no_error_outcome(tmp_path):
    outcomes = _outcomes("complete")
    with pytest.raises(RuntimeError, match="No status file"):
        resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")


def test_resolve_triggers_error_outcome_when_no_status_file(tmp_path):
    outcomes = _outcomes("complete", "error")
    matched, result = resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")
    assert result.status == "error"
    assert matched.status == "error"


def test_resolve_raises_when_status_file_matches_no_outcome(tmp_path):
    (tmp_path / "status_unknown").touch()
    outcomes = _outcomes("complete")
    with pytest.raises(RuntimeError, match="does not match any defined outcome"):
        resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")


def test_resolve_raises_when_declared_output_file_missing(tmp_path):
    (tmp_path / "status_incomplete").touch()
    outcomes = [Outcome("incomplete", "gaps", ["questions.txt"], _noop)]
    with pytest.raises(RuntimeError, match="questions.txt"):
        resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")


def test_resolve_collects_declared_output_file_content(tmp_path):
    (tmp_path / "status_incomplete").touch()
    (tmp_path / "questions.txt").write_text("Q1?")
    outcomes = [Outcome("incomplete", "gaps", ["questions.txt"], _noop)]
    _, result = resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")
    assert result.files["questions.txt"] == "Q1?"


def test_resolve_excludes_status_file_from_files_dict(tmp_path):
    (tmp_path / "status_complete").touch()
    outcomes = _outcomes("complete")
    _, result = resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")
    assert "status_complete" not in result.files


def test_resolve_populates_job_result_metadata(tmp_path):
    (tmp_path / "status_complete").touch()
    outcomes = _outcomes("complete")
    _, result = resolve(tmp_path, outcomes, "id1", "claude", 2.5, "raw stdout")
    assert result.job_id == "id1"
    assert result.target == "claude"
    assert result.duration_seconds == 2.5
    assert result.stdout == "raw stdout"


def test_resolve_uses_first_alphabetical_on_multiple_status_files(tmp_path, caplog):
    (tmp_path / "status_complete").touch()
    (tmp_path / "status_incomplete").touch()
    outcomes = _outcomes("complete", "incomplete")
    with caplog.at_level(logging.WARNING, logger="llm_eval.status_resolver"):
        matched, result = resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")
    assert result.status == "complete"
    assert "Multiple status files" in caplog.text
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_status_resolver.py -v
```

Expected: `ModuleNotFoundError: No module named 'llm_eval.status_resolver'`

- [ ] **Step 3: Create `llm_eval/status_resolver.py`**

```python
import logging
from pathlib import Path

from llm_eval.job import JobResult, Outcome

logger = logging.getLogger(__name__)


def resolve(
    workspace: Path,
    outcomes: list[Outcome],
    job_id: str,
    target: str,
    duration_seconds: float,
    stdout: str,
) -> tuple[Outcome, JobResult]:
    status_files = sorted(workspace.glob("status_*"))

    if len(status_files) > 1:
        logger.warning(
            "Multiple status files found: %s. Using %s.",
            [p.name for p in status_files],
            status_files[0].name,
        )

    if not status_files:
        error_outcome = next((o for o in outcomes if o.status == "error"), None)
        if error_outcome is None:
            raise RuntimeError(
                "No status file created by LLM and no 'error' outcome defined."
            )
        matched = error_outcome
        status_name = "error"
    else:
        status_name = status_files[0].name[len("status_"):]
        matched = next((o for o in outcomes if o.status == status_name), None)
        if matched is None:
            raise RuntimeError(
                f"Status file 'status_{status_name}' does not match any defined outcome."
            )

    missing = [f for f in matched.output_files if not (workspace / f).exists()]
    if missing:
        raise RuntimeError(
            f"Outcome '{status_name}' declared output_files {missing} "
            "but LLM did not create them."
        )

    files: dict[str, str] = {
        path.name: path.read_text(encoding="utf-8")
        for path in workspace.iterdir()
        if path.is_file() and not path.name.startswith("status_")
    }

    result = JobResult(
        job_id=job_id,
        status=status_name,
        target=target,
        duration_seconds=duration_seconds,
        files=files,
        stdout=stdout,
    )
    return matched, result
```

- [ ] **Step 4: Run to confirm passing**

```bash
python -m pytest tests/test_status_resolver.py -v
```

Expected: 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add llm_eval/status_resolver.py tests/test_status_resolver.py
git commit -m "feat: add status_resolver"
```

---

### Task 7: Wire up `evaluate()` in `__init__.py`

**Files:**
- Modify: `llm_eval/__init__.py`
- Create: `tests/test_evaluate.py`

- [ ] **Step 1: Write failing integration tests**

Create `tests/test_evaluate.py`:
```python
import pytest
from pathlib import Path
from unittest.mock import patch
from llm_eval import evaluate
from llm_eval.job import Outcome, JobResult


def _noop(r):
    pass


def _fake_run_once_writing(status_name, extra_files=None):
    """Returns a fake run_once that creates status + extra files in the workspace cwd."""
    def fake(target, prompt, **kwargs):
        ws = Path(kwargs["cwd"])
        (ws / f"status_{status_name}").touch()
        for fname, content in (extra_files or {}).items():
            (ws / fname).write_text(content)
        return "fake stdout"
    return fake


def test_evaluate_calls_matching_callback(tmp_path):
    received = []

    outcomes = [
        Outcome("complete",   "Done",      [],               lambda r: received.append(r)),
        Outcome("incomplete", "Has gaps",  ["questions.txt"], _noop),
    ]

    with patch("llm_eval.llm_svc.run_once", _fake_run_once_writing("complete")):
        evaluate(target="claude", purpose="Review.", outcomes=outcomes, cwd=str(tmp_path))

    assert len(received) == 1
    assert received[0].status == "complete"
    assert received[0].target == "claude"
    assert received[0].stdout == "fake stdout"


def test_evaluate_passes_files_to_callback(tmp_path):
    received = []

    outcomes = [
        Outcome("incomplete", "Has gaps", ["questions.txt"],
                lambda r: received.append(r)),
    ]

    with patch("llm_eval.llm_svc.run_once",
               _fake_run_once_writing("incomplete", {"questions.txt": "Q1?"})):
        evaluate(target="claude", purpose="Review.", outcomes=outcomes, cwd=str(tmp_path))

    assert received[0].files["questions.txt"] == "Q1?"


def test_evaluate_cleans_up_workspace_after_callback(tmp_path):
    ws_path = []

    def capture_ws(target, prompt, **kwargs):
        ws_path.append(Path(kwargs["cwd"]))
        (ws_path[0] / "status_complete").touch()
        return ""

    outcomes = [Outcome("complete", "Done", [], _noop)]

    with patch("llm_eval.llm_svc.run_once", capture_ws):
        evaluate(target="claude", purpose=".", outcomes=outcomes, cwd=str(tmp_path))

    assert not ws_path[0].exists()


def test_evaluate_cleans_up_workspace_even_when_callback_raises(tmp_path):
    ws_path = []

    def capture_ws(target, prompt, **kwargs):
        ws_path.append(Path(kwargs["cwd"]))
        (ws_path[0] / "status_complete").touch()
        return ""

    def raising_callback(r):
        raise ValueError("callback error")

    outcomes = [Outcome("complete", "Done", [], raising_callback)]

    with patch("llm_eval.llm_svc.run_once", capture_ws):
        with pytest.raises(ValueError, match="callback error"):
            evaluate(target="claude", purpose=".", outcomes=outcomes, cwd=str(tmp_path))

    assert not ws_path[0].exists()


def test_evaluate_calls_on_exception_when_run_once_raises(tmp_path):
    errors = []

    def boom(target, prompt, **kwargs):
        raise RuntimeError("CLI not found")

    outcomes = [Outcome("complete", "Done", [], _noop)]

    evaluate(
        target="claude",
        purpose=".",
        outcomes=outcomes,
        on_exception=lambda exc: errors.append(exc),
        cwd=str(tmp_path),
    )

    assert len(errors) == 1
    assert "CLI not found" in str(errors[0])


def test_evaluate_propagates_exception_when_no_on_exception(tmp_path):
    def boom(target, prompt, **kwargs):
        raise RuntimeError("CLI not found")

    outcomes = [Outcome("complete", "Done", [], _noop)]

    with patch("llm_eval.llm_svc.run_once", boom):
        with pytest.raises(RuntimeError, match="CLI not found"):
            evaluate(target="claude", purpose=".", outcomes=outcomes, cwd=str(tmp_path))


def test_evaluate_raises_on_invalid_target(tmp_path):
    with pytest.raises(ValueError, match="Unsupported target"):
        evaluate(target="nonexistent", purpose=".", outcomes=[])
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_evaluate.py -v
```

Expected: `ImportError` or `AttributeError` — `evaluate` not yet implemented.

- [ ] **Step 3: Implement `llm_eval/__init__.py`**

```python
import logging
import time
from typing import Callable

from llm_eval import llm_svc
from llm_eval.job import JobResult, Outcome
from llm_eval.llm_target import LLMTarget
from llm_eval.prompt_builder import build_prompt
from llm_eval.status_resolver import resolve
from llm_eval.workspace import cleanup_workspace, create_workspace

__all__ = ["evaluate", "Outcome", "JobResult"]

logger = logging.getLogger(__name__)


def evaluate(
    target: str,
    purpose: str,
    outcomes: list[Outcome],
    *,
    on_exception: Callable[[Exception], None] | None = None,
    model: str | None = None,
    timeout: float = 1800,
    cwd: str | None = None,
) -> None:
    try:
        llm_target = LLMTarget(target)
    except ValueError:
        valid = [t.value for t in LLMTarget]
        raise ValueError(f"Unsupported target {target!r}. Valid: {valid}")

    prompt = build_prompt(purpose, outcomes)
    job_id, workspace = create_workspace(cwd)
    start = time.monotonic()

    try:
        stdout = llm_svc.run_once(
            llm_target,
            prompt,
            model=model,
            cwd=str(workspace),
            timeout=timeout,
        )
    except Exception as exc:
        cleanup_workspace(workspace)
        if on_exception is not None:
            on_exception(exc)
            return
        raise

    duration = time.monotonic() - start

    try:
        matched_outcome, result = resolve(
            workspace=workspace,
            outcomes=outcomes,
            job_id=job_id,
            target=target,
            duration_seconds=duration,
            stdout=stdout,
        )
    except Exception as exc:
        cleanup_workspace(workspace)
        if on_exception is not None:
            on_exception(exc)
            return
        raise

    try:
        matched_outcome.callback(result)
    finally:
        cleanup_workspace(workspace)
```

- [ ] **Step 4: Run to confirm passing**

```bash
python -m pytest tests/test_evaluate.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add llm_eval/__init__.py tests/test_evaluate.py
git commit -m "feat: implement evaluate() — wires prompt_builder, workspace, run_once, status_resolver"
```

---

### Task 8: Remove old files and add `pyproject.toml`

**Files:**
- Delete: `main.py`, `requirements.txt`, `Dockerfile`, `llm_agent/`
- Create: `pyproject.toml`

- [ ] **Step 1: Delete removed files**

```bash
git rm main.py requirements.txt Dockerfile
git rm -r llm_agent/
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "llm-eval"
version = "0.1.0"
description = "Structured LLM task runner with outcome routing via file signals"
requires-python = ">=3.11"
dependencies = []

[tool.setuptools.packages.find]
where = ["."]
include = ["llm_eval*"]
```

- [ ] **Step 3: Install library in editable mode**

```bash
pip install -e .
```

- [ ] **Step 4: Run full test suite one final time**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "chore: remove FastAPI service files, add pyproject.toml"
```

---

## Self-Review

**Spec coverage:**
- ✅ `evaluate()` with all parameters
- ✅ `Outcome` dataclass with all fields
- ✅ `JobResult` dataclass with all fields
- ✅ Prompt construction with status + output_files instructions
- ✅ Workspace per-call isolation and cleanup
- ✅ Status file scanning (one found, none found, multiple found)
- ✅ `output_files` missing → `RuntimeError`
- ✅ `on_exception` called on subprocess failure
- ✅ Exception propagates when `on_exception` not provided
- ✅ Callback raises → workspace still cleaned up
- ✅ Old files removed
- ✅ `pyproject.toml` for installability

**Placeholder scan:** None found.

**Type consistency:** `Outcome`, `JobResult`, `resolve()`, `create_workspace()`, `cleanup_workspace()`, `build_prompt()` — all names consistent across tasks.
