import logging
import time
from pathlib import Path
from typing import Callable, Union

from llm_eval import llm_svc
from llm_eval.job import JobResult, Outcome
from llm_eval.llm_svc import LLMEvaluationError
from llm_eval.llm_target import LLMTarget, parse_targets
from llm_eval.preflight import TargetStatus, check_all, check_target
from llm_eval.prompt_builder import build_prompt
from llm_eval.status_resolver import resolve
from llm_eval.workspace import cleanup_workspace, create_workspace

__all__ = ["evaluate", "run", "Outcome", "JobResult", "LLMTarget", "LLMEvaluationError",
           "check_target", "check_all", "TargetStatus", "parse_targets"]

logger = logging.getLogger(__name__)


def evaluate(
    target: LLMTarget | None,
    purpose: Union[str, Callable[[Path], str]],
    outcomes: list[Outcome],
    *,
    targets: list[LLMTarget] | None = None,
    on_exception: Callable[[Exception], None] | None = None,
    model: str | None = None,
    timeout: float = 1800,
    cwd: str | None = None,
) -> None:
    """Run an LLM evaluation against one or more targets.

    Pass ``targets`` (list) to enable ordered fallback: each target is tried in
    sequence and the next is used only when the previous raises LLMEvaluationError.
    Pass ``target`` (single) for the original single-target behaviour.
    Providing both raises ValueError; providing neither raises ValueError.

    ``purpose`` may be a plain string or a callable that receives the workspace
    Path and returns a string. Use the callable form when the prompt must embed
    the workspace path as the LLM output directory so that resolve() can find
    the files written by the LLM.
    """
    if targets is not None and target is not None:
        raise ValueError("Provide either 'target' or 'targets', not both.")
    _targets: list[LLMTarget] = targets if targets is not None else ([target] if target is not None else [])
    if not _targets:
        raise ValueError("evaluate() requires 'target' or 'targets'.")
    if not outcomes:
        raise ValueError("outcomes must not be empty.")

    job_id, workspace = create_workspace(cwd)
    purpose_str = purpose(workspace) if callable(purpose) else purpose
    prompt = build_prompt(purpose_str, outcomes, workspace=workspace)
    start = time.monotonic()

    try:
        stdout, winning_target = _run_with_fallback(
            _targets, prompt, model=model, cwd=str(workspace), timeout=timeout
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
            target=winning_target.value,
            duration_seconds=duration,
            stdout=stdout,
        )
    except Exception as exc:
        cleanup_workspace(workspace)
        if on_exception is not None:
            on_exception(exc)
            return
        raise

    # Callback exceptions are intentionally NOT caught here — they originate from
    # business logic, not the LLM layer, and must propagate directly to the caller.
    try:
        matched_outcome.callback(result)
    finally:
        cleanup_workspace(workspace)


def run(
    target: LLMTarget | None = None,
    prompt: str = "",
    *,
    targets: list[LLMTarget] | None = None,
    model: str | None = None,
    timeout: float = 1800,
    cwd: str | None = None,
) -> str:
    """Run a raw LLM prompt and return stdout without outcome routing."""
    if targets is not None and target is not None:
        raise ValueError("Provide either 'target' or 'targets', not both.")
    _targets: list[LLMTarget] = targets if targets is not None else ([target] if target is not None else [])
    if not _targets:
        raise ValueError("run() requires 'target' or 'targets'.")
    if len(_targets) == 1:
        return llm_svc.run(_targets[0], prompt, model=model, cwd=cwd, timeout=timeout)
    return llm_svc.run_with_fallback(_targets, prompt, model=model, cwd=cwd, timeout=timeout)


def _run_with_fallback(
    targets: list[LLMTarget],
    prompt: str,
    *,
    model: str | None = None,
    cwd: str | None = None,
    timeout: float = 1800,
) -> tuple[str, LLMTarget]:
    """Try each target in order; return (stdout, winning_target) on first success."""
    last_exc: llm_svc.LLMEvaluationError | None = None
    for t in targets:
        try:
            return llm_svc.run(t, prompt, model=model, cwd=cwd, timeout=timeout), t
        except llm_svc.LLMEvaluationError as exc:
            logger.warning("evaluate fallback: %s failed, trying next. error: %s", t.value, exc)
            last_exc = exc
    raise last_exc  # type: ignore[misc]
