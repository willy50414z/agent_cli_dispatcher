## 1. CLI layer — add --effort parameter

- [x] 1.1 Add `--effort` to `_add_common_execution_args` in `llm_eval/cli.py`
- [x] 1.2 Update `_handle_run` to pass `effort=args.effort` to `llm_eval.run()`
- [x] 1.3 Update `_handle_evaluate` to pass `effort=args.effort` to `_execute_evaluate`
- [x] 1.4 Update `_execute_evaluate` signature to accept and forward `effort` to `_run_with_fallback`
- [x] 1.5 Update `_run_with_fallback` (in cli.py) signature to accept and forward `effort` to `llm_svc.run`

## 2. Public API — add effort parameter

- [x] 2.1 Add `effort` keyword arg to `llm_eval.run()` in `llm_eval/__init__.py` and forward to `llm_svc.run`
- [x] 2.2 Add `effort` keyword arg to `llm_eval.evaluate()` in `llm_eval/__init__.py` and forward through `_run_with_fallback`
- [x] 2.3 Update `_run_with_fallback` (in `__init__.py`) signature to accept and forward `effort`

## 3. llm_svc layer — wire model and effort for Codex

- [x] 3.1 Add `effort` keyword arg to `llm_svc.run()` signature (after `model`)
- [x] 3.2 Add `--model <model>` to Codex command when `model` is provided
- [x] 3.3 Add `--effort <effort>` to Codex command when `effort` is provided

## 4. Integration tests

- [x] 4.1 Add parameterized test `TestModelEffortIntegration` in `tests/test_cli.py` with mock `subprocess.run`
- [x] 4.2 Test case: Claude target with --model passes --model to claude CLI
- [x] 4.3 Test case: Codex target with --model and --effort xhigh passes both to codex CLI
- [x] 4.4 Test case: Codex target with --model and --effort high passes both to codex CLI
- [x] 4.5 Test case: DeepSeek target with --model sets ANTHROPIC_MODEL env var
- [x] 4.6 Test case: DeepSeek target without --model uses hardcoded default model
- [x] 4.7 Test case: Prompt text passed as stdin input to subprocess.run

## 5. Validation

- [x] 5.1 Run `pytest tests/test_cli.py -v` to verify all existing and new tests pass
