from llm_eval.job import Outcome, JobResult


def test_outcome_stores_fields():
    called = []
    cb = lambda r: called.append(r)
    o = Outcome(
        status="complete",
        description="All good",
        output_files=["notes.txt"],
        callback=cb,
    )
    assert o.status == "complete"
    assert o.description == "All good"
    assert o.output_files == ["notes.txt"]
    assert o.callback is cb


def test_outcome_default_output_files_is_empty():
    o = Outcome(status="ok", description="fine", output_files=[], callback=lambda r: None)
    assert o.output_files == []


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
