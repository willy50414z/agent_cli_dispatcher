## ADDED Requirements

### Requirement: CLI supports --effort parameter
The `run` and `evaluate` subcommands SHALL accept an optional `--effort` parameter that maps to the underlying CLI's effort/thinking level.

#### Scenario: run with --effort
- **WHEN** user runs `agent-dispatch run --target codex --prompt "hello" --effort xhigh`
- **THEN** the effort value `xhigh` is passed to `llm_svc.run()` and forwarded to the codex CLI via `-c model_reasoning_effort=xhigh`

#### Scenario: run without --effort
- **WHEN** user runs `agent-dispatch run --target codex --prompt "hello"` without `--effort`
- **THEN** `llm_svc.run()` receives `effort=None` and no `model_reasoning_effort` config override is added to the subprocess command

#### Scenario: evaluate with --effort
- **WHEN** user runs `agent-dispatch evaluate --target codex --purpose "test" --outcome done=Done --json --effort high`
- **THEN** the effort value `high` is forwarded through `_execute_evaluate` → `_run_with_fallback` → `llm_svc.run()`

### Requirement: Codex target forwards --model to codex exec
The Codex target in `llm_svc.run()` SHALL append `--model <model>` to the `codex exec` command when a model argument is provided.

#### Scenario: Codex with model specified
- **WHEN** `llm_svc.run(LLMTarget.CODEX, prompt, model="gpt-5.5")` is called
- **THEN** the executed command includes `--model gpt-5.5`

#### Scenario: Codex without model
- **WHEN** `llm_svc.run(LLMTarget.CODEX, prompt)` is called without a model argument
- **THEN** the executed command does NOT include `--model`

### Requirement: Codex target forwards effort via config override
The Codex target in `llm_svc.run()` SHALL pass effort as a config override `-c model_reasoning_effort=<level>` (the codex CLI config mechanism) rather than as a CLI flag.

#### Scenario: Codex with effort xhigh
- **WHEN** `llm_svc.run(LLMTarget.CODEX, prompt, effort="xhigh")` is called
- **THEN** the executed command includes `-c model_reasoning_effort=xhigh`

#### Scenario: Codex with effort high
- **WHEN** `llm_svc.run(LLMTarget.CODEX, prompt, effort="high")` is called
- **THEN** the executed command includes `-c model_reasoning_effort=high`

#### Scenario: Codex without effort
- **WHEN** `llm_svc.run(LLMTarget.CODEX, prompt)` is called without an effort argument
- **THEN** the executed command does NOT include `model_reasoning_effort`

### Requirement: llm_svc.run() signature extended with effort parameter
`llm_svc.run()` SHALL accept an optional `effort: str | None = None` keyword argument, placed after the existing `model` parameter.

#### Scenario: Backward compatible
- **WHEN** existing callers invoke `llm_svc.run()` without the `effort` keyword
- **THEN** behavior is unchanged; `effort` defaults to `None`

### Requirement: Public API signatures extended
The public API functions `llm_eval.run()` and `llm_eval.evaluate()` SHALL accept and forward the `effort` parameter.

#### Scenario: llm_eval.run forwards effort
- **WHEN** `llm_eval.run(target=LLMTarget.CODEX, prompt="hello", model="gpt-5.5", effort="xhigh")` is called
- **THEN** `llm_svc.run()` receives `effort="xhigh"`
