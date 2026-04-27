import logging
import time
from typing import Callable

from llm_eval import llm_svc
from llm_eval.job import JobResult, Outcome
from llm_eval.llm_target import LLMTarget
from llm_eval.prompt_builder import build_prompt
from llm_eval.status_resolver import resolve
from llm_eval.workspace import cleanup_workspace, create_workspace

__all__ = ["evaluate", "Outcome", "JobResult"]

logger = logging.getLogger(__name__)


def evaluate(
    target: str,
    purpose: str,
    outcomes: list[Outcome],
    *,
    on_exception: Callable[[Exception], None] | None = None,
    model: str | None = None,
    timeout: float = 1800,
    cwd: str | None = None,
) -> None:
    try:
        llm_target = LLMTarget(target)
    except ValueError:
        valid = [t.value for t in LLMTarget]
        raise ValueError(f"Unsupported target {target!r}. Valid: {valid}")

    prompt = build_prompt(purpose, outcomes)
    job_id, workspace = create_workspace(cwd)
    start = time.monotonic()

    try:
        stdout = llm_svc.run_once(
            llm_target,
            prompt,
            model=model,
            cwd=str(workspace),
            timeout=timeout,
        )
    except Exception as exc:
        cleanup_workspace(workspace)
        if on_exception is not None:
            on_exception(exc)
            return
        raise

    duration = time.monotonic() - start

    try:
        matched_outcome, result = resolve(
            workspace=workspace,
            outcomes=outcomes,
            job_id=job_id,
            target=target,
            duration_seconds=duration,
            stdout=stdout,
        )
    except Exception as exc:
        cleanup_workspace(workspace)
        if on_exception is not None:
            on_exception(exc)
            return
        raise

    try:
        matched_outcome.callback(result)
    finally:
        cleanup_workspace(workspace)
