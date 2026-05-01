import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable

from llm_eval.llm_target import LLMTarget


@dataclass(frozen=True)
class TargetStatus:
    ok: bool
    reason: str | None = None


def _resolve_cli(command_name: str) -> str:
    if os.name == "nt":
        cmd_candidate = shutil.which(f"{command_name}.cmd")
        if cmd_candidate:
            return cmd_candidate
    resolved = shutil.which(command_name)
    return resolved if resolved else command_name


def _check_claude() -> TargetStatus:
    binary = _resolve_cli("claude")
    try:
        result = subprocess.run(
            [binary, "auth", "status", "--json"],
            capture_output=True, text=True, timeout=15, input="",
        )
        if result.returncode == 0 and '"loggedIn": true' in result.stdout:
            return TargetStatus(ok=True)
        reason = result.stderr.strip() or result.stdout.strip() or "loggedIn not true"
        return TargetStatus(ok=False, reason=reason[:200])
    except FileNotFoundError:
        return TargetStatus(ok=False, reason="claude CLI not found on PATH")
    except subprocess.TimeoutExpired:
        return TargetStatus(ok=False, reason="claude auth status timed out")
    except Exception as e:
        return TargetStatus(ok=False, reason=str(e)[:200])


def _check_codex() -> TargetStatus:
    binary = _resolve_cli("codex")
    try:
        result = subprocess.run(
            [binary, "login", "status"],
            capture_output=True, text=True, timeout=15, input="",
        )
        if result.returncode == 0 and "Logged in" in result.stdout:
            return TargetStatus(ok=True)
        reason = result.stderr.strip() or result.stdout.strip() or "not logged in"
        return TargetStatus(ok=False, reason=reason[:200])
    except FileNotFoundError:
        return TargetStatus(ok=False, reason="codex CLI not found on PATH")
    except subprocess.TimeoutExpired:
        return TargetStatus(ok=False, reason="codex login status timed out")
    except Exception as e:
        return TargetStatus(ok=False, reason=str(e)[:200])


def _check_via_version(tool: str) -> TargetStatus:
    binary = _resolve_cli(tool)
    try:
        result = subprocess.run(
            [binary, "--version"],
            capture_output=True, text=True, timeout=15, input="",
        )
        if result.returncode == 0:
            return TargetStatus(ok=True)
        reason = (result.stderr or result.stdout or "non-zero exit").strip()
        return TargetStatus(ok=False, reason=reason[:200])
    except FileNotFoundError:
        return TargetStatus(ok=False, reason=f"{tool} CLI not found on PATH")
    except subprocess.TimeoutExpired:
        return TargetStatus(ok=False, reason=f"{tool} --version timed out")
    except Exception as e:
        return TargetStatus(ok=False, reason=str(e)[:200])


_CHECKERS: dict[LLMTarget, Callable[[], TargetStatus]] = {
    LLMTarget.CLAUDE:   _check_claude,
    LLMTarget.GEMINI:   lambda: _check_via_version("gemini"),
    LLMTarget.CODEX:    _check_codex,
    LLMTarget.OPENCODE: lambda: _check_via_version("opencode"),
    LLMTarget.COPILOT:  lambda: _check_via_version("copilot"),
}


def check_target(target: LLMTarget) -> TargetStatus:
    """Check whether a single LLM target's CLI is installed and authenticated."""
    return _CHECKERS[target]()


def check_all() -> dict[LLMTarget, TargetStatus]:
    """Check all known LLM targets. Always runs live; no caching."""
    return {target: checker() for target, checker in _CHECKERS.items()}
