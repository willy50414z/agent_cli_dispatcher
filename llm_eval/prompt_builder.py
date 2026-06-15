from pathlib import Path

from llm_eval.job import Outcome, effective_status


def build_prompt(purpose: str, outcomes: list[Outcome], workspace: Path | None = None) -> str:
    outcome_lines: list[str] = []
    for i, outcome in enumerate(outcomes):
        st = effective_status(outcome, i)
        if not outcome.output_files or st == "error":
            continue
        outcome_lines.append(f'If the outcome is "{st}" ({outcome.description}), write:')
        for filename in outcome.output_files:
            path = str(workspace / filename) if workspace else filename
            outcome_lines.append(f"  {path}")
        outcome_lines.append("")

    if not outcome_lines:
        return purpose

    return "\n".join([purpose, "", "---", "", *outcome_lines]).rstrip()
