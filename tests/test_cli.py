import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from llm_eval import cli
from llm_eval.job import JobResult
from llm_eval.llm_svc import LLMEvaluationError
from llm_eval.llm_target import LLMTarget
from llm_eval.preflight import TargetStatus


def test_help_and_subcommand_help(capsys):
    assert cli.main(["--help"]) == 0
    assert "run" in capsys.readouterr().out

    assert cli.main(["run", "--help"]) == 0
    assert "--prompt" in capsys.readouterr().out

    assert cli.main(["evaluate", "--help"]) == 0
    assert "--outcome" in capsys.readouterr().out

    assert cli.main(["health", "--help"]) == 0
    assert "--json" in capsys.readouterr().out

    assert cli.main(["install_delegant", "--help"]) == 0
    out = capsys.readouterr().out
    assert "--mode" in out
    assert "--level" in out


def test_run_with_inline_prompt(capsys):
    with patch("llm_eval.cli.llm_eval.run", return_value="answer") as mock_run:
        assert cli.main(["run", "--target", "deepseek", "--prompt", "hello"]) == 0

    mock_run.assert_called_once_with(
        target=LLMTarget.DEEPSEEK,
        targets=None,
        prompt="hello",
        model=None,
        effort=None,
        timeout=1800,
        cwd=None,
    )
    assert capsys.readouterr().out == "answer"


def test_run_with_prompt_file(tmp_path, capsys):
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("from file", encoding="utf-8")

    with patch("llm_eval.cli.llm_eval.run", return_value="ok") as mock_run:
        assert cli.main(["run", "--target", "deepseek", "--prompt-file", str(prompt_file)]) == 0

    assert mock_run.call_args.kwargs["prompt"] == "from file"
    assert capsys.readouterr().out == "ok"


def test_run_with_stdin_prompt(monkeypatch, capsys):
    class FakeStdin:
        def read(self):
            return "from stdin"

    monkeypatch.setattr("sys.stdin", FakeStdin())
    with patch("llm_eval.cli.llm_eval.run", return_value="ok") as mock_run:
        assert cli.main(["run", "--target", "deepseek", "--stdin"]) == 0

    assert mock_run.call_args.kwargs["prompt"] == "from stdin"
    assert capsys.readouterr().out == "ok"


def test_evaluate_json_with_declared_outcomes(tmp_path, capsys):
    purpose_file = tmp_path / "purpose.md"
    purpose_file.write_text("do work", encoding="utf-8")

    def fake_execute(targets, purpose, outcomes, **kwargs):
        assert targets == [LLMTarget.DEEPSEEK]
        assert purpose == "do work"
        assert [o.status for o in outcomes] == ["complete", "failed"]
        return JobResult(
            job_id="abc12345",
            status="complete",
            target="deepseek",
            duration_seconds=1.25,
            files={},
            stdout="done",
        )

    with patch("llm_eval.cli._execute_evaluate", fake_execute):
        exit_code = cli.main(
            [
                "evaluate",
                "--target",
                "deepseek",
                "--purpose-file",
                str(purpose_file),
                "--outcome",
                "complete=Done",
                "--outcome",
                "failed=Failed",
                "--json",
            ]
        )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "status": "complete",
        "target": "deepseek",
        "duration_seconds": 1.25,
        "stdout": "done",
        "files": {},
    }


def test_evaluate_output_file_json_serialization(tmp_path, capsys):
    def fake_execute(targets, purpose, outcomes, **kwargs):
        assert outcomes[0].output_files == ["errors.txt"]
        return JobResult(
            job_id="abc12345",
            status="failed",
            target="deepseek",
            duration_seconds=2.0,
            files={"errors.txt": b"bad bytes: \xff"},
            stdout="",
        )

    with patch("llm_eval.cli._execute_evaluate", fake_execute):
        exit_code = cli.main(
            [
                "evaluate",
                "--target",
                "deepseek",
                "--purpose",
                "do work",
                "--outcome",
                "failed=Failed",
                "--output-file",
                "failed=errors.txt",
                "--json",
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "failed"
    assert payload["files"] == {"errors.txt": "bad bytes: �"}


def test_target_and_targets_are_mutually_exclusive(capsys):
    exit_code = cli.main(
        ["run", "--target", "deepseek", "--targets", "claude,deepseek", "--prompt", "hello"]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "not allowed with argument" in captured.err


def test_targets_are_parsed_in_order(capsys):
    with patch("llm_eval.cli.llm_eval.run", return_value="answer") as mock_run:
        assert cli.main(["run", "--targets", "claude,deepseek", "--prompt", "hello"]) == 0

    assert mock_run.call_args.kwargs["target"] is None
    assert mock_run.call_args.kwargs["targets"] == [LLMTarget.CLAUDE, LLMTarget.DEEPSEEK]
    assert capsys.readouterr().out == "answer"


def test_health_json_for_all_targets(capsys):
    statuses = {
        LLMTarget.CODEX: TargetStatus(ok=True),
        LLMTarget.DEEPSEEK: TargetStatus(ok=False, reason="missing token"),
    }

    with patch("llm_eval.cli.check_all", return_value=statuses):
        assert cli.main(["health", "--json"]) == 0

    assert json.loads(capsys.readouterr().out) == {
        "codex": {"ok": True, "reason": None},
        "deepseek": {"ok": False, "reason": "missing token"},
    }


def test_health_json_for_single_target(capsys):
    with patch("llm_eval.cli.check_target", return_value=TargetStatus(ok=True)) as mock_check:
        assert cli.main(["health", "--target", "codex", "--json"]) == 0

    mock_check.assert_called_once_with(LLMTarget.CODEX)
    assert json.loads(capsys.readouterr().out) == {"codex": {"ok": True, "reason": None}}


def test_missing_prompt_input_is_argument_error(capsys):
    exit_code = cli.main(["run", "--target", "deepseek"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "one of the arguments --prompt --prompt-file --stdin is required" in captured.err


def test_execution_failure_writes_stderr_only(capsys):
    with patch("llm_eval.cli.llm_eval.run", side_effect=LLMEvaluationError("target failed")):
        exit_code = cli.main(["run", "--target", "deepseek", "--prompt", "hello"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "target failed" in captured.err


# ---------------------------------------------------------------------------
# 1.1 Tests: --mode main, --mode hybrid, --mode delegated-apply
# ---------------------------------------------------------------------------


def test_install_delegant_mode_main_creates_guidance(tmp_path, capsys):
    exit_code = cli.main(["install_delegant", "--cwd", str(tmp_path), "--mode", "main"])

    assert exit_code == 0
    guidance = tmp_path / "AGENTS.md"
    assert guidance.exists()
    text = guidance.read_text(encoding="utf-8")
    assert "agent-dispatch:openspec-delegation:start" in text
    assert "Delegation mode: main" in text
    assert "no automatic submodel delegation" in text
    captured = capsys.readouterr()
    assert "Delegation mode: main" in captured.out
    assert "Scope: project-local" in captured.out


def test_install_delegant_mode_hybrid_creates_guidance(tmp_path, capsys):
    exit_code = cli.main(["install_delegant", "--cwd", str(tmp_path), "--mode", "hybrid"])

    assert exit_code == 0
    guidance = tmp_path / "AGENTS.md"
    assert guidance.exists()
    text = guidance.read_text(encoding="utf-8")
    assert "agent-dispatch:openspec-delegation:start" in text
    assert "Delegation mode: hybrid" in text
    assert "delegation-first apply for tagged work" in text
    assert "recommended delegation-first cost-control default" in text
    captured = capsys.readouterr()
    assert "Delegation mode: hybrid" in captured.out


def test_install_delegant_mode_delegated_apply_creates_guidance(tmp_path, capsys):
    exit_code = cli.main(
        ["install_delegant", "--cwd", str(tmp_path), "--mode", "delegated-apply"]
    )

    assert exit_code == 0
    guidance = tmp_path / "AGENTS.md"
    assert guidance.exists()
    text = guidance.read_text(encoding="utf-8")
    assert "agent-dispatch:openspec-delegation:start" in text
    assert "Delegation mode: delegated-apply" in text
    assert "full delegated apply with main-model verification" in text
    captured = capsys.readouterr()
    assert "Delegation mode: delegated-apply" in captured.out


# ---------------------------------------------------------------------------
# 1.2 Compatibility tests: --level → mode mapping
# ---------------------------------------------------------------------------


def test_install_delegant_level_1_maps_to_hybrid(tmp_path, capsys):
    exit_code = cli.main(["install_delegant", "--cwd", str(tmp_path), "--level", "1"])

    assert exit_code == 0
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Delegation mode: hybrid" in text
    captured = capsys.readouterr()
    assert "Delegation mode: hybrid" in captured.out


def test_install_delegant_level_2_maps_to_delegated_apply(tmp_path, capsys):
    exit_code = cli.main(["install_delegant", "--cwd", str(tmp_path), "--level", "2"])

    assert exit_code == 0
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Delegation mode: delegated-apply" in text
    captured = capsys.readouterr()
    assert "Delegation mode: delegated-apply" in captured.out


def test_install_delegant_same_mode_and_level_accepted(tmp_path):
    """--mode hybrid --level 1 are compatible (same effective mode)."""
    exit_code = cli.main(
        ["install_delegant", "--cwd", str(tmp_path), "--mode", "hybrid", "--level", "1"]
    )
    assert exit_code == 0
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Delegation mode: hybrid" in text


# ---------------------------------------------------------------------------
# 1.3 Conflict and non-interactive tests
# ---------------------------------------------------------------------------


def test_install_delegant_conflicting_mode_and_level_rejected(tmp_path, capsys):
    """--mode main --level 1 are incompatible (main vs hybrid)."""
    exit_code = cli.main(
        ["install_delegant", "--cwd", str(tmp_path), "--mode", "main", "--level", "1"]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "incompatible" in captured.err
    assert not (tmp_path / "AGENTS.md").exists()


def test_install_delegant_conflicting_mode_delegated_and_level_rejected(tmp_path, capsys):
    """--mode main --level 2 are incompatible (main vs delegated-apply)."""
    exit_code = cli.main(
        ["install_delegant", "--cwd", str(tmp_path), "--mode", "main", "--level", "2"]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "incompatible" in captured.err
    assert not (tmp_path / "AGENTS.md").exists()


def test_install_delegant_non_interactive_requires_mode(tmp_path, capsys):
    exit_code = cli.main(["install_delegant", "--cwd", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "requires --mode in non-interactive mode" in captured.err
    assert not (tmp_path / "AGENTS.md").exists()


def test_install_delegant_yes_uses_hybrid_default(tmp_path, capsys):
    assert cli.main(["install_delegant", "--cwd", str(tmp_path), "--yes"]) == 0

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Delegation mode: hybrid" in text
    captured = capsys.readouterr()
    assert "Delegation mode: hybrid" in captured.out


# ---------------------------------------------------------------------------
# Update / uninstall tests (using --mode)
# ---------------------------------------------------------------------------


def test_install_delegant_updates_existing_managed_block_in_place(tmp_path):
    guidance = tmp_path / "AGENTS.md"
    guidance.write_text("Existing guidance\n", encoding="utf-8")

    assert cli.main(["install_delegant", "--cwd", str(tmp_path), "--mode", "hybrid"]) == 0
    assert cli.main(
        ["install_delegant", "--cwd", str(tmp_path), "--mode", "delegated-apply"]
    ) == 0

    text = guidance.read_text(encoding="utf-8")
    assert text.count("agent-dispatch:openspec-delegation:start") == 1
    assert "Existing guidance" in text
    assert "Delegation mode: delegated-apply" in text
    assert "Delegation mode: hybrid" not in text


def test_install_delegant_uninstall_removes_managed_block(tmp_path):
    guidance = tmp_path / "AGENTS.md"
    guidance.write_text("Keep me\n", encoding="utf-8")
    assert cli.main(["install_delegant", "--cwd", str(tmp_path), "--mode", "hybrid"]) == 0

    assert cli.main(["install_delegant", "--cwd", str(tmp_path), "--uninstall"]) == 0

    text = guidance.read_text(encoding="utf-8")
    assert "Keep me" in text
    assert "agent-dispatch:openspec-delegation:start" not in text


def test_install_delegant_uninstall_when_not_installed(tmp_path, capsys):
    exit_code = cli.main(["install_delegant", "--cwd", str(tmp_path), "--uninstall"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "not-installed" in captured.out


# ---------------------------------------------------------------------------
# 3.3 Task-packet guidance assertions
# ---------------------------------------------------------------------------


def test_guidance_block_includes_task_packet_instructions(tmp_path):
    cli.main(["install_delegant", "--cwd", str(tmp_path), "--mode", "hybrid"])

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Propose-time task packets" in text
    assert "context" in text
    assert "output" in text
    assert "verify" in text
    assert "[delegate:test]" in text


def test_all_mode_guidance_blocks_include_task_packet_instructions(tmp_path):
    for mode in ("main", "hybrid", "delegated-apply"):
        cli.main(["install_delegant", "--cwd", str(tmp_path), "--mode", mode])

        text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "Propose-time task packets" in text, f"missing in mode {mode}"
        assert "context" in text, f"missing in mode {mode}"
        assert "output" in text, f"missing in mode {mode}"
        assert "verify" in text, f"missing in mode {mode}"
        assert "- [ ]" in text, f"missing checkbox in mode {mode}"


# ---------------------------------------------------------------------------
# Mode-specific guidance content assertions
# ---------------------------------------------------------------------------


def test_main_mode_guidance_disables_automatic_delegation(tmp_path):
    cli.main(["install_delegant", "--cwd", str(tmp_path), "--mode", "main"])

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "no automatic submodel delegation" in text
    assert "Do not delegate any apply tasks" in text


def test_hybrid_mode_guidance_lists_main_model_ownership(tmp_path):
    cli.main(["install_delegant", "--cwd", str(tmp_path), "--mode", "hybrid"])

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Main model owns" in text
    assert "OpenSpec artifact interpretation, scope, and architecture decisions" in text
    assert "Submodels are assigned" in text
    assert "Implementation drafts with clear file scope" in text
    assert "First-pass diff/spec review" in text


def test_hybrid_mode_guidance_requires_delegation_first_for_tagged_tasks(tmp_path):
    cli.main(["install_delegant", "--cwd", str(tmp_path), "--mode", "hybrid"])

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Hybrid mandatory delegation rules" in text
    assert "supersedes older guidance" in text
    assert "mandatory delegation-attempt tags, not" in text
    assert "During OpenSpec propose, Codex MUST call DeepSeek" in text
    assert "finalizing `proposal.md`, `design.md`, or `tasks.md`" in text
    assert "not just ask" in text
    assert "Codex MUST assign delegate-friendly implementation" in text
    assert "Codex MUST attempt delegation for every `[delegate:deepseek]`" in text
    assert "A valid apply-time delegation attempt means Codex actually invokes" in text
    assert "Do not skip a tagged delegate task merely because it is small" in text
    assert "Do not reinterpret tagged delegate tasks" in text
    assert "agent-dispatch run --target deepseek --prompt-file <packet>" in text


def test_delegated_apply_mode_guidance_requires_main_model_verification(tmp_path):
    cli.main(["install_delegant", "--cwd", str(tmp_path), "--mode", "delegated-apply"])

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "full delegated apply" in text
    assert "main-model verification" in text
    assert "The main model must" in text


# ---------------------------------------------------------------------------
# Interactive mode selection tests
# ---------------------------------------------------------------------------


def test_interactive_mode_selection_A_main(monkeypatch, tmp_path, capsys):
    inputs = iter(["A"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with patch.object(cli.sys.stdin, "isatty", return_value=True, create=True):
        assert cli.main(["install_delegant", "--cwd", str(tmp_path)]) == 0

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Delegation mode: main" in text
    captured = capsys.readouterr()
    assert "A) main" in captured.out


def test_interactive_mode_selection_B_hybrid(monkeypatch, tmp_path, capsys):
    inputs = iter(["B"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with patch.object(cli.sys.stdin, "isatty", return_value=True, create=True):
        assert cli.main(["install_delegant", "--cwd", str(tmp_path)]) == 0

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Delegation mode: hybrid" in text
    captured = capsys.readouterr()
    assert "B) hybrid" in captured.out


def test_interactive_mode_selection_C_delegated_apply(monkeypatch, tmp_path, capsys):
    inputs = iter(["C"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with patch.object(cli.sys.stdin, "isatty", return_value=True, create=True):
        assert cli.main(["install_delegant", "--cwd", str(tmp_path)]) == 0

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Delegation mode: delegated-apply" in text
    captured = capsys.readouterr()
    assert "C) delegated-apply" in captured.out


def test_interactive_mode_selection_lowercase_accepted(monkeypatch, tmp_path):
    inputs = iter(["b"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with patch.object(cli.sys.stdin, "isatty", return_value=True, create=True):
        assert cli.main(["install_delegant", "--cwd", str(tmp_path)]) == 0

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Delegation mode: hybrid" in text


def test_interactive_mode_selection_invalid_rejected(monkeypatch, tmp_path, capsys):
    inputs = iter(["X"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with patch.object(cli.sys.stdin, "isatty", return_value=True, create=True):
        exit_code = cli.main(["install_delegant", "--cwd", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "mode must be A, B, or C" in captured.err


# ---------------------------------------------------------------------------
# Integration tests: CLI → subprocess model/effort parameter passing
# ---------------------------------------------------------------------------


def _assert_sequence_in_list(expected: list[str], actual: list[str]) -> None:
    """Assert that expected items appear in actual list in order (subsequence)."""
    idx = 0
    for item in expected:
        try:
            idx = actual.index(item, idx)
        except ValueError:
            raise AssertionError(
                f"Expected {item!r} not found in {actual!r} at or after index {idx}"
            )


class TestModelEffortIntegration:
    """Verify CLI arguments reach subprocess.run with correct commands and env vars."""

    @pytest.mark.parametrize(
        "cli_args,expected_cmd_elems,expected_env,expected_stdin",
        [
            # 4.2: Claude target with --model claude-opus-4-8
            (
                ["run", "--target", "claude", "--model", "claude-opus-4-8", "--prompt", "hello"],
                ["claude", "--print", "--dangerously-skip-permissions", "--model", "claude-opus-4-8"],
                {},
                "hello",
            ),
            # 4.3: Codex target with --model gpt-5.5 --effort xhigh
            (
                ["run", "--target", "codex", "--model", "gpt-5.5", "--effort", "xhigh", "--prompt", "hello"],
                ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox",
                 "--skip-git-repo-check", "--model", "gpt-5.5", "-c", "model_reasoning_effort=xhigh"],
                {},
                "hello",
            ),
            # 4.4: Codex target with --model gpt-5.5 --effort high
            (
                ["run", "--target", "codex", "--model", "gpt-5.5", "--effort", "high", "--prompt", "hello"],
                ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox",
                 "--skip-git-repo-check", "--model", "gpt-5.5", "-c", "model_reasoning_effort=high"],
                {},
                "hello",
            ),
            # 4.5: DeepSeek target with --model deepseek-v4-pro[1m]
            (
                ["run", "--target", "deepseek", "--model", "deepseek-v4-pro[1m]", "--prompt", "hello"],
                ["claude", "--print", "--dangerously-skip-permissions", "--model", "deepseek-v4-pro[1m]"],
                {"ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
                 "ANTHROPIC_MODEL": "deepseek-v4-pro[1m]"},
                "hello",
            ),
            # 4.6: DeepSeek target without --model uses default
            (
                ["run", "--target", "deepseek", "--prompt", "hello"],
                ["claude", "--print", "--dangerously-skip-permissions"],
                {"ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
                 "ANTHROPIC_MODEL": "deepseek-v4-pro[1m]"},
                "hello",
            ),
        ],
    )
    def test_model_effort_passed_to_subprocess(
        self, tmp_path, capsys, monkeypatch,
        cli_args, expected_cmd_elems, expected_env, expected_stdin,
    ):
        """CLI model/effort args are forwarded to the correct subprocess command and env."""
        # DeepSeek requires DEEPSEEK_AUTH_TOKEN
        monkeypatch.setenv("DEEPSEEK_AUTH_TOKEN", "test-token")

        # Mock _resolve_cli to return bare command names (environment-independent)
        def _fake_resolve(name: str) -> str:
            return name

        mock_completed = MagicMock()
        mock_completed.returncode = 0
        mock_completed.stdout = "mock response"
        mock_completed.stderr = ""

        with patch("llm_eval.llm_svc._resolve_cli", side_effect=_fake_resolve):
            with patch("llm_eval.llm_svc.subprocess.run", return_value=mock_completed) as mock_run:
                exit_code = cli.main(cli_args + ["--cwd", str(tmp_path)])

        assert exit_code == 0
        assert capsys.readouterr().out == "mock response"

        mock_run.assert_called_once()
        actual_cmd = mock_run.call_args[0][0]
        _assert_sequence_in_list(expected_cmd_elems, actual_cmd)

        actual_env = mock_run.call_args.kwargs.get("env", {})
        for key, value in expected_env.items():
            assert actual_env.get(key) == value, f"env {key}: expected {value!r}, got {actual_env.get(key)!r}"

        assert mock_run.call_args.kwargs.get("input") == expected_stdin

    # 4.7: Prompt text passed as stdin to subprocess.run
    def test_prompt_passed_as_stdin(self, tmp_path, capsys):
        def _fake_resolve(name: str) -> str:
            return name

        mock_completed = MagicMock()
        mock_completed.returncode = 0
        mock_completed.stdout = "mock response"
        mock_completed.stderr = ""

        with patch("llm_eval.llm_svc._resolve_cli", side_effect=_fake_resolve):
            with patch("llm_eval.llm_svc.subprocess.run", return_value=mock_completed) as mock_run:
                exit_code = cli.main(
                    ["run", "--target", "claude", "--prompt", "hello world", "--cwd", str(tmp_path)]
                )

        assert exit_code == 0
        mock_run.assert_called_once()
        assert mock_run.call_args.kwargs.get("input") == "hello world"

    # 4.7 (additional): verify effort config not passed when omitted
    def test_codex_without_effort_omits_flag(self, tmp_path, capsys):
        def _fake_resolve(name: str) -> str:
            return name

        mock_completed = MagicMock()
        mock_completed.returncode = 0
        mock_completed.stdout = "mock response"
        mock_completed.stderr = ""

        with patch("llm_eval.llm_svc._resolve_cli", side_effect=_fake_resolve):
            with patch("llm_eval.llm_svc.subprocess.run", return_value=mock_completed) as mock_run:
                exit_code = cli.main(
                    ["run", "--target", "codex", "--prompt", "hello", "--cwd", str(tmp_path)]
                )

        assert exit_code == 0
        actual_cmd = mock_run.call_args[0][0]
        assert "model_reasoning_effort" not in str(actual_cmd)
        assert "--model" not in actual_cmd
