import argparse
import json
import sys
import time
from pathlib import Path
from typing import Sequence

import llm_eval
from llm_eval import llm_svc
from llm_eval.job import JobResult, Outcome
from llm_eval.llm_target import LLMTarget, parse_targets
from llm_eval.openspec_delegation import install_project_guidance, uninstall_project_guidance
from llm_eval.preflight import TargetStatus, check_all, check_target
from llm_eval.prompt_builder import build_prompt
from llm_eval.status_resolver import resolve
from llm_eval.workspace import cleanup_workspace, create_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-dispatch")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a raw prompt against an LLM target.")
    _add_target_args(run_parser, required=True)
    _add_input_args(run_parser, "prompt")
    _add_common_execution_args(run_parser)
    run_parser.set_defaults(handler=_handle_run)

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Run outcome-routed LLM execution and emit JSON."
    )
    _add_target_args(evaluate_parser, required=True)
    _add_input_args(evaluate_parser, "purpose")
    _add_common_execution_args(evaluate_parser)
    evaluate_parser.add_argument(
        "--outcome",
        action="append",
        required=True,
        default=[],
        metavar="STATUS=DESCRIPTION",
        help="Declare an outcome status and description. May be repeated.",
    )
    evaluate_parser.add_argument(
        "--output-file",
        action="append",
        default=[],
        metavar="STATUS=PATH",
        help="Declare an output file for an outcome status. May be repeated.",
    )
    evaluate_parser.add_argument(
        "--json",
        action="store_true",
        required=True,
        help="Write one JSON result object to stdout.",
    )
    evaluate_parser.set_defaults(handler=_handle_evaluate)

    health_parser = subparsers.add_parser("health", help="Check target availability.")
    health_parser.add_argument("--target", choices=[target.value for target in LLMTarget])
    health_parser.add_argument("--json", action="store_true", required=True)
    health_parser.set_defaults(handler=_handle_health)

    install_parser = subparsers.add_parser(
        "install_delegant",
        help="Install project-local OpenSpec delegation guidance.",
    )
    install_parser.add_argument(
        "--mode",
        choices=["main", "hybrid", "delegated-apply"],
        help="Delegation mode: main (all work stays with main model), "
        "hybrid (main model plans/integrates, submodels handle bounded work), "
        "delegated-apply (main model delegates apply and verifies).",
    )
    install_parser.add_argument(
        "--level",
        type=int,
        choices=[1, 2],
        help="(Deprecated) Delegation level: 1 maps to hybrid, 2 maps to delegated-apply. "
        "Use --mode instead.",
    )
    install_parser.add_argument(
        "--yes",
        action="store_true",
        help="Use the recommended hybrid mode default in non-interactive mode.",
    )
    install_parser.add_argument(
        "--cwd",
        help="Project directory to install into. Defaults to the current directory.",
    )
    install_parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the managed OpenSpec delegation guidance block from this project.",
    )
    install_parser.set_defaults(handler=_handle_install_delegant)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return args.handler(args)
    except SystemExit as exc:
        return int(exc.code)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _add_target_args(parser: argparse.ArgumentParser, *, required: bool) -> None:
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument("--target", choices=[target.value for target in LLMTarget])
    group.add_argument("--targets", help="Comma-separated ordered fallback target list.")


def _add_input_args(parser: argparse.ArgumentParser, name: str) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(f"--{name}", dest="input_text")
    group.add_argument(f"--{name}-file", dest="input_file")
    group.add_argument("--stdin", action="store_true", dest="input_stdin")


def _add_common_execution_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--cwd")


def _handle_run(args: argparse.Namespace) -> int:
    prompt = _load_input(args)
    target, targets = _parse_target_args(args)
    output = llm_eval.run(
        target=target,
        targets=targets,
        prompt=prompt,
        model=args.model,
        timeout=args.timeout,
        cwd=args.cwd,
    )
    sys.stdout.write(output)
    return 0


def _handle_evaluate(args: argparse.Namespace) -> int:
    purpose = _load_input(args)
    target, targets = _parse_target_args(args)
    selected_targets = targets if targets is not None else [target]
    outcomes = _parse_outcomes(args.outcome, args.output_file)
    result = _execute_evaluate(
        selected_targets,
        purpose,
        outcomes,
        model=args.model,
        timeout=args.timeout,
        cwd=args.cwd,
    )
    print(json.dumps(_job_result_to_json(result), sort_keys=True))
    return 0


def _handle_health(args: argparse.Namespace) -> int:
    if args.target:
        target = LLMTarget(args.target)
        statuses = {target: check_target(target)}
    else:
        statuses = check_all()
    print(json.dumps(_target_statuses_to_json(statuses), sort_keys=True))
    return 0


_LEVEL_TO_MODE = {1: "hybrid", 2: "delegated-apply"}


def _resolve_mode(args: argparse.Namespace) -> str:
    provided_mode = args.mode
    provided_level = args.level

    if provided_level is not None:
        mapped_mode = _LEVEL_TO_MODE[provided_level]
        if provided_mode is not None and provided_mode != mapped_mode:
            raise ValueError(
                f"--mode {provided_mode} and --level {provided_level} are incompatible. "
                f"Level {provided_level} maps to '{mapped_mode}'. "
                f"Use only --mode."
            )
        return mapped_mode

    if provided_mode is not None:
        return provided_mode

    return _select_install_mode(args.yes)


def _select_install_mode(use_default: bool) -> str:
    if use_default:
        return "hybrid"
    if not sys.stdin.isatty():
        raise ValueError(
            "install_delegant requires --mode in non-interactive mode. "
            "Use --yes for the recommended hybrid default."
        )

    print("Select OpenSpec delegation mode:")
    print("A) main — all apply work stays with the main model")
    print("B) hybrid — main model plans/integrates/validates; submodels handle bounded work (recommended)")
    print("C) delegated-apply — main model delegates apply to a submodel and verifies completion")
    choice = input("Mode [A/B/C]: ").strip().upper()
    if choice == "A":
        return "main"
    elif choice == "B":
        return "hybrid"
    elif choice == "C":
        return "delegated-apply"
    raise ValueError("mode must be A, B, or C")


def _handle_install_delegant(args: argparse.Namespace) -> int:
    project_dir = args.cwd if args.cwd else Path.cwd()
    if args.uninstall:
        result = uninstall_project_guidance(project_dir)
        print(f"OpenSpec delegation guidance {result.action}: {result.path}")
        return 0

    mode = _resolve_mode(args)
    result = install_project_guidance(project_dir, mode)
    print(f"OpenSpec delegation guidance {result.action}: {result.path}")
    print(f"Delegation mode: {result.mode}")
    print("Scope: project-local")
    return 0


def _load_input(args: argparse.Namespace) -> str:
    if args.input_text is not None:
        return args.input_text
    if args.input_file is not None:
        return Path(args.input_file).read_text(encoding="utf-8")
    if args.input_stdin:
        return sys.stdin.read()
    raise ValueError("input is required")


def _parse_target_args(args: argparse.Namespace) -> tuple[LLMTarget | None, list[LLMTarget] | None]:
    if args.target is not None:
        return LLMTarget(args.target), None
    if args.targets is not None:
        targets = parse_targets(args.targets)
        if not targets:
            raise ValueError("--targets must include at least one target")
        return None, targets
    raise ValueError("--target or --targets is required")


def _parse_outcomes(
    outcome_values: list[str], output_file_values: list[str]
) -> list[Outcome]:
    output_files_by_status: dict[str, list[str]] = {}
    for value in output_file_values:
        status, path = _parse_assignment(value, "--output-file")
        output_files_by_status.setdefault(status, []).append(path)

    outcomes: list[Outcome] = []
    seen_statuses: set[str] = set()
    for value in outcome_values:
        status, description = _parse_assignment(value, "--outcome")
        if status in seen_statuses:
            raise ValueError(f"duplicate outcome status: {status}")
        seen_statuses.add(status)
        outcomes.append(
            Outcome(
                status=status,
                description=description,
                callback=lambda result: None,
                output_files=output_files_by_status.pop(status, None),
            )
        )

    if output_files_by_status:
        unknown = ", ".join(sorted(output_files_by_status))
        raise ValueError(f"--output-file references unknown outcome status: {unknown}")
    return outcomes


def _parse_assignment(value: str, flag_name: str) -> tuple[str, str]:
    if "=" not in value:
        raise ValueError(f"{flag_name} must use STATUS=VALUE syntax")
    key, parsed_value = value.split("=", 1)
    key = key.strip()
    parsed_value = parsed_value.strip()
    if not key or not parsed_value:
        raise ValueError(f"{flag_name} must use STATUS=VALUE syntax")
    return key, parsed_value


def _execute_evaluate(
    targets: list[LLMTarget],
    purpose: str,
    outcomes: list[Outcome],
    *,
    model: str | None = None,
    timeout: float = 1800,
    cwd: str | None = None,
) -> JobResult:
    if not targets:
        raise ValueError("evaluate requires at least one target")

    job_id, workspace = create_workspace(cwd)
    prompt = build_prompt(purpose, outcomes, workspace=workspace)
    start = time.monotonic()
    try:
        stdout, winning_target = _run_with_fallback(
            targets, prompt, model=model, cwd=str(workspace), timeout=timeout
        )
        duration = time.monotonic() - start
        _matched, result = resolve(
            workspace=workspace,
            outcomes=outcomes,
            job_id=job_id,
            target=winning_target.value,
            duration_seconds=duration,
            stdout=stdout,
        )
        return result
    finally:
        cleanup_workspace(workspace)


def _run_with_fallback(
    targets: list[LLMTarget],
    prompt: str,
    *,
    model: str | None,
    cwd: str,
    timeout: float,
) -> tuple[str, LLMTarget]:
    last_exc: llm_svc.LLMEvaluationError | None = None
    for target in targets:
        try:
            return llm_svc.run(target, prompt, model=model, cwd=cwd, timeout=timeout), target
        except llm_svc.LLMEvaluationError as exc:
            last_exc = exc
    raise last_exc  # type: ignore[misc]


def _job_result_to_json(result: JobResult) -> dict[str, object]:
    return {
        "status": result.status,
        "target": result.target,
        "duration_seconds": result.duration_seconds,
        "stdout": result.stdout,
        "files": {
            name: content.decode("utf-8", errors="replace")
            for name, content in result.files.items()
        },
    }


def _target_statuses_to_json(
    statuses: dict[LLMTarget, TargetStatus]
) -> dict[str, dict[str, object]]:
    return {
        target.value: {"ok": status.ok, "reason": status.reason}
        for target, status in statuses.items()
    }


if __name__ == "__main__":
    raise SystemExit(main())
