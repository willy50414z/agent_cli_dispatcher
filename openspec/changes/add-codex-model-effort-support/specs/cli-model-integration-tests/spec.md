## ADDED Requirements

### Requirement: Integration tests verify CLI-to-subprocess model parameter passing
The test suite SHALL include parameterized integration tests that mock `subprocess.run` and verify the CLI constructs correct subprocess commands and environment variables for each LLM target with various model/effort combinations.

#### Scenario: Claude target passes --model to claude CLI
- **WHEN** `agent-dispatch run --target claude --model claude-opus-4-8 --prompt "hello"` is called with `subprocess.run` mocked
- **THEN** `subprocess.run` is invoked with a command containing `["claude", "--print", "--dangerously-skip-permissions", "--model", "claude-opus-4-8"]`

#### Scenario: Codex target passes --model and --effort to codex CLI
- **WHEN** `agent-dispatch run --target codex --model gpt-5.5 --effort xhigh --prompt "hello"` is called with `subprocess.run` mocked
- **THEN** `subprocess.run` is invoked with a command containing `["codex", "exec", ..., "--model", "gpt-5.5", "--effort", "xhigh"]`

#### Scenario: Codex target passes --effort high to codex CLI
- **WHEN** `agent-dispatch run --target codex --model gpt-5.5 --effort high --prompt "hello"` is called with `subprocess.run` mocked
- **THEN** `subprocess.run` is invoked with a command containing `["codex", "exec", ..., "--model", "gpt-5.5", "--effort", "high"]`

#### Scenario: DeepSeek target sets ANTHROPIC_MODEL env var and passes --model
- **WHEN** `agent-dispatch run --target deepseek --model deepseek-v4-pro[1m] --prompt "hello"` is called with `subprocess.run` mocked
- **THEN** `subprocess.run` is invoked with env containing `ANTHROPIC_MODEL=deepseek-v4-pro[1m]` and `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`

#### Scenario: DeepSeek target uses default model when --model not specified
- **WHEN** `agent-dispatch run --target deepseek --prompt "hello"` is called without `--model` with `subprocess.run` mocked
- **THEN** `subprocess.run` is invoked with env containing `ANTHROPIC_MODEL=deepseek-v4-pro[1m]` (the hardcoded default)

### Requirement: Tests are independent of actual CLI installations
The integration tests SHALL use `unittest.mock.patch` on `subprocess.run` to avoid requiring actual `claude`, `codex`, or `deepseek` CLI binaries on the test machine.

#### Scenario: Tests run without installed CLIs
- **WHEN** tests are executed on a machine without any LLM CLI tools installed
- **THEN** all integration tests pass because `subprocess.run` is mocked

### Requirement: Prompt is passed via stdin to CLI subprocess
The integration tests SHALL verify that the prompt text is correctly passed as the `input` parameter to `subprocess.run` (stdin), matching each target's input convention.

#### Scenario: Prompt text reaches subprocess.run via stdin
- **WHEN** `agent-dispatch run --target claude --prompt "hello world"` is called with `subprocess.run` mocked
- **THEN** `subprocess.run` receives `input="hello world"`
