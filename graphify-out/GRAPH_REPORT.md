# Graph Report - .  (2026-04-27)

## Corpus Check
- Corpus is ~1,265 words - fits in a single context window. You may not need a graph.

## Summary
- 41 nodes · 60 edges · 9 communities detected
- Extraction: 68% EXTRACTED · 32% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.71)
- Token cost: 3,200 input · 1,850 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Quota Resilience Logic|Quota Resilience Logic]]
- [[_COMMUNITY_FastAPI Request Handling|FastAPI Request Handling]]
- [[_COMMUNITY_LLM Target Enum|LLM Target Enum]]
- [[_COMMUNITY_Service Framework & Dependencies|Service Framework & Dependencies]]
- [[_COMMUNITY_Codex Workspace Management|Codex Workspace Management]]
- [[_COMMUNITY_Target Availability Checks|Target Availability Checks]]
- [[_COMMUNITY_OpenCode Integration|OpenCode Integration]]
- [[_COMMUNITY_Agent Module Init|Agent Module Init]]
- [[_COMMUNITY_HTTP Client Dependency|HTTP Client Dependency]]

## God Nodes (most connected - your core abstractions)
1. `LLMTarget` - 17 edges
2. `run_once()` - 10 edges
3. `CLI Credential Directory Map` - 6 edges
4. `_is_quota_error()` - 4 edges
5. `_resolve_cli()` - 4 edges
6. `FastAPI LLM Service App` - 4 edges
7. `POST /invoke Endpoint` - 4 edges
8. `GET /health Endpoint` - 4 edges
9. `InvokeRequest` - 3 edges
10. `_get_codex_workspace()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `llm_image/main.py  FastAPI service that wraps framework.llm_agent.llm_svc.run_on` --uses--> `LLMTarget`  [INFERRED]
  main.py → llm_agent\llm_target.py
- `Invoke a LLM target and return its output.      Returns:         200: { "output"` --uses--> `LLMTarget`  [INFERRED]
  main.py → llm_agent\llm_target.py
- `Report service health and which LLM targets are available.      A CLI target is` --uses--> `LLMTarget`  [INFERRED]
  main.py → llm_agent\llm_target.py
- `_resolve_cli()` --semantically_similar_to--> `.llm_io Temp File I/O Pattern`  [INFERRED] [semantically similar]
  llm_agent\llm_svc.py → llm_agent/llm_svc.py
- `framework/llm_agent/llm_svc.py  (llm_image copy)  Single entry-point for calling` --uses--> `LLMTarget`  [INFERRED]
  llm_agent\llm_svc.py → llm_agent\llm_target.py

## Hyperedges (group relationships)
- **LLM Invocation Dispatch Pipeline** — main_invoke_endpoint, llm_svc_run_once, llm_target_llmtarget [EXTRACTED 0.95]
- **Quota Exhaustion Resilience Pattern** — llm_svc_quota_error_patterns, llm_svc_is_quota_error, llm_svc_quota_retry_logic [EXTRACTED 0.95]
- **Target Availability Health Check Pattern** — main_health_endpoint, main_cli_cred_dirs, main_api_key_checks [EXTRACTED 0.90]

## Communities

### Community 0 - "Quota Resilience Logic"
Cohesion: 0.31
Nodes (9): .llm_io Temp File I/O Pattern, _is_quota_error(), Opencode JSON Stream Parser, _QUOTA_ERROR_PATTERNS — Regex List, Quota Retry Loop Logic, Invoke a CLI-based LLM agent and return its stdout as a string.      Args:, Resolve CLI binary path, preferring .cmd on Windows., _resolve_cli() (+1 more)

### Community 1 - "FastAPI Request Handling"
Cohesion: 0.25
Nodes (7): BaseModel, health(), invoke(), InvokeRequest, llm_image/main.py  FastAPI service that wraps framework.llm_agent.llm_svc.run_on, Report service health and which LLM targets are available.      A CLI target is, Invoke a LLM target and return its output.      Returns:         200: { "output"

### Community 2 - "LLM Target Enum"
Cohesion: 0.4
Nodes (5): Enum, LLMTarget.CODEX, LLMTarget.COPILOT, LLMTarget.GEMINI, LLMTarget

### Community 3 - "Service Framework & Dependencies"
Cohesion: 0.33
Nodes (6): FastAPI LLM Service App, POST /invoke Endpoint, InvokeRequest Pydantic Model, fastapi==0.135.1 Dependency, pydantic==2.12.5 Dependency, uvicorn==0.42.0 Dependency

### Community 4 - "Codex Workspace Management"
Cohesion: 0.67
Nodes (3): _ensure_codex_trusted(), _get_codex_workspace(), framework/llm_agent/llm_svc.py  (llm_image copy)  Single entry-point for calling

### Community 5 - "Target Availability Checks"
Cohesion: 0.67
Nodes (4): LLMTarget.CLAUDE, API Key Environment Variable Check Map, CLI Credential Directory Map, GET /health Endpoint

### Community 6 - "OpenCode Integration"
Cohesion: 1.0
Nodes (2): _ALLOW_ALL_OPENCODE_PERMISSION — Opencode Permission Map, LLMTarget.OPENCODE

### Community 7 - "Agent Module Init"
Cohesion: 1.0
Nodes (0): 

### Community 8 - "HTTP Client Dependency"
Cohesion: 1.0
Nodes (1): httpx==0.28.1 Dependency

## Knowledge Gaps
- **6 isolated node(s):** `Opencode JSON Stream Parser`, `LLMTarget.COPILOT`, `fastapi==0.135.1 Dependency`, `uvicorn==0.42.0 Dependency`, `httpx==0.28.1 Dependency` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `OpenCode Integration`** (2 nodes): `_ALLOW_ALL_OPENCODE_PERMISSION — Opencode Permission Map`, `LLMTarget.OPENCODE`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Agent Module Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HTTP Client Dependency`** (1 nodes): `httpx==0.28.1 Dependency`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMTarget` connect `LLM Target Enum` to `Quota Resilience Logic`, `FastAPI Request Handling`, `Service Framework & Dependencies`, `Codex Workspace Management`, `Target Availability Checks`, `OpenCode Integration`?**
  _High betweenness centrality (0.598) - this node is a cross-community bridge._
- **Why does `run_once()` connect `Quota Resilience Logic` to `LLM Target Enum`, `Service Framework & Dependencies`, `Codex Workspace Management`, `OpenCode Integration`?**
  _High betweenness centrality (0.288) - this node is a cross-community bridge._
- **Why does `POST /invoke Endpoint` connect `Service Framework & Dependencies` to `Quota Resilience Logic`, `LLM Target Enum`?**
  _High betweenness centrality (0.167) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `LLMTarget` (e.g. with `InvokeRequest` and `llm_image/main.py  FastAPI service that wraps framework.llm_agent.llm_svc.run_on`) actually correct?**
  _`LLMTarget` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `CLI Credential Directory Map` (e.g. with `LLMTarget.CLAUDE` and `LLMTarget.GEMINI`) actually correct?**
  _`CLI Credential Directory Map` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Opencode JSON Stream Parser`, `LLMTarget.COPILOT`, `fastapi==0.135.1 Dependency` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._