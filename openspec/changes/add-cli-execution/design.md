## Context

The package already provides a synchronous Python API for raw LLM execution (`run`) and outcome-routed execution (`evaluate`). The execution layer shells out to target-specific CLIs and already handles long prompts by writing prompt content to files or stdin for several targets.

External agents need a stable process boundary. They should be able to invoke this package from a shell, pass prompts without embedding Python code, and receive deterministic stdout/stderr/exit-code behavior that is easy to automate.

## Goals / Non-Goals

**Goals:**
- Provide a dependency-light CLI using the Python standard library.
- Expose raw prompt execution through a `run` subcommand.
- Expose structured outcome routing through an `evaluate` subcommand that emits JSON instead of using Python callbacks.
- Expose target preflight checks through a `health` subcommand.
- Support inline, file, and stdin input for prompts and purposes.
- Preserve current Python API behavior.

**Non-Goals:**
- Add OpenSpec-specific delegation commands in this change.
- Add asynchronous job queues, background daemons, or persistent job storage.
- Add new LLM targets beyond the targets already supported by the library.
- Change existing `run()` or `evaluate()` Python call signatures.

## Decisions

### Use `argparse` and standard-library JSON

The CLI will live in a new `llm_eval.cli` module and be exposed through a `pyproject.toml` console script. `argparse` is sufficient for subcommands, validation, and help text without adding runtime dependencies.

Alternative considered: `click` or `typer`. They provide nicer ergonomics, but the package currently has no dependencies and the required CLI surface is small.

### Implement CLI `evaluate` with the existing building blocks

The Python `evaluate()` API routes work by invoking callbacks, which is awkward across a process boundary. The CLI should instead use the existing lower-level building blocks (`create_workspace`, `build_prompt`, fallback execution, `resolve`, and `cleanup_workspace`) and serialize the `JobResult` into JSON.

Alternative considered: call `evaluate()` with a callback that captures the result. That works for the success path but is less direct for exception handling and JSON serialization, and it hides the lifecycle needed by the CLI.

### Use explicit outcome flags

The CLI will accept repeated outcome definitions rather than requiring users to write Python:

```bash
agent-dispatch evaluate --target deepseek \
  --purpose-file purpose.md \
  --outcome complete="Implementation is complete" \
  --outcome failed="Implementation failed or is incomplete" \
  --output-file failed=errors.txt \
  --json
```

Each outcome has a status and description. Output files can be attached to a status with repeated `--output-file status=path` flags.

Alternative considered: require a JSON config file for outcomes. A config file may be useful later, but repeated flags are easier for agents to generate and inspect.

### Keep machine output deterministic

`run` writes model stdout to stdout. `evaluate --json` writes one JSON object to stdout. Operational errors write human-readable diagnostics to stderr and exit non-zero. This separation lets calling agents pipe successful results while still surfacing failures.

## Risks / Trade-offs

- CLI `evaluate` duplicates some orchestration logic from Python `evaluate()` -> Mitigation: keep the duplication thin and reuse shared primitives for prompt construction, execution, resolution, and cleanup.
- JSON output must represent binary `JobResult.files` -> Mitigation: decode files as UTF-8 with replacement for CLI JSON and document that CLI output files are text-oriented.
- Outcome flag syntax can become limiting -> Mitigation: keep the first version simple, then add `--outcomes-json` later if real workflows need richer config.
- Subprocess failures may include large stderr/stdout payloads -> Mitigation: existing `LLMEvaluationError` truncation behavior remains in the execution layer.

## Migration Plan

1. Add the CLI module and console script entry point.
2. Add focused tests for command parsing, successful command behavior with mocked execution, JSON output, and exit codes.
3. Document installation and CLI usage in README.
4. Existing Python users continue using the same APIs with no migration required.

Rollback is to remove the console script and CLI module; existing Python APIs are unaffected.

## Open Questions

- Should a future change add `--outcomes-json` for complex outcome definitions?
- Should OpenSpec-specific delegation become a separate `agent-dispatch openspec ...` capability after the generic CLI is available?
