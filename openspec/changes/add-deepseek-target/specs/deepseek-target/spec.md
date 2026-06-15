## ADDED Requirements

### Requirement: DeepSeek as an LLM target
The system SHALL support `LLMTarget.DEEPSEEK` as a valid evaluation target that executes prompts via the Claude CLI binary pointed at the DeepSeek Anthropic-compatible API.

#### Scenario: DeepSeek target runs successfully
- **WHEN** `llm_svc.run(LLMTarget.DEEPSEEK, prompt, ...)` is called and `DEEPSEEK_AUTH_TOKEN` is set
- **THEN** the system invokes the `claude` CLI with `--print --dangerously-skip-permissions` flags
- **AND** the environment variables `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL`, and `CLAUDE_CODE_EFFORT_LEVEL` are set to DeepSeek-specific values
- **AND** returns the CLI stdout

#### Scenario: Missing API key raises error
- **WHEN** `llm_svc.run(LLMTarget.DEEPSEEK, prompt, ...)` is called and `DEEPSEEK_AUTH_TOKEN` is NOT set
- **THEN** a `ValueError` is raised with a message indicating that `DEEPSEEK_AUTH_TOKEN` is required

### Requirement: DeepSeek model configuration
The system SHALL default to `deepseek-v4-pro[1m]` as the model and allow callers to override via the `model` parameter.

#### Scenario: Default model is deepseek-v4-pro[1m]
- **WHEN** `llm_svc.run(LLMTarget.DEEPSEEK, prompt, ...)` is called without a `model` argument
- **THEN** the `ANTHROPIC_MODEL` env var is set to `deepseek-v4-pro[1m]`
- **AND** no `--model` flag is passed to the CLI

#### Scenario: Custom model overrides default
- **WHEN** `llm_svc.run(LLMTarget.DEEPSEEK, prompt, model="deepseek-v4-flash", ...)` is called
- **THEN** the `ANTHROPIC_MODEL` env var is set to `deepseek-v4-flash`
- **AND** the `--model deepseek-v4-flash` flag is passed to the CLI

### Requirement: DeepSeek in evaluation pipeline
The system SHALL support `LLMTarget.DEEPSEEK` in `evaluate()` as both a single target and as part of a fallback chain.

#### Scenario: DeepSeek as single target in evaluate
- **WHEN** `evaluate(target=LLMTarget.DEEPSEEK, purpose="...", outcomes=[...])` is called
- **THEN** the evaluation runs against DeepSeek and resolves the outcome normally

#### Scenario: DeepSeek in fallback chain
- **WHEN** `evaluate(targets=[LLMTarget.CLAUDE, LLMTarget.DEEPSEEK], purpose="...", outcomes=[...])` is called and CLAUDE fails with `LLMEvaluationError`
- **THEN** the system falls back to DEEPSEEK and uses its result

### Requirement: DeepSeek preflight check
The system SHALL report DeepSeek as always-ready in `check_target()` and `check_all()` without performing CLI authentication checks.

#### Scenario: check_target returns ok for DeepSeek
- **WHEN** `check_target(LLMTarget.DEEPSEEK)` is called
- **THEN** it returns `TargetStatus(ok=True)` without invoking any subprocess

### Requirement: DeepSeek target string parsing
The system SHALL accept `"deepseek"` as a valid input to `LLMTarget` enum lookup and `parse_targets()`.

#### Scenario: Parse deepseek string
- **WHEN** `parse_targets("claude,deepseek")` is called
- **THEN** the result is `[LLMTarget.CLAUDE, LLMTarget.DEEPSEEK]`
