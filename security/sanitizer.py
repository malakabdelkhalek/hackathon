"""
Prompt injection detection and sanitization module.
Protects all agent inputs from adversarial prompt manipulation.
"""

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore your instructions",
    "forget your rules",
    "you are now",
    "disregard",
    "override",
    "system prompt",
    "new instructions",
    "act as",
    "pretend you are",
    "jailbreak",
    "do anything now",
]


class PromptInjectionDetected(Exception):
    """Raised when a prompt injection attempt is detected in user-supplied input."""
    pass


def sanitize(text: str, field_name: str = "input") -> str:
    """
    Check text for prompt injection patterns.
    Raises PromptInjectionDetected if a pattern is found.
    Returns the original text if clean.
    """
    if not isinstance(text, str):
        return text

    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern.lower() in text_lower:
            raise PromptInjectionDetected(
                f"PROMPT INJECTION DETECTED in field '{field_name}': "
                f"Pattern '{pattern}' found in input: '{text[:100]}'"
            )
    return text
