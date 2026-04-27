from pathlib import Path
from llm_eval.workspace import create_workspace, cleanup_workspace


def test_create_workspace_returns_job_id_and_path(tmp_path):
    job_id, ws = create_workspace(str(tmp_path))
    assert isinstance(job_id, str)
    assert len(job_id) == 8
    assert ws.exists()
    assert ws.is_dir()


def test_workspace_path_contains_job_id(tmp_path):
    job_id, ws = create_workspace(str(tmp_path))
    assert job_id in str(ws)


def test_workspace_nested_under_llm_eval(tmp_path):
    _, ws = create_workspace(str(tmp_path))
    assert ws.parent.name == ".llm_eval"


def test_create_workspace_uses_cwd_when_base_dir_none(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _, ws = create_workspace(None)
    assert ws.exists()
    cleanup_workspace(ws)


def test_cleanup_removes_workspace(tmp_path):
    _, ws = create_workspace(str(tmp_path))
    cleanup_workspace(ws)
    assert not ws.exists()


def test_cleanup_ignores_missing_directory(tmp_path):
    ws = tmp_path / "nonexistent"
    cleanup_workspace(ws)  # must not raise


def test_two_calls_produce_different_job_ids(tmp_path):
    id1, ws1 = create_workspace(str(tmp_path))
    id2, ws2 = create_workspace(str(tmp_path))
    assert id1 != id2
    cleanup_workspace(ws1)
    cleanup_workspace(ws2)
