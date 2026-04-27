# llm_eval Library Design

**Date:** 2026-04-27
**Status:** Approved

---

## Overview

Transform the existing project from a FastAPI HTTP service into a pure Python library called `llm_eval`. The library lets callers run a structured LLM task, define possible outcomes upfront, and receive a callback routed to the matching outcome — all based on which status file the LLM agent creates in a temporary workspace.

**Removed from project:**
- `main.py` (FastAPI service)
- `requirements.txt`
- `Dockerfile`
- API key check logic

---

## Core Concept

The caller provides a `purpose` (what to analyse) and a list of `Outcome` objects (what the LLM might conclude). The library:

1. Builds a prompt that instructs the LLM to create exactly one empty status file (`status_<name>`) and any declared output files
2. Runs the LLM CLI in an isolated workspace directory
3. Scans the workspace for a status file to determine which outcome occurred
4. Calls the matching `Outcome.callback` with a `JobResult`
5. Cleans up the workspace after the callback returns

If no status file is found and the LLM did not fail, the `"error"` outcome is triggered (if defined). If the LLM subprocess itself raises, `on_exception` is called.

---

## Public API

```python
from llm_eval import evaluate, Outcome, JobResult

evaluate(
    target="claude",
    purpose="Review this spec:\n```\n{content}\n```",
    outcomes=[
        Outcome(
            status="complete",
            description="The spec is complete and well-formed",
            output_files=[],
            callback=on_complete,
        ),
        Outcome(
            status="incomplete",
            description="The spec has gaps or missing sections",
            output_files=["questions.txt"],
            callback=on_incomplete,
        ),
        Outcome(
            status="error",
            description="Cannot determine completeness",
            output_files=[],
            callback=on_error,
        ),
    ],
    on_exception=lambda exc: logger.error("LLM failed: %s", exc),
    model=None,      # optional model override
    timeout=1800,    # seconds, passed to run_once()
)
```

### `evaluate()` parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `target` | `str` | yes | LLMTarget value: `"claude"`, `"gemini"`, `"codex"`, `"opencode"`, `"copilot"` |
| `purpose` | `str` | yes | The task description. Embedded verbatim in the built prompt. |
| `outcomes` | `list[Outcome]` | yes | Possible outcomes. At least one required. |
| `on_exception` | `Callable[[Exception], None]` | no | Called when the LLM subprocess raises. If omitted, exception propagates. |
| `model` | `str \| None` | no | Model override passed to `run_once()`. |
| `timeout` | `float` | no | Subprocess timeout in seconds. Default 1800. |

### `Outcome` fields

| Field | Type | Description |
|---|---|---|
| `status` | `str` | Identifier, e.g. `"complete"`. Library creates signal file `status_<status>`. |
| `description` | `str` | Plain-language description shown to the LLM: when should it pick this outcome. |
| `output_files` | `list[str]` | Files the LLM should additionally write for this outcome, e.g. `["questions.txt"]`. |
| `callback` | `Callable[[JobResult], None]` | Called when this outcome is detected. |

### `JobResult` fields

| Field | Type | Description |
|---|---|---|
| `job_id` | `str` | UUID hex identifying this call. |
| `status` | `str` | The outcome status that was triggered. |
| `target` | `str` | LLM target used. |
| `duration_seconds` | `float` | Wall time from LLM start to completion. |
| `files` | `dict[str, str]` | All files found in workspace: `{filename: content}`. |
| `stdout` | `str` | Raw LLM stdout. |

---

## Prompt Construction (`prompt_builder.py`)

The library appends a structured instruction block to the caller's `purpose`. Example for the spec review case:

```
{purpose}

---

After completing your analysis, you MUST create exactly one of the following empty files
in your current working directory to signal your conclusion. This must be the last action
you take.

Status files (create exactly one, leave it empty):
  status_complete   — The spec is complete and well-formed
  status_incomplete — The spec has gaps or missing sections
  status_error      — Cannot determine completeness

If the outcome is "incomplete", also write these files:
  questions.txt     — The questions or gaps you identified

Do not create more than one status file.
Do not write anything inside the status file.
```

The `output_files` instructions are only appended for their matching outcome to keep the prompt focused.

---

## Workspace Management (`workspace.py`)

- Each `evaluate()` call creates a unique temp directory: `{cwd or tempdir}/.llm_eval/{job_id}/`
- This directory is passed as `cwd` to `run_once()`
- After `callback` returns (or `on_exception` returns), the workspace is deleted unconditionally
- If `callback` raises, the workspace is still deleted and the exception propagates to the caller

---

## Status Resolution (`status_resolver.py`)

After `run_once()` returns:

1. Scan workspace for files matching `status_*`
2. If exactly one found → extract status name, find matching `Outcome`, call its callback
3. If none found → find `Outcome` with `status="error"`, call it (if defined); otherwise raise `RuntimeError("No status file created and no error outcome defined")`
4. If more than one found → use the first one alphabetically, log a warning

---

## Module Structure

```
llm_eval/
├── __init__.py        # exports: evaluate, Outcome, JobResult
├── job.py             # Outcome, JobResult dataclasses
├── prompt_builder.py  # builds full prompt from purpose + outcomes
├── workspace.py       # creates and cleans up per-call workspace
├── status_resolver.py # scans workspace, resolves outcome
├── llm_svc.py         # run_once() (moved from llm_agent/)
└── llm_target.py      # LLMTarget enum (moved from llm_agent/)
```

`llm_agent/` directory is removed. `llm_eval/llm_svc.py` retains existing quota retry logic and CLI resolution. API key checks and `_CLI_CRED_DIRS` health-check logic are removed.

---

## Error Handling Contract

| Situation | Behaviour |
|---|---|
| LLM subprocess fails (non-zero exit, timeout, binary not found) | `on_exception(exc)` called; if not defined, exception propagates |
| LLM succeeds, no status file found, `"error"` outcome defined | `"error"` outcome callback called |
| LLM succeeds, no status file found, no `"error"` outcome | `RuntimeError` raised |
| Callback raises | Exception propagates to `evaluate()` caller; workspace still cleaned up |
| Multiple status files found | First alphabetically used; warning logged |
| Declared `output_files` not created by LLM | `RuntimeError` raised; workspace cleaned up; caller handles |

---

## Concurrency Model

`evaluate()` is synchronous and blocking. It has no internal threads. If the caller needs concurrent LLM calls, they manage their own threads or process pool. The library is stateless between calls.

---

## What Is Not In Scope

- Async / queue-based execution (caller's responsibility)
- Webhook callbacks (caller's responsibility)
- API key management
- HTTP interface
- Persistent job storage
