"""
llm_image/main.py

FastAPI service that wraps framework.llm_agent.llm_svc.run_once()
and exposes it over HTTP.

Endpoints:
    POST /invoke  — invoke a LLM target, return { "output": "..." }
    GET  /health  — report available targets based on credentials present
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from llm_agent.llm_svc import run_once
from llm_agent.llm_target import LLMTarget

logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Service", version="1.0.0")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class InvokeRequest(BaseModel):
    target: str
    prompt: str
    model: str | None = None
    cwd: str | None = None
    timeout: float | None = 1800


# ---------------------------------------------------------------------------
# POST /invoke
# ---------------------------------------------------------------------------

@app.post("/invoke")
def invoke(req: InvokeRequest):
    """
    Invoke a LLM target and return its output.

    Returns:
        200: { "output": "..." }
        422: unsupported target value
        500: CLI binary not found or execution error
    """
    try:
        target = LLMTarget(req.target)
    except ValueError:
        valid = [t.value for t in LLMTarget]
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported target: {req.target!r}. Valid values: {valid}",
        )

    logger.info("invoke target=%s cwd=%s", target.value, req.cwd)

    try:
        output = run_once(
            target,
            req.prompt,
            model=req.model,
            cwd=req.cwd,
            timeout=req.timeout,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"CLI binary not found for target {target.value!r}: {e}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"output": output}


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

# Mapping from LLMTarget to its required CLI credential directory inside the container
_CLI_CRED_DIRS: dict[str, Path] = {
    "claude":   Path("/root/.claude"),
    "gemini":   Path("/root/.gemini"),
    "codex":    Path("/root/.codex"),
    "opencode": Path("/root/.config/opencode"),  # opencode uses XDG config
}

# Mapping from display target name to required API key env var
_API_KEY_CHECKS: dict[str, str] = {
    "claude_api": "ANTHROPIC_API_KEY",
    "gemini_api": "GEMINI_API_KEY",
    "openai_api": "OPENAI_API_KEY",
}


@app.get("/health")
def health():
    """
    Report service health and which LLM targets are available.

    A CLI target is available when its credential directory exists.
    An API target is available when its API key env var is set.

    Returns:
        { "status": "ok", "available_targets": [...] }
    """
    available_targets: list[str] = []

    for target_name, cred_dir in _CLI_CRED_DIRS.items():
        if cred_dir.exists():
            available_targets.append(target_name)

    for target_name, env_var in _API_KEY_CHECKS.items():
        if os.getenv(env_var):
            available_targets.append(target_name)

    return {"status": "ok", "available_targets": available_targets}
