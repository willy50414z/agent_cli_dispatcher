## Context

`llm_eval` 專案透過 CLI (`agent-dispatch`) 包裝多個 LLM CLI 工具（claude、codex、gemini、deepseek 等），提供統一的 `run`/`evaluate` 介面。目前 `--model` 參數僅對 claude、copilot、deepseek 有效；codex 分支完全未使用。此外，codex 支援 `--effort` 旗標來控制推理深度（xhigh/high/medium/low），但專案尚無此機制。

### 現有簽章鏈路

```
cli._handle_run(args)
  → llm_eval.run(target, prompt, model=args.model, timeout=..., cwd=...)
    → llm_svc.run(target, prompt, model=model, cwd=cwd, timeout=timeout)
      → subprocess.run(command, input=stdin, env=env, ...)
```

`model` 參數貫穿 CLI → public API → internal svc 三層。`effort` 需要同樣的傳遞鏈路。

## Goals / Non-Goals

**Goals:**
- Codex target 正確傳遞 `--model` 和 `--effort` 到 `codex exec`
- CLI 提供 `--effort` 參數，可供所有 target 使用（即使目前僅 codex 實際使用）
- 整合測試 mock `subprocess.run` 驗證 Claude/Codex/DeepSeek 的正確指令建構

**Non-Goals:**
- 不改動 gemini、opencode、copilot 的行為（effort 對這些 target 為 no-op）
- 不更動 DeepSeek 現有的硬編碼 effort（`_DEEPSEEK_EFFORT_LEVEL = "max"` 保持不變）
- 不實作真正的端對端測試（需要實際 CLI 和 API key）

## Decisions

### Decision 1: `--effort` 加入 common args 而非 per-target args

**選擇**：將 `--effort` 放在 `_add_common_execution_args` 中，與 `--model`、`--timeout`、`--cwd` 同層。

**理由**：
- 與 `--model` 的模式一致：所有 target 都接受，各 target 自行決定是否使用
- 未來其他 target 若支援 effort 可直接受益，不需改 CLI
- 避免 per-target 參數碎片化

**替代方案**：僅對 codex 子命令加 `--effort` → 拒絕。會造成 CLI 參數不一致，且需要 subparser-level 的條件參數，增加複雜度。

### Decision 2: `effort` 參數位置 — 接在 `model` 之後

**選擇**：在 `llm_svc.run()` 簽章中，`effort` 放在 `model` 之後：

```python
def run(target, prompt, *, model=None, effort=None, cwd=None, timeout=1800, ...):
```

**理由**：
- `model` 和 `effort` 都是模型相關的可選參數，語意上相鄰
- 使用 keyword-only args (`*` 之後) 保持向後相容
- 與 CLI 參數順序一致（`--model` 先於 `--effort`）

### Decision 3: 測試策略 — mock subprocess.run

**選擇**：在測試層 mock `subprocess.run`，不 mock 更高層的 `llm_svc.run` 或 `llm_eval.run`。

**理由**：
- 驗證完整鏈路：CLI arg parsing → handler → llm_eval.run → llm_svc.run → subprocess.run
- 確保未來重構不會意外破壞參數傳遞
- 現有測試已覆蓋 mock `llm_eval.run` 的場景，新測試補上更底層的驗證

**替代方案**：mock `llm_svc.run` → 拒絕。無法驗證 `llm_svc.run` 內部的指令建構邏輯。

### Decision 4: Codex CLI command 結構

**選擇**：`--model` 以獨立旗標加到 command list，`effort` 透過 codex config override 機制傳遞：

```python
command = [_resolve_cli("codex"), "exec",
           "--dangerously-bypass-approvals-and-sandbox",
           "--skip-git-repo-check"]
if model:
    command.extend(["--model", model])
if effort:
    command.extend(["-c", f"model_reasoning_effort={effort}"])
```

**理由**：Codex CLI 不支援 `--effort` 旗標，effort level 是透過 config system (`-c model_reasoning_effort=<level>`) 設定。這是實測 codex CLI v0.140.0 確認的。`--model` 則與 Claude 分支模式一致。

## Risks / Trade-offs

- **[Low] codex CLI 的 --effort 旗標名稱可能變更** → 測試會立即捕捉到；`--effort` 是 codex CLI 的公開介面，變更機率低
- **[Low] --effort 對不支援的 target 為 silent no-op** → 使用者可能對 claude target 傳 `--effort xhigh` 但無效果。可在 future iteration 中加上 validation 或 warning
- **[None] 無破壞性變更** → 所有新增參數為 optional，預設值保持現有行為
