from llm_eval.job import Outcome, effective_status


def build_prompt(purpose: str, outcomes: list[Outcome]) -> str:
    lines = [
        purpose,
        "",
        "---",
        "",
        "After completing your analysis, you MUST create exactly one of the following "
        "empty files in your current working directory to signal your conclusion. "
        "This must be the last action you take.",
        "",
        "Status files (create exactly one, leave it empty):",
    ]

    for i, outcome in enumerate(outcomes):
        status = effective_status(outcome, i)
        lines.append(f"  status_{status:<20} — {outcome.description}")

    lines.append("")

    for i, outcome in enumerate(outcomes):
        if outcome.output_files:
            status = effective_status(outcome, i)
            lines.append(f'If the outcome is "{status}", also write these files:')
            for filename in outcome.output_files:
                lines.append(f"  {filename}")
            lines.append("")

    lines.append("Do not create more than one status file.")
    lines.append("Do not write anything inside the status file.")

    return "\n".join(lines)
