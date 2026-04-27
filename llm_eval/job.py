from dataclasses import dataclass
from typing import Callable


@dataclass
class Outcome:
    status: str
    description: str
    output_files: list[str]
    callback: Callable[["JobResult"], None]


@dataclass
class JobResult:
    job_id: str
    status: str
    target: str
    duration_seconds: float
    files: dict[str, str]
    stdout: str
