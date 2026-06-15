## Why

`llm_eval` currently exposes `run()` and `evaluate()` only as Python APIs, while agent-to-agent delegation needs a stable command-line surface that other agents can invoke without embedding Python code. Adding a first-class CLI makes this library usable as an automation bridge for Codex/OpenSpec workflows, including dispatching implementation and testing work to DeepSeek.

## What Changes

- Add an installable console command for the package.
- Add a raw `run` command that invokes an LLM target and writes the model stdout to stdout.
- Add an `evaluate` command that exposes outcome-based routing through CLI-friendly JSON output instead of Python callbacks.
- Add a `health` command that reports target availability and credential/preflight status.
- Support prompt/purpose input from inline arguments, files, or stdin so callers can avoid shell command length limits.
- Preserve existing Python API behavior and target implementations.

## Capabilities

### New Capabilities
- `cli-execution`: Command-line execution surface for invoking `run`, `evaluate`, and target health checks from external agents and scripts.

### Modified Capabilities
- None.

## Impact

- Affected package metadata: `pyproject.toml` gains a console script entry point.
- Affected code: new CLI module under `llm_eval`, reusing existing `run()`, `evaluate()`, `Outcome`, `LLMTarget`, `check_target()`, and `check_all()` APIs.
- Affected docs: README gains CLI installation and usage examples.
- Affected tests: CLI argument parsing, stdin/file input, JSON output, exit codes, and health command behavior.
