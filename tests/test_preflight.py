from unittest.mock import MagicMock, patch
import subprocess
import pytest

from llm_eval.preflight import TargetStatus, _check_codex, check_target
from llm_eval.llm_target import LLMTarget


def _make_proc(returncode=0, stdout="", stderr=""):
    proc = MagicMock()
    proc.returncode = returncode
    proc.stdout = stdout
    proc.stderr = stderr
    return proc


class TestCheckCodex:
    def test_ok_when_logged_in(self):
        with patch("subprocess.run", return_value=_make_proc(stdout="Logged in using ChatGPT")):
            result = _check_codex()
        assert result.ok is True
        assert result.reason is None

    def test_fail_when_not_logged_in(self):
        with patch("subprocess.run", return_value=_make_proc(stdout="Not logged in")):
            result = _check_codex()
        assert result.ok is False
        assert "Not logged in" in result.reason

    def test_fail_when_returncode_nonzero(self):
        with patch("subprocess.run", return_value=_make_proc(returncode=1, stderr="auth error")):
            result = _check_codex()
        assert result.ok is False
        assert "auth error" in result.reason

    def test_fail_when_cli_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _check_codex()
        assert result.ok is False
        assert "not found on PATH" in result.reason

    def test_fail_when_timeout(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("codex", 15)):
            result = _check_codex()
        assert result.ok is False
        assert "timed out" in result.reason

    def test_fail_on_unexpected_exception(self):
        with patch("subprocess.run", side_effect=OSError("permission denied")):
            result = _check_codex()
        assert result.ok is False
        assert "permission denied" in result.reason

    def test_reason_truncated_to_200_chars(self):
        long_msg = "x" * 300
        with patch("subprocess.run", return_value=_make_proc(returncode=1, stderr=long_msg)):
            result = _check_codex()
        assert len(result.reason) <= 200

    def test_uses_correct_command(self):
        with patch("subprocess.run", return_value=_make_proc(stdout="Logged in using ChatGPT")) as mock_run:
            _check_codex()
        args = mock_run.call_args[0][0]
        assert args[1:] == ["login", "status"]

    def test_check_target_dispatches_to_codex_checker(self):
        sentinel = TargetStatus(ok=True)
        mock_checker = MagicMock(return_value=sentinel)
        with patch.dict("llm_eval.preflight._CHECKERS", {LLMTarget.CODEX: mock_checker}):
            result = check_target(LLMTarget.CODEX)
        mock_checker.assert_called_once()
        assert result is sentinel
