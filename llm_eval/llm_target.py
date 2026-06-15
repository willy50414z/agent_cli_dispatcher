from enum import Enum


class LLMTarget(Enum):
    CLAUDE   = "claude"
    GEMINI   = "gemini"
    CODEX    = "codex"
    OPENCODE = "opencode"
    COPILOT  = "copilot"
    DEEPSEEK = "deepseek"


def parse_targets(value: str) -> list[LLMTarget]:
    """Parse 'claude,gemini' → [LLMTarget.CLAUDE, LLMTarget.GEMINI]."""
    return [LLMTarget(v.strip()) for v in value.split(",") if v.strip()]
