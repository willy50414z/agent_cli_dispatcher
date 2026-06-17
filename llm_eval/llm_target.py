from enum import Enum


class LLMTarget(Enum):
    CLAUDE   = "claude"
    # GEMINI   = "gemini"    # untested — coming soon
    CODEX    = "codex"
    # OPENCODE = "opencode"  # untested — coming soon
    # COPILOT  = "copilot"   # untested — coming soon
    DEEPSEEK = "deepseek"


def parse_targets(value: str) -> list[LLMTarget]:
    """Parse 'claude,codex' → [LLMTarget.CLAUDE, LLMTarget.CODEX]."""
    return [LLMTarget(v.strip()) for v in value.split(",") if v.strip()]
