import logging
from pathlib import Path

from llm_eval.job import JobResult, Outcome, effective_status

logger = logging.getLogger(__name__)


def resolve(
    workspace: Path,
    outcomes: list[Outcome],
    job_id: str,
    target: str,
    duration_seconds: float,
    stdout: str,
) -> tuple[Outcome, JobResult]:
    status_files = sorted(workspace.glob("status_*"))

    if len(status_files) > 1:
        logger.warning(
            "Multiple status files found: %s. Using %s.",
            [p.name for p in status_files],
            status_files[0].name,
        )

    if not status_files:
        error_outcome = next(
            (o for i, o in enumerate(outcomes) if effective_status(o, i) == "error"),
            None,
        )
        if error_outcome is None:
            raise RuntimeError(
                "No status file created by LLM and no 'error' outcome defined."
            )
        matched = error_outcome
        status_name = "error"
    else:
        status_name = status_files[0].name[len("status_"):]
        matched = next(
            (o for i, o in enumerate(outcomes) if effective_status(o, i) == status_name),
            None,
        )
        if matched is None:
            raise RuntimeError(
                f"Status file 'status_{status_name}' does not match any defined outcome."
            )

    if matched.output_files is not None:
        missing = [f for f in matched.output_files if not (workspace / f).exists()]
        if missing:
            raise RuntimeError(
                f"Outcome '{status_name}' declared output_files {missing} "
                "but LLM did not create them."
            )

    files: dict[str, str] = {
        path.name: path.read_text(encoding="utf-8")
        for path in workspace.iterdir()
        if path.is_file() and not path.name.startswith("status_")
    }

    result = JobResult(
        job_id=job_id,
        status=status_name,
        target=target,
        duration_seconds=duration_seconds,
        files=files,
        stdout=stdout,
    )
    return matched, result
