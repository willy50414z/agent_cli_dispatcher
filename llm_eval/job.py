from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Outcome:
    status: str
    description: str
    callback: Callable[["JobResult"], None]
    output_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class JobResult:
    job_id: str
    status: str
    target: str
    duration_seconds: float
    files: dict[str, str]
    stdout: str
