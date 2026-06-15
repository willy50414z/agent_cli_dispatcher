## ADDED Requirements

### Requirement: Installable command
The package SHALL expose an installable console command named `agent-dispatch`.

#### Scenario: Console script is installed
- **WHEN** the package is installed in editable or packaged form
- **THEN** the `agent-dispatch` command is available on the environment PATH
- **AND** running `agent-dispatch --help` exits successfully

### Requirement: Raw run command
The CLI SHALL provide a `run` subcommand that invokes a selected LLM target with a raw prompt and writes the target stdout to process stdout.

#### Scenario: Run with inline prompt
- **WHEN** the user runs `agent-dispatch run --target deepseek --prompt "hello"`
- **THEN** the CLI invokes the raw `run` execution path with target `deepseek`
- **AND** the CLI writes the returned model output to stdout
- **AND** the CLI exits with status code 0

#### Scenario: Run with prompt file
- **WHEN** the user runs `agent-dispatch run --target deepseek --prompt-file prompt.md`
- **THEN** the CLI reads `prompt.md` as UTF-8 text
- **AND** the CLI invokes the raw `run` execution path with that prompt

#### Scenario: Run with stdin prompt
- **WHEN** the user pipes prompt text into `agent-dispatch run --target deepseek --stdin`
- **THEN** the CLI reads the prompt from stdin
- **AND** the CLI invokes the raw `run` execution path with that prompt

### Requirement: Evaluate command
The CLI SHALL provide an `evaluate` subcommand that performs outcome-routed LLM execution and emits a machine-readable JSON result.

#### Scenario: Evaluate with declared outcomes
- **WHEN** the user runs `agent-dispatch evaluate --target deepseek --purpose-file purpose.md --outcome complete="Done" --outcome failed="Failed" --json`
- **THEN** the CLI builds an outcome-routed prompt from the purpose and declared outcomes
- **AND** the CLI invokes the selected LLM target
- **AND** the CLI resolves the selected status file
- **AND** the CLI writes one JSON object to stdout containing `status`, `target`, `duration_seconds`, `stdout`, and `files`
- **AND** the CLI exits with status code 0

#### Scenario: Evaluate with outcome output files
- **WHEN** the user includes `--output-file failed=errors.txt`
- **THEN** the CLI declares `errors.txt` as an output file for the `failed` outcome
- **AND** the JSON result includes the file content when the `failed` outcome is selected

### Requirement: Target fallback
The CLI SHALL support ordered fallback targets for both `run` and `evaluate`.

#### Scenario: Fallback target list succeeds
- **WHEN** the user supplies `--targets claude,deepseek`
- **THEN** the CLI tries the targets in the provided order
- **AND** the CLI returns the first successful target result

#### Scenario: Target arguments are mutually exclusive
- **WHEN** the user supplies both `--target deepseek` and `--targets claude,deepseek`
- **THEN** the CLI exits with a non-zero status code
- **AND** the CLI writes an argument error to stderr

### Requirement: Health command
The CLI SHALL provide a `health` subcommand that reports LLM target availability.

#### Scenario: Health check all targets
- **WHEN** the user runs `agent-dispatch health --json`
- **THEN** the CLI checks all known targets
- **AND** the CLI writes JSON keyed by target name with `ok` and `reason` fields

#### Scenario: Health check one target
- **WHEN** the user runs `agent-dispatch health --target codex --json`
- **THEN** the CLI checks only the `codex` target
- **AND** the CLI writes that target status as JSON

### Requirement: Error handling
The CLI SHALL use deterministic exit codes and stderr diagnostics for invalid input and execution failures.

#### Scenario: Missing prompt input
- **WHEN** the user runs `agent-dispatch run --target deepseek` without `--prompt`, `--prompt-file`, or `--stdin`
- **THEN** the CLI exits with a non-zero status code
- **AND** the CLI writes an argument error to stderr

#### Scenario: Execution failure
- **WHEN** the selected LLM target raises an execution error
- **THEN** the CLI exits with a non-zero status code
- **AND** the CLI writes the error message to stderr
- **AND** the CLI does not write a success JSON object to stdout
