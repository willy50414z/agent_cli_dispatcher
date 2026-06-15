## 1. Enum and Constants

- [x] 1.1 Add `DEEPSEEK = "deepseek"` to `LLMTarget` enum in `llm_eval/llm_target.py`

## 2. Core Execution Logic

- [x] 2.1 Add DeepSeek module-level constants in `llm_eval/llm_svc.py`: base URL, default model names, effort level
- [x] 2.2 Add `elif target == LLMTarget.DEEPSEEK:` branch in `llm_svc.run()` that validates `DEEPSEEK_AUTH_TOKEN`, sets environment variables, and constructs the Claude CLI command (mirroring the CLAUDE branch)
- [x] 2.3 Support `model` parameter: when provided, override `ANTHROPIC_MODEL` env var and pass `--model` flag to CLI

## 3. Preflight

- [x] 3.1 Add `LLMTarget.DEEPSEEK` entry in `preflight.py` `_CHECKERS` dict that returns `TargetStatus(ok=True)` without subprocess calls

## 4. Tests

- [x] 4.1 Add `LLMTarget.DEEPSEEK` accessibility assert in `tests/test_llm_target.py`
- [x] 4.2 Manually verify DEEPSEEK target works end-to-end with a real `DEEPSEEK_AUTH_TOKEN`
