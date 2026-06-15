## Why

`llm_eval` 目前支援五個 LLM target（Claude、Gemini、Codex、OpenCode、Copilot），但缺少 DeepSeek。DeepSeek 提供 Anthropic-compatible API endpoint，可以用 Claude CLI 直接呼叫，只需替換環境變數。加上這個 target 後，evaluation pipeline 就能把 DeepSeek 當作獨立 target 使用，也可以放在 fallback chain 裡。

## What Changes

- `LLMTarget` enum 新增 `DEEPSEEK = "deepseek"` 成員
- `llm_svc.run()` 新增 DEEPSEEK branch：複用 Claude CLI 的 command，但注入 DeepSeek 專屬環境變數
- `preflight.py` 對 DEEPSEEK 先跳過 CLI 登入檢查（DeepSeek 不需要 `claude auth`），直接回傳 ok
- DeepSeek 的 API base URL、model 名稱等常數寫死在模組內，API key 從 `DEEPSEEK_AUTH_TOKEN` 環境變數讀取
- 支援 `model` 參數（覆寫預設 model）

## Capabilities

### New Capabilities

- `deepseek-target`: 讓 `llm_eval` 的 `evaluate()` 和 `run()` 接受 `LLMTarget.DEEPSEEK`，透過 Claude CLI + DeepSeek Anthropic-compatible API 執行 LLM 任務

### Modified Capabilities

（無 — 這是全新功能，不修改既有 target 的行為）

## Impact

- `llm_eval/llm_target.py` — 加一個 enum 成員
- `llm_eval/llm_svc.py` — 加 elif branch + 模組級常數
- `llm_eval/preflight.py` — 加 always-ok checker
- `tests/test_llm_target.py` — 加 accessibility assert
