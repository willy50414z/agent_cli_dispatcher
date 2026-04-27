from llm_eval.job import Outcome


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

    for outcome in outcomes:
        lines.append(f"  status_{outcome.status:<20} — {outcome.description}")

    lines.append("")

    for outcome in outcomes:
        if outcome.output_files:
            lines.append(f'If the outcome is "{outcome.status}", also write these files:')
            for filename in outcome.output_files:
                lines.append(f"  {filename}")
            lines.append("")

    lines.append("Do not create more than one status file.")
    lines.append("Do not write anything inside the status file.")

    return "\n".join(lines)
