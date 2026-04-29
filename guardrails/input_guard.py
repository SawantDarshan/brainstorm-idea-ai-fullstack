# Input guardrails - validate and sanitize user input before processing
import re
from guardrails.base import BaseGuard, GuardResult

class TopicLengthGuard(BaseGuard):
    """Ensure topic is within acceptable length."""
    def __init__(self, min_len: int = 2, max_len: int = 500):
        self.min_len = min_len
        self.max_len = max_len

    def check(self, content: str, **kwargs) -> GuardResult:
        if len(content.strip()) < self.min_len:
            return GuardResult(passed=False, message=f"Input too short. Minimum {self.min_len} characters.")
        if len(content.strip()) > self.max_len:
            return GuardResult(passed=False, message=f"Input too long. Maximum {self.max_len} characters.")
        return GuardResult(passed=True)

class InjectionGuard(BaseGuard):
    """Block prompt injection attempts."""
    PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"you\s+are\s+now\s+",
        r"forget\s+(everything|all)",
        r"system\s*:\s*",
        r"<\s*script",
        r"\{\{.*\}\}",
    ]

    def check(self, content: str, **kwargs) -> GuardResult:
        lower = content.lower()
        for pattern in self.PATTERNS:
            if re.search(pattern, lower):
                return GuardResult(passed=False, message="Potential prompt injection detected.")
        return GuardResult(passed=True)

class ProfanityGuard(BaseGuard):
    """Basic profanity/harmful content filter."""
    BLOCKED_TERMS = [
        "hack", "exploit", "malware", "phishing",
    ]

    def check(self, content: str, **kwargs) -> GuardResult:
        lower = content.lower()
        for term in self.BLOCKED_TERMS:
            if term in lower:
                return GuardResult(passed=False, message=f"Input contains blocked term: '{term}'.")
        return GuardResult(passed=True)

# Default input guards
INPUT_GUARDS = [
    TopicLengthGuard(),
    InjectionGuard(),
    ProfanityGuard(),
]

def validate_input(content: str) -> GuardResult:
    """Run all input guards. Returns first failure or success."""
    for guard in INPUT_GUARDS:
        result = guard.check(content)
        if not result.passed:
            return result
    return GuardResult(passed=True, sanitized_content=content.strip())