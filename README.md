# llm-eval

A Python library for running structured LLM tasks with outcome routing. Define what the agent should conclude, and receive a typed callback for whichever outcome the LLM signals — no polling, no parsing.

## How it works

1. You provide a `purpose` (the task) and a list of `Outcome` objects (what the LLM might decide).
2. The library builds a prompt that tells the LLM to create exactly one empty signal file (`status_<name>`) plus any declared output files.
3. The LLM CLI runs in an isolated workspace directory.
4. The library scans the workspace, routes to the matching outcome, and calls its `callback` with a `JobResult`.
5. The workspace is deleted unconditionally after the callback returns.

## Installation

```bash
pip install -e .
```

Requires Python ≥ 3.11. The LLM CLI tools must be installed separately and available on your `PATH` (e.g. `claude`, `gemini`, `codex`, `opencode`, `copilot`).

## Quick start

```python
from llm_eval import evaluate, Outcome, JobResult, LLMTarget

def on_complete(result: JobResult) -> None:
    print(f"Done in {result.duration_seconds:.1f}s")

def on_incomplete(result: JobResult) -> None:
    questions = result.files.get("questions.txt", "")
    print("Gaps found:\n", questions)

def on_error(result: JobResult) -> None:
    print("LLM could not determine completeness")

evaluate(
    target=LLMTarget.CLAUDE,
    purpose="Review this spec and determine whether it is complete:\n\n<spec>\n...\n</spec>",
    outcomes=[
        Outcome(
            status="complete",
            description="The spec is complete and well-formed",
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
            callback=on_error,
        ),
    ],
)
```

## API reference

### `evaluate()`

```python
from llm_eval import evaluate, run, LLMTarget

evaluate(
    target,        # LLMTarget — LLM CLI to use (see Supported targets)
    purpose,       # str — task description, embedded verbatim in the prompt
    outcomes,      # list[Outcome] — possible conclusions the LLM can signal
    *,
    on_exception=None,  # Callable[[Exception], None] — called on subprocess failure
    model=None,         # str | None — model override passed to the CLI
    timeout=1800,       # float — subprocess timeout in seconds
    cwd=None,           # str | None — base dir for the workspace (default: cwd)
)
```

`evaluate()` is **synchronous and blocking**. For concurrent calls, manage threads or a process pool in the calling code.

`outcomes` must contain at least one `Outcome`. Use `run()` when you only need the
raw LLM response and do not need status-file routing or callbacks.

### `run()`

```python
from llm_eval import run, LLMTarget

answer = run(
    target=LLMTarget.CLAUDE,
    prompt="Explain the difference between latency and throughput.",
)
```

`run()` sends the prompt directly to the selected LLM CLI and returns raw stdout
as `str`. It does not create a workspace, inspect status files, or call outcome
callbacks.

#### Supported targets

| `LLMTarget` member | CLI binary |
|---|---|
| `LLMTarget.CLAUDE` | `claude` |
| `LLMTarget.GEMINI` | `gemini` |
| `LLMTarget.CODEX` | `codex` |
| `LLMTarget.OPENCODE` | `opencode` |
| `LLMTarget.COPILOT` | `copilot` |

### `Outcome`

```python
from llm_eval import Outcome

Outcome(
    status,        # str — identifier, e.g. "complete"
    description,   # str — shown to the LLM: when should it pick this outcome
    callback,      # Callable[[JobResult], None]
    output_files=[], # list[str] — files the LLM must write for this outcome
)
```

### `JobResult`

Passed to the matching `callback`.

| Field | Type | Description |
|---|---|---|
| `job_id` | `str` | Unique ID for this call (8-char hex) |
| `status` | `str` | The outcome that was triggered |
| `target` | `str` | LLM target used |
| `duration_seconds` | `float` | Wall time from LLM start to completion |
| `files` | `dict[str, str]` | All non-status files in the workspace: `{filename: content}` |
| `stdout` | `str` | Raw LLM stdout |

## Error handling

| Situation | Behaviour |
|---|---|
| LLM subprocess fails (non-zero exit, timeout, binary not found) | `on_exception(exc)` is called; if not defined, the exception propagates |
| LLM produces no status file, `"error"` outcome defined | `"error"` outcome callback is called |
| LLM produces no status file, no `"error"` outcome | `RuntimeError` raised |
| Declared `output_files` not created by the LLM | `RuntimeError` raised; workspace still cleaned up |
| Multiple status files found | First alphabetically is used; a warning is logged |
| Callback raises | Exception propagates to `evaluate()` caller; workspace still cleaned up |

```python
import logging

evaluate(
    target="claude",
    purpose="...",
    outcomes=[...],
    on_exception=lambda exc: logging.error("LLM failed: %s", exc),
)
```

## Quota retry

`run_once` automatically retries on quota / rate-limit errors. Configure via environment variables:

| Variable | Default | Description |
|---|---|---|
| `LLM_QUOTA_RETRY_INTERVAL` | `300` | Seconds to wait between quota retries |
| `LLM_QUOTA_MAX_RETRIES` | `288` | Maximum number of quota retries before raising |

## Workspace

Each call creates an isolated directory at `{cwd}/.llm_eval/{job_id}/`. The LLM CLI runs with this as its working directory and must write its signal file there. The directory is deleted after the callback returns (or `on_exception` returns).

## Logging

The library uses the standard `logging` module under the `llm_eval` logger hierarchy. Enable debug output to see prompt content and subprocess details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Running tests

```bash
pip install pytest
pytest
```
