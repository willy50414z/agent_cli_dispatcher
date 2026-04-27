import shutil
import uuid
from pathlib import Path


def create_workspace(base_dir: str | None) -> tuple[str, Path]:
    job_id = uuid.uuid4().hex[:8]
    base = Path(base_dir) if base_dir else Path.cwd()
    workspace = base / ".llm_eval" / job_id
    workspace.mkdir(parents=True, exist_ok=True)
    return job_id, workspace


def cleanup_workspace(workspace: Path) -> None:
    shutil.rmtree(workspace, ignore_errors=True)
