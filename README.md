# llm-eval

A Python library for running structured LLM tasks with outcome routing. Define what the agent should conclude, and receive a typed callback for whichever outcome the LLM signals; no polling, no parsing.

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

Requires Python 3.11 or newer. The LLM CLI tools (`claude`, `codex`) must be installed separately and available on your `PATH`. DeepSeek uses the `claude` CLI with a `DEEPSEEK_AUTH_TOKEN` environment variable.

Editable or packaged installs expose the `agent-dispatch` command:

```bash
agent-dispatch --help
```

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
    target,        # LLMTarget: LLM CLI to use (see Supported targets)
    purpose,       # str: task description, embedded verbatim in the prompt
    outcomes,      # list[Outcome]: possible conclusions the LLM can signal
    *,
    on_exception=None,  # Callable[[Exception], None]: called on subprocess failure
    model=None,         # str | None: model override passed to the CLI
    effort=None,        # str | None: reasoning effort (codex only: xhigh/high/medium/low)
    timeout=1800,       # float: subprocess timeout in seconds
    cwd=None,           # str | None: base dir for the workspace (default: cwd)
)
```

`evaluate()` is synchronous and blocking. For concurrent calls, manage threads or a process pool in the calling code.

`outcomes` must contain at least one `Outcome`. Use `run()` when you only need the raw LLM response and do not need status-file routing or callbacks.

### `run()`

```python
from llm_eval import run, LLMTarget

answer = run(
    target=LLMTarget.CLAUDE,
    prompt="Explain the difference between latency and throughput.",
)
```

`run()` sends the prompt directly to the selected LLM CLI and returns raw stdout as `str`. It does not create a workspace, inspect status files, or call outcome callbacks.

#### Supported targets

| `LLMTarget` member | CLI binary | Status |
|---|---|---|
| `LLMTarget.CLAUDE` | `claude` | ✅ Tested |
| `LLMTarget.CODEX` | `codex` | ✅ Tested |
| `LLMTarget.DEEPSEEK` | `claude` with DeepSeek Anthropic-compatible environment | ✅ Tested |
| `LLMTarget.GEMINI` | `gemini` | 🔜 Coming soon |
| `LLMTarget.OPENCODE` | `opencode` | 🔜 Coming soon |
| `LLMTarget.COPILOT` | `copilot` | 🔜 Coming soon |

## CLI

### Raw prompt execution

```bash
agent-dispatch run --target deepseek --prompt "Explain this repository."
```

Specify model and effort (Codex only for effort):

```bash
agent-dispatch run --target claude --model claude-opus-4-8 --prompt "Review this code."
agent-dispatch run --target codex --model gpt-5.5 --effort xhigh --prompt "Optimize this function."
agent-dispatch run --target deepseek --model deepseek-v4-pro[1m] --prompt "Summarize."
```

`run` writes only the model response to stdout on success.

Prompt input can come from exactly one source:

```bash
agent-dispatch run --target deepseek --prompt "inline text"
agent-dispatch run --target deepseek --prompt-file prompt.md
type prompt.md | agent-dispatch run --target deepseek --stdin
```

Use `--targets` for ordered fallback. The first successful target wins:

```bash
agent-dispatch run --targets claude,deepseek --prompt-file prompt.md
```

`--target` and `--targets` are mutually exclusive.

### Outcome-routed evaluation

```bash
agent-dispatch evaluate --target deepseek \
  --purpose-file purpose.md \
  --outcome complete="Implementation is complete" \
  --outcome failed="Implementation failed or is incomplete" \
  --output-file failed=errors.txt \
  --json
```

`--outcome` uses `status=description` syntax and may be repeated. `--output-file` uses `status=path` syntax and declares text files that the selected outcome must write in the evaluation workspace.

Successful `evaluate --json` writes one JSON object to stdout:

```json
{
  "status": "complete",
  "target": "deepseek",
  "duration_seconds": 1.23,
  "stdout": "raw model stdout",
  "files": {
    "errors.txt": "file content"
  }
}
```

File content is decoded as UTF-8 with replacement for invalid bytes.

### OpenSpec delegation installer

`pip install` only installs the package and CLI. It does not modify Codex skills,
project rules, or user-level Codex configuration.

To opt in for the current project, run:

```bash
agent-dispatch install_delegant --mode hybrid
```

The command writes a managed OpenSpec delegation block to `AGENTS.md` in the
target project. Re-running the command updates the managed block in place instead
of duplicating it.

Delegation modes:

| Mode | Label | Behavior |
|---|---|---|
| `main` | A | All OpenSpec apply work stays with the main model. Submodels are not used unless the user explicitly asks. |
| `hybrid` | B | **Recommended.** Propose-time task routing plus delegation-first apply for tagged work. Main model owns scope, integration, final verification, and OpenSpec state; DeepSeek handles delegated implementation/test/review/diagnosis drafts first. |
| `delegated-apply` | C | Main model delegates apply implementation to a submodel and verifies task completion, tests, and spec alignment afterward. Aggressive mode - may increase total token usage. |

#### Hybrid mode responsibility split

Mode B (`hybrid`) is the recommended delegation-first cost-control default. It
requires propose-time task routing and apply-time delegation attempts for tagged
work:

| Main model owns | Delegants are assigned |
|---|---|
| OpenSpec interpretation, scope, and architecture decisions | Implementation drafts with clear file scope |
| Security, data migration, destructive ops, credentials | Small-scope tests and test suggestions |
| High-risk exception decisions | Documentation reading, extraction, and summaries |
| Integration of delegated output | Repetitive edits |
| Large feature acceptance and final tests | Failure diagnosis |
| `tasks.md` checkbox updates | First-pass diff/spec review |
| Final verification and OpenSpec state changes | |

Hybrid routing rules:

- During OpenSpec propose, delegate-friendly implementation, test, review,
  documentation extraction, repetitive edit, and diagnosis work must be split
  into standalone task packets with `context`, `output`, and `verify` notes.
- During apply, Codex must attempt delegation for every `[delegate:deepseek]`,
  `[delegate:test]`, and `[delegate:review]` task before implementing it
  directly.
- `agent-dispatch run --target deepseek --prompt-file <packet>` is the default
  shell delegation path unless a task packet names another target or DeepSeek is
  unavailable.
- Codex may skip or take over only when the task is high-risk, needs broad repo
  context, the delegation backend is unavailable, or one delegated attempt
  returns unusable output. "It is faster for Codex" is not a skip reason.
- Codex still integrates delegated output, runs final verification, and is the
  only actor that marks OpenSpec tasks complete.

For non-interactive setup, pass an explicit mode. `--yes` uses the hybrid default:

```bash
agent-dispatch install_delegant --yes
```

#### Compatibility: `--level`

The deprecated `--level` flag is preserved for existing scripts. Level 1 maps to
`hybrid` and level 2 maps to `delegated-apply`:

```bash
agent-dispatch install_delegant --level 1   # equivalent to --mode hybrid
agent-dispatch install_delegant --level 2   # equivalent to --mode delegated-apply
```

`--mode` and `--level` cannot be used together when they specify incompatible
values. Prefer `--mode` for new installs.

Remove the managed project guidance with:

```bash
agent-dispatch install_delegant --uninstall
```

### Health checks

```bash
agent-dispatch health --json
agent-dispatch health --target codex --json
```

Health output is JSON keyed by target name:

```json
{
  "codex": {
    "ok": true,
    "reason": null
  }
}
```

### CLI exit codes

| Exit code | Meaning |
|---|---|
| `0` | Command succeeded and wrote result data to stdout |
| `1` | Execution or runtime failure; diagnostic written to stderr |
| `2` | Argument parsing or validation failure; diagnostic written to stderr |

### `Outcome`

```python
from llm_eval import Outcome

Outcome(
    status,        # str: identifier, e.g. "complete"
    description,   # str: shown to the LLM: when should it pick this outcome
    callback,      # Callable[[JobResult], None]
    output_files=[], # list[str]: files the LLM must write for this outcome
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
