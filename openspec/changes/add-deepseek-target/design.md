## Context

`llm_eval` 的 `run()` 函式透過 `LLMTarget` enum 派發到不同的 CLI 工具。每個 target 對應一個獨立的 CLI（`claude`, `gemini`, `codex`, `opencode`, `copilot`）。

DeepSeek 沒有自己的 CLI。它提供 Anthropic-compatible API endpoint（`https://api.deepseek.com/anthropic`），可以讓標準 Claude CLI 直接呼叫。現有的 Windows 環境設定腳本（`E:\software\win_scripts\deepseekEnv.ps1`）已經證明了這個模式可行。

此設計把 "Claude CLI + DeepSeek env vars" 封裝成一個新的 `LLMTarget.DEEPSEEK`。

## Goals / Non-Goals

**Goals:**
- 讓 `llm_eval.run(target=LLMTarget.DEEPSEEK, ...)` 可運作
- 讓 `llm_eval.evaluate(target=LLMTarget.DEEPSEEK, ...)` 可運作
- 支援 fallback chain：例如 `targets=[LLMTarget.CLAUDE, LLMTarget.DEEPSEEK]`
- API key 從環境變數 `DEEPSEEK_AUTH_TOKEN` 注入，不進程式碼
- `model` 參數可控（預設 `deepseek-v4-pro[1m]`）

**Non-Goals:**
- 不修改 `deepseekEnv.ps1` 腳本
- 不更動其他 target 的行為
- 不把 DeepSeek env vars 做成外部 config file（先寫死在模組內）
- 不做 preflight 實際檢查（先 always-ok）

## Decisions

### 1. DEEPSEEK 複用 Claude CLI command 而非獨立 CLI

**Why**: DeepSeek 的 API 是 Anthropic-compatible 的。Claude CLI 在設定 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN` 後可以直接打到 DeepSeek。不需要額外安裝 CLI。

**Alternatives considered**:
- 直接 HTTP call DeepSeek API：需重寫整個 subprocess 模型，與既有架構不一致
- 呼叫 `deepseekEnv.ps1` 後再執行 claude：兩個 subprocess 之間 env vars 不會傳遞，除非合併成單一 command，但這會讓 Windows/non-Windows 路徑分歧更大

### 2. 環境變數在 Python 端設定，不依賴外部 PS1 腳本

**Why**: `subprocess.run()` 接受 `env` dict，可以直接在 Python 端設置環境變數。PS1 腳本的內容（base URL、model 名稱）是靜態常數，寫在 Python 裡更可控。唯一的 runtime 變數是 API key，從 `DEEPSEEK_AUTH_TOKEN` 讀取。

**Alternatives considered**:
- 執行 PS1 腳本後 parse 其輸出取得 env vars：過度複雜，PS1 腳本沒有輸出 env vars 的介面
- 把所有值都做成 env var：太多 env vars 反而增加設定負擔

### 3. API key 強制從 `DEEPSEEK_AUTH_TOKEN` 讀取

**Why**: 避免把 API key 寫死在程式碼或 PS1 腳本中。如果 `DEEPSEEK_AUTH_TOKEN` 不存在，直接 `raise ValueError` 說明原因。

### 4. preflight 先跳過（always-ok）

**Why**: DeepSeek 不需要 `claude auth login`（它是 API key 認證，不是 OAuth）。但 `claude auth status` 可能會回傳非零（因為沒登入 Anthropic），所以先不檢查。遇到 runtime error 自然浮現。

### 5. 預設 model 用 `deepseek-v4-pro[1m]`

**Why**: 這是目前 DeepSeek 最強模型，對應 `deepseekEnv.ps1` 中的 `ANTHROPIC_DEFAULT_OPUS_MODEL`。`model` 參數可覆寫。

## Risks / Trade-offs

- **[Risk] DeepSeek API 的 quota/rate-limit error 格式可能與現有 `_QUOTA_ERROR_PATTERNS` 不匹配** → 若遇到，後續補 pattern。不阻塞此 change。
- **[Risk] `deepseek-v4-pro[1m]` model 名稱包含 `[1m]` 後綴，若 DeepSeek 改名需要更新常數** → 常數集中在模組頂部，修改成本低。
- **[Risk] DEEPSEEK 和 CLAUDE 共用 `claude` binary，若使用者環境已有 `ANTHROPIC_AUTH_TOKEN` 指向 Anthropic，DEEPSEEK branch 會完全覆寫** → 這是預期行為，不會互相汙染。
