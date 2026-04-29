# Output guardrails - validate LLM output before returning to user
import re
from guardrails.base import BaseGuard, GuardResult

class EmptyOutputGuard(BaseGuard):
    """Ensure output is not empty or trivial."""
    def check(self, content: str, **kwargs) -> GuardResult:
        if not content or len(content.strip()) < 10:
            return GuardResult(passed=False, message="Output is empty or too short.")
        return GuardResult(passed=True)

class HallucinationGuard(BaseGuard):
    """Flag outputs that contain common hallucination indicators."""
    INDICATORS = [
        r"as an ai",
        r"i cannot",
        r"i don'?t have access",
        r"i'?m not able to",
        r"my training data",
        r"as of my last update",
    ]

    def check(self, content: str, **kwargs) -> GuardResult:
        lower = content.lower()
        for pattern in self.INDICATORS:
            if re.search(pattern, lower):
                return GuardResult(
                    passed=True,  # Pass but flag
                    message=f"Warning: Output contains AI self-reference pattern.",
                    sanitized_content=content,
                )
        return GuardResult(passed=True)

class SensitiveDataGuard(BaseGuard):
    """Detect and redact potential sensitive data in output."""
    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    }

    def check(self, content: str, **kwargs) -> GuardResult:
        redacted = content
        found = []
        for name, pattern in self.PATTERNS.items():
            if re.search(pattern, redacted):
                found.append(name)
                redacted = re.sub(pattern, f"[REDACTED-{name.upper()}]", redacted)
        if found:
            return GuardResult(
                passed=True,
                message=f"Redacted sensitive data: {', '.join(found)}",
                sanitized_content=redacted,
            )
        return GuardResult(passed=True)

# Default output guards
OUTPUT_GUARDS = [
    EmptyOutputGuard(),
    HallucinationGuard(),
    SensitiveDataGuard(),
]

def validate_output(content: str) -> GuardResult:
    """Run all output guards. Returns first failure or sanitized content."""
    sanitized = content
    warnings = []
    for guard in OUTPUT_GUARDS:
        result = guard.check(sanitized)
        if not result.passed:
            return result
        if result.message:
            warnings.append(result.message)
        if result.sanitized_content:
            sanitized = result.sanitized_content
    return GuardResult(passed=True, message="; ".join(warnings), sanitized_content=sanitized)