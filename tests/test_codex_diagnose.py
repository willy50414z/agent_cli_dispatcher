"""
Diagnostic integration tests for the codex CLI.

These tests call the real codex binary (no mocking) to expose the root cause
of codex execution failures.  Run with:

    pytest tests/test_codex_diagnose.py -v -s

Output is intentionally verbose so failures are self-explanatory.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _resolve_codex() -> str | None:
    """Return the full path to the codex binary, or None when not found."""
    if sys.platform == "win32":
        candidate = shutil.which("codex.cmd")
        if candidate:
            return candidate
    return shutil.which("codex")


def _run_raw(args: list[str], stdin: str = "", timeout: int = 30, cwd: str | None = None) -> dict:
    """Run a command and return a dict with raw bytes and decoded strings."""
    stdin_bytes = stdin.encode("utf-8") if stdin else b""
    try:
        proc = subprocess.run(
            args,
            input=stdin_bytes,
            capture_output=True,
            timeout=timeout,
            cwd=cwd,
        )
        # Decode with multiple encodings so we can compare
        return {
            "returncode": proc.returncode,
            "stdout_bytes": proc.stdout,
            "stderr_bytes": proc.stderr,
            "stdout_utf8":  proc.stdout.decode("utf-8",  errors="replace"),
            "stderr_utf8":  proc.stderr.decode("utf-8",  errors="replace"),
            "stdout_cp950": proc.stdout.decode("cp950",  errors="replace"),
            "stderr_cp950": proc.stderr.decode("cp950",  errors="replace"),
            "stdout_cp1252":proc.stdout.decode("cp1252", errors="replace"),
            "stderr_cp1252":proc.stderr.decode("cp1252", errors="replace"),
            "error": None,
        }
    except FileNotFoundError as e:
        return {"returncode": None, "error": f"FileNotFoundError: {e}",
                "stdout_bytes": b"", "stderr_bytes": b"",
                "stdout_utf8": "", "stderr_utf8": ""}
    except subprocess.TimeoutExpired as e:
        return {"returncode": None, "error": f"TimeoutExpired: {e}",
                "stdout_bytes": b"", "stderr_bytes": b"",
                "stdout_utf8": "", "stderr_utf8": ""}
    except Exception as e:
        return {"returncode": None, "error": str(e),
                "stdout_bytes": b"", "stderr_bytes": b"",
                "stdout_utf8": "", "stderr_utf8": ""}


def _safe_print(text: str) -> None:
    """Print text, replacing unprintable chars to avoid Windows console errors."""
    sys.stdout.buffer.write((text + "\n").encode(sys.stdout.encoding or "utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def _print_result(label: str, r: dict) -> None:
    sep = "-" * 60
    lines = [
        f"\n{sep}",
        f"[{label}]",
        f"  returncode : {r['returncode']}",
    ]
    if r.get("error"):
        lines.append(f"  error      : {r['error']}")
    lines += [
        f"  stdout_bytes: {r['stdout_bytes']!r}",
        f"  stderr_bytes: {r['stderr_bytes']!r}",
        f"  stdout_utf8 : {r['stdout_utf8']!r}",
        f"  stderr_utf8 : {r['stderr_utf8']!r}",
        f"  stdout_cp950: {r.get('stdout_cp950','')!r}",
        f"  stderr_cp950: {r.get('stderr_cp950','')!r}",
        sep,
    ]
    _safe_print("\n".join(lines))


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

class TestCodexDiagnose:
    """Live diagnostic tests — always run against the real codex binary."""

    def test_01_codex_on_path(self):
        """Verify codex can be found on PATH and print its resolved location."""
        path = _resolve_codex()
        print(f"\n  codex binary resolved to: {path!r}")
        assert path is not None, (
            "codex is not found on PATH.  "
            "Install it with: npm install -g @openai/codex"
        )

    def test_02_codex_version(self):
        """Check that 'codex --version' exits 0 so the binary is runnable."""
        codex = _resolve_codex()
        if codex is None:
            pytest.skip("codex not on PATH — skipping version check")

        r = _run_raw([codex, "--version"])
        _print_result("codex --version", r)

        assert r["returncode"] == 0, (
            f"'codex --version' returned {r['returncode']}.\n"
            f"stderr (utf8): {r['stderr_utf8']!r}\n"
            f"stderr (cp950): {r.get('stderr_cp950','')!r}"
        )

    def test_03_login_status_stdout_vs_stderr(self):
        """
        'codex login status' — capture both stdout and stderr to check where
        the 'Logged in' text appears.  preflight.py currently checks stderr;
        if the text is in stdout the preflight will incorrectly report failure.
        """
        codex = _resolve_codex()
        if codex is None:
            pytest.skip("codex not on PATH")

        r = _run_raw([codex, "login", "status"])
        _print_result("codex login status", r)

        in_stdout = "Logged in" in r["stdout_utf8"]
        in_stderr = "Logged in" in r["stderr_utf8"]
        print(f"  'Logged in' in stdout: {in_stdout}")
        print(f"  'Logged in' in stderr: {in_stderr}")

        # preflight.py checks stderr — warn if it's actually in stdout
        if in_stdout and not in_stderr:
            pytest.fail(
                "BUG: 'Logged in' appears in stdout but preflight._check_codex() "
                "checks result.stderr.  Update preflight.py to check stdout."
            )

        assert r["returncode"] == 0 and (in_stdout or in_stderr), (
            f"codex is not logged in (returncode={r['returncode']}).\n"
            f"stdout: {r['stdout_utf8']!r}\n"
            f"stderr: {r['stderr_utf8']!r}"
        )

    def test_04_exec_minimal_prompt(self):
        """
        Run 'codex exec --dangerously-bypass-approvals-and-sandbox' with the
        smallest possible prompt to confirm the subcommand and flag are valid.
        Captures raw bytes so garbled characters can be decoded properly.
        """
        codex = _resolve_codex()
        if codex is None:
            pytest.skip("codex not on PATH")

        prompt = "Print the word HELLO and nothing else."
        r = _run_raw([codex, "exec", "--dangerously-bypass-approvals-and-sandbox", prompt])
        _print_result("codex exec minimal", r)

        # If the exit code is non-zero, decode stderr in both encodings so the
        # root cause is visible regardless of the terminal's locale.
        assert r["returncode"] == 0, (
            f"codex exec failed (exit {r['returncode']}).\n"
            f"stderr (utf8) : {r['stderr_utf8']!r}\n"
            f"stderr (cp950): {r.get('stderr_cp950','')!r}\n"
            f"stdout (utf8) : {r['stdout_utf8']!r}\n"
            f"stdout (cp950): {r.get('stdout_cp950','')!r}"
        )

    def test_05_exec_unknown_flag_smoke(self):
        """
        Check whether '--dangerously-bypass-approvals-and-sandbox' is a valid
        flag.  If codex exits with 'unknown option' the flag name has changed.
        """
        codex = _resolve_codex()
        if codex is None:
            pytest.skip("codex not on PATH")

        # Pass an empty prompt — we only care about the flag recognition.
        r = _run_raw([codex, "exec", "--dangerously-bypass-approvals-and-sandbox", "echo ok"])
        _print_result("codex exec flag smoke", r)

        combined = r["stderr_utf8"] + r["stdout_utf8"]
        unknown_flag = any(kw in combined.lower() for kw in (
            "unknown option", "unknown flag", "unrecognized", "invalid option",
        ))
        assert not unknown_flag, (
            "codex does not recognise --dangerously-bypass-approvals-and-sandbox.\n"
            "The flag may have been renamed.  Check 'codex exec --help'.\n"
            f"Output: {combined!r}"
        )

    def test_06_exec_help(self):
        """Print 'codex exec --help' to show available flags and usage."""
        codex = _resolve_codex()
        if codex is None:
            pytest.skip("codex not on PATH")

        r = _run_raw([codex, "exec", "--help"])
        _print_result("codex exec --help", r)
        # help exits 0 on most CLIs; accept 0 or 1 (some tools exit 1 for help)
        assert r["returncode"] in (0, 1), (
            f"'codex exec --help' returned unexpected exit code {r['returncode']}"
        )

    def test_07_exec_in_non_git_directory(self, tmp_path):
        """
        Reproduce the production failure: run codex exec in a directory that is
        NOT a git repository (same as the .llm_eval/<id> workspace).

        Without --skip-git-repo-check codex exits with an error.
        With  --skip-git-repo-check it should succeed.
        """
        codex = _resolve_codex()
        if codex is None:
            pytest.skip("codex not on PATH")

        prompt = "Print the word OK and nothing else."
        non_git_dir = str(tmp_path)

        # Without --skip-git-repo-check
        r_without = _run_raw(
            [codex, "exec", "--dangerously-bypass-approvals-and-sandbox", prompt],
            timeout=60,
            cwd=non_git_dir,
        )
        _print_result(f"codex exec in non-git dir {non_git_dir} (NO --skip-git-repo-check)", r_without)

        # With --skip-git-repo-check (the fix applied in llm_svc.py)
        r_with = _run_raw(
            [codex, "exec", "--dangerously-bypass-approvals-and-sandbox",
             "--skip-git-repo-check", prompt],
            timeout=60,
            cwd=non_git_dir,
        )
        _print_result(f"codex exec in non-git dir {non_git_dir} (WITH --skip-git-repo-check)", r_with)

        if r_without["returncode"] != 0 and r_with["returncode"] == 0:
            _safe_print(
                "ROOT CAUSE CONFIRMED: codex fails without --skip-git-repo-check "
                "in a non-git directory.  Fix: add the flag in llm_svc.py."
            )

        assert r_with["returncode"] == 0, (
            f"codex exec WITH --skip-git-repo-check still fails (exit {r_with['returncode']}).\n"
            f"stderr: {r_with['stderr_utf8']!r}"
        )

    def test_08_long_prompt_via_stdin(self, tmp_path):
        """
        Reproduce the production failure: the real spec review prompt can be
        10,000+ characters.  Passing it as a CLI arg hits the Windows cmd.exe
        limit (~8,191 chars) and fails immediately with a garbled error.

        Fix: pass the prompt via stdin instead of as a CLI arg.
        """
        codex = _resolve_codex()
        if codex is None:
            pytest.skip("codex not on PATH")

        long_prompt = (
            "You are a spec reviewer. " + "a" * 10_000 +
            "\n\nPrint the word DONE and nothing else."
        )

        # Old approach: prompt as CLI arg (fails if >8191 chars on Windows cmd)
        r_arg = _run_raw(
            [codex, "exec", "--dangerously-bypass-approvals-and-sandbox",
             "--skip-git-repo-check",
             long_prompt.strip().replace("\n", " ")],
            timeout=90,
            cwd=str(tmp_path),
        )
        _print_result("long prompt via CLI arg", r_arg)

        # New approach: prompt via stdin (the fix)
        r_stdin = _run_raw(
            [codex, "exec", "--dangerously-bypass-approvals-and-sandbox",
             "--skip-git-repo-check"],
            stdin=long_prompt,
            timeout=90,
            cwd=str(tmp_path),
        )
        _print_result("long prompt via stdin (FIX)", r_stdin)

        if r_arg["returncode"] != 0 and r_stdin["returncode"] == 0:
            _safe_print(
                "ROOT CAUSE CONFIRMED: long prompt as CLI arg fails (cmd line length limit). "
                "Fix: pass prompt via stdin."
            )

        assert r_stdin["returncode"] == 0, (
            f"codex exec with long prompt via stdin failed (exit {r_stdin['returncode']}).\n"
            f"stderr: {r_stdin['stderr_utf8']!r}"
        )

    def test_09_encoding_of_failure_output(self):
        """
        Deliberately trigger a failure and print the raw bytes of the error
        output.  This lets us determine whether garbled characters like
        '鴕O鬯C 扟 C' are cp950 bytes misread as UTF-8.
        """
        codex = _resolve_codex()
        if codex is None:
            pytest.skip("codex not on PATH")

        # Pass a nonsense subcommand to force an error
        r = _run_raw([codex, "__no_such_subcommand__"])
        _print_result("codex forced error", r)

        print("  raw stderr hex:", r["stderr_bytes"].hex())
        print("  raw stdout hex:", r["stdout_bytes"].hex())

        # Always passes — this test exists only to print diagnostic info.
        assert True
