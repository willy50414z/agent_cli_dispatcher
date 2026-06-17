## Why

Codex target 目前沒有將 `--model` 和 effort 參數傳遞到底層 `codex exec` CLI，導致無法指定模型變體（如 `gpt-5.5`）和 effort level（如 `xhigh`/`high`）。同時，缺乏對 CLI → subprocess 模型參數傳遞的整合測試，無法驗證各 target 的參數是否正確到達底層 CLI。

## What Changes

- **Codex target 補上 `--model` 傳遞**：`llm_svc.run()` 的 Codex 分支將 `model` 參數傳給 `codex exec --model <model>`
- **新增 `--effort` CLI 參數**：`run` 和 `evaluate` 子命令支援 `--effort`，對應到 codex 的 `--effort` 旗標
- **整合測試**：新增參數化測試，mock `subprocess.run`，驗證 Claude/Codex/DeepSeek 各 target 的正確 CLI 指令和環境變數組合

## Capabilities

### New Capabilities
- `codex-model-effort`: Codex target 支援 --model 和 --effort 參數傳遞，讓使用者可指定 OpenAI 模型和 effort level
- `cli-model-integration-tests`: 整合測試覆蓋 CLI → subprocess 的參數傳遞鏈路，驗證各 target 在不同 model/effort 組合下的正確性

### Modified Capabilities
<!-- None - this is all new wiring, not changing existing spec-level behavior -->

## Impact

- `llm_eval/cli.py`：`_add_common_execution_args` 新增 `--effort` 參數
- `llm_eval/llm_svc.py`：`run()` 簽章新增 `effort` 參數，Codex 分支補上 `--model` 和 `--effort` 旗標
- `llm_eval/__init__.py`：`run()` 和 `evaluate()` 簽章新增 `effort` 參數傳遞
- `tests/test_cli.py`：新增 `TestModelEffortIntegration` 測試類別
