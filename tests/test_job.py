from llm_eval.job import Outcome, JobResult, effective_status


def test_outcome_stores_fields():
    called = []
    cb = lambda r: called.append(r)
    o = Outcome(
        description="All good",
        callback=cb,
        status="complete",
        output_files=["notes.txt"],
    )
    assert o.status == "complete"
    assert o.description == "All good"
    assert o.output_files == ["notes.txt"]
    assert o.callback is cb


def test_outcome_defaults_status_and_output_files_to_none():
    o = Outcome(description="fine", callback=lambda r: None)
    assert o.status is None
    assert o.output_files is None


def test_outcome_accepts_explicit_output_files_list():
    o = Outcome(description="fine", callback=lambda r: None, output_files=[])
    assert o.output_files == []


def test_effective_status_uses_status_when_set():
    o = Outcome("done", lambda r: None, status="complete")
    assert effective_status(o, 0) == "complete"


def test_effective_status_falls_back_to_index():
    o = Outcome("done", lambda r: None)
    assert effective_status(o, 0) == "0"
    assert effective_status(o, 3) == "3"


def test_job_result_stores_all_fields():
    r = JobResult(
        job_id="abc123",
        status="complete",
        target="claude",
        duration_seconds=3.5,
        files={"notes.txt": "hello"},
        stdout="raw output",
    )
    assert r.job_id == "abc123"
    assert r.status == "complete"
    assert r.target == "claude"
    assert r.duration_seconds == 3.5
    assert r.files == {"notes.txt": "hello"}
    assert r.stdout == "raw output"
