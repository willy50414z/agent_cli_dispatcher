import json
import logging
import os
import re
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from llm_eval.llm_target import LLMTarget

logger = logging.getLogger(__name__)


class LLMEvaluationError(RuntimeError):
    """LLM subprocess failure: non-zero exit, quota exhaustion, timeout, or execution error."""

_QUOTA_ERROR_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"exceeded your monthly token limit",
        r"exceeded your current quota",
        r"insufficient.quota",
        r"quota.exceeded",
        r"billing hard limit",
        r"credit balance is too low",
        r"out of credits",
        r"rate.limit.exceeded",
        r"429",
        r"payment required",
    ]
]

_QUOTA_RETRY_INTERVAL_SECONDS: int = int(os.getenv("LLM_QUOTA_RETRY_INTERVAL", "300"))
_QUOTA_MAX_RETRIES: int = int(os.getenv("LLM_QUOTA_MAX_RETRIES", "288"))

_ALLOW_ALL_OPENCODE_PERMISSION = {
    "bash": "allow", "read": "allow", "edit": "allow", "task": "allow",
    "glob": "allow", "grep": "allow", "list": "allow",
    "external_directory": "allow", "todowrite": "allow", "todoread": "allow",
    "question": "allow", "webfetch": "allow", "websearch": "allow",
    "codesearch": "allow", "lsp": "allow", "doom_loop": "allow", "skill": "allow",
}


def _is_quota_error(text: str) -> bool:
    for pattern in _QUOTA_ERROR_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _resolve_cli(command_name: str) -> str:
    if os.name == "nt":
        cmd_candidate = shutil.which(f"{command_name}.cmd")
        if cmd_candidate:
            return cmd_candidate
    resolved = shutil.which(command_name)
    return resolved if resolved else command_name


def run(
    target: LLMTarget,
    prompt: str,
    *,
    model: str | None = None,
    cwd: str | None = None,
    timeout: float | None = 1800,
    encoding: str = "utf-8",
    quota_retry_interval: int | None = None,
    quota_max_retries: int | None = None,
) -> str:
    if not prompt.strip():
        raise ValueError("prompt must not be empty.")

    _retry_interval = quota_retry_interval if quota_retry_interval is not None else _QUOTA_RETRY_INTERVAL_SECONDS
    _max_retries    = quota_max_retries    if quota_max_retries    is not None else _QUOTA_MAX_RETRIES

    work_dir = str(Path(cwd).resolve()) if cwd else None
    effective_dir = work_dir or str(Path.cwd())

    run_id = uuid.uuid4().hex[:8]
    io_dir = Path(effective_dir) / ".llm_io"
    io_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = io_dir / f"prompt_{run_id}.txt"
    output_file = io_dir / f"output_{run_id}.txt"
    prompt_file.write_text(prompt, encoding=encoding)

    stdin_input: str = ""
    env = dict(os.environ)

    try:
        if target == LLMTarget.CLAUDE:
            command = [_resolve_cli("claude"), "--print", "--dangerously-skip-permissions"]
            if model:
                command.extend(["--model", model])
            stdin_input = prompt_file.read_text(encoding=encoding)

        elif target == LLMTarget.GEMINI:
            command = [_resolve_cli("gemini"), "--approval-mode", "auto_edit",
                       "--prompt", prompt_file.read_text(encoding=encoding)]

        elif target == LLMTarget.CODEX:
            command = [_resolve_cli("codex"), "exec", "--dangerously-bypass-approvals-and-sandbox",
                       prompt_file.read_text(encoding=encoding).strip().replace("\n", " ")]

        elif target == LLMTarget.OPENCODE:
            env.setdefault("OPENCODE_PERMISSION", json.dumps(_ALLOW_ALL_OPENCODE_PERMISSION))
            runtime_root = Path(effective_dir).resolve() / "data" / "tool-runtime" / "opencode"
            for subdir in ("config", "data", "state"):
                (runtime_root / subdir).mkdir(parents=True, exist_ok=True)
            env.setdefault("XDG_CONFIG_HOME", str(runtime_root / "config"))
            env.setdefault("XDG_DATA_HOME",   str(runtime_root / "data"))
            env.setdefault("XDG_STATE_HOME",  str(runtime_root / "state"))
            command = [_resolve_cli("opencode"), "run",
                       "--dir", effective_dir, "--format", "json", "-"]
            stdin_input = prompt_file.read_text(encoding=encoding)

        elif target == LLMTarget.COPILOT:
            command = [_resolve_cli("copilot"), "-p", prompt_file.read_text(encoding=encoding),
                       "--allow-all", "--no-ask-user", "--output-format", "text", "--silent",
                       "--add-dir", effective_dir]
            if model:
                command.extend(["--model", model])

        else:
            raise ValueError(f"Unsupported LLM target: {target}")

        logger.info("run [%s] cwd=%s", target.value, work_dir or "(inherit)")
        logger.debug("run [%s] command=%s", target.value, command)
        logger.debug("run [%s] prompt_file=%s\n%s", target.value, prompt_file, prompt)

        completed = None
        for quota_attempt in range(_max_retries + 1):
            try:
                completed = subprocess.run(
                    command,
                    input=stdin_input,
                    capture_output=True,
                    text=True,
                    encoding=encoding,
                    cwd=work_dir,
                    env=env,
                    timeout=timeout,
                )
            except LLMEvaluationError:
                raise
            except Exception as e:
                logger.error("execute cmd exception: %s", e)
                raise LLMEvaluationError(f"{target.value} subprocess error: {e}") from e

            if completed.returncode != 0:
                stderr = (completed.stderr or "").strip()
                stdout = (completed.stdout or "").strip()
                parts = [s for s in [stderr, stdout] if s]
                detail = "\n".join(parts) if parts else "(no output)"

                if _is_quota_error(detail):
                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    logger.warning(
                        "[QUOTA EXHAUSTED] %s | attempt=%d/%d | Retrying in %ds. Detail: %s",
                        target.value, quota_attempt + 1, _max_retries, _retry_interval, detail[:300],
                    )
                    if quota_attempt < _max_retries:
                        time.sleep(_retry_interval)
                        continue
                    raise LLMEvaluationError(
                        f"{target.value} quota exhausted after {_max_retries} retries. "
                        f"Last error: {detail[:300]}"
                    )

                raise LLMEvaluationError(
                    f"{target.value} CLI failed (exit {completed.returncode}): {detail[:500]}"
                )

            break

        raw_stdout = (completed.stdout or "").strip()

        if target == LLMTarget.OPENCODE and raw_stdout:
            try:
                chunks = []
                for line in raw_stdout.splitlines():
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if event.get("type") == "error":
                        msg = (event.get("error") or {}).get("data", {}).get("message", "")
                        raise RuntimeError(str(msg))
                    message = event.get("message")
                    if isinstance(message, dict):
                        for item in (message.get("content") or []):
                            if isinstance(item, dict) and item.get("type") == "text":
                                chunks.append(str(item["text"]))
                if chunks:
                    raw_stdout = "\n".join(chunks).strip()
            except json.JSONDecodeError:
                pass

        logger.info("run [%s] done. stdout_len=%d", target.value, len(raw_stdout))
        output_file.write_text(raw_stdout, encoding=encoding)
        return output_file.read_text(encoding=encoding)

    finally:
        prompt_file.unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)


def run_with_fallback(
    targets: list[LLMTarget],
    prompt: str,
    *,
    model: str | None = None,
    cwd: str | None = None,
    timeout: float | None = 1800,
    encoding: str = "utf-8",
) -> str:
    if not targets:
        raise ValueError("targets must not be empty")
    last_exc: LLMEvaluationError | None = None
    for target in targets:
        try:
            return run(target, prompt, model=model, cwd=cwd, timeout=timeout, encoding=encoding)
        except LLMEvaluationError as exc:
            logger.warning("run_with_fallback: %s failed, trying next. error: %s", target.value, exc)
            last_exc = exc
    raise last_exc
