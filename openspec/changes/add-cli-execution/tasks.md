## 1. CLI Contract Tests

- [x] 1.1 Add tests for `agent-dispatch --help` and subcommand help behavior.
- [x] 1.2 Add tests for `run` with `--prompt`, `--prompt-file`, and `--stdin` using mocked LLM execution.
- [x] 1.3 Add tests for `evaluate --json` with declared outcomes and mocked status resolution.
- [x] 1.4 Add tests for `evaluate --output-file status=path` JSON file serialization.
- [x] 1.5 Add tests for `--target` and `--targets` mutual exclusion and fallback parsing.
- [x] 1.6 Add tests for `health --json` for all targets and a single target using mocked preflight checks.
- [x] 1.7 Add tests for missing input and execution failure exit codes/stderr behavior.

## 2. CLI Implementation

- [x] 2.1 Create `llm_eval/cli.py` with an `argparse` parser and `main(argv=None)` entry point.
- [x] 2.2 Implement shared input loading for inline text, UTF-8 files, and stdin.
- [x] 2.3 Implement target parsing for `--target` and ordered `--targets`.
- [x] 2.4 Implement the `run` subcommand using existing raw `llm_eval.run()`.
- [x] 2.5 Implement the `evaluate` subcommand using existing prompt/workspace/execution/resolution primitives and JSON serialization.
- [x] 2.6 Implement the `health` subcommand using `check_target()` and `check_all()`.
- [x] 2.7 Ensure command success writes only result data to stdout and errors write diagnostics to stderr.

## 3. Packaging and Documentation

- [x] 3.1 Add the `agent-dispatch` console script entry point to `pyproject.toml`.
- [x] 3.2 Update README installation docs with CLI usage and examples.
- [x] 3.3 Document CLI input modes, outcome flag syntax, JSON output shape, and exit-code behavior.

## 4. Verification

- [x] 4.1 Run focused CLI tests.
- [x] 4.2 Run the full test suite.
- [x] 4.3 Verify `agent-dispatch --help` works from an editable install.
- [x] 4.4 Verify `openspec status --change add-cli-execution` reports the change as apply-ready.
