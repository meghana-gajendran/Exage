"""
Objective eval for curiosity breaker anecdotes.

Pure Python checks — no API calls, no cost.
Run these on every generated anecdote.

These are proposed heuristics for ExAge specifically.
Thresholds should be refined after real usage data is available.
"""

import re
from dataclasses import dataclass


@dataclass
class ObjectiveEvalResult:
    anecdote: str
    word_count: int
    length_pass: bool
    concrete_detail_pass: bool
    no_forbidden_phrases_pass: bool
    forbidden_phrases_found: list[str]
    ends_open_pass: bool
    total_checks: int
    checks_passed: int
    passed: bool
    failure_reasons: list[str]


# Phrases that indicate the anecdote is explaining rather than creating curiosity
DEFAULT_FORBIDDEN_PHRASES = [
    "you should",
    "the solution is",
    "the reason is",
    "this is because",
    "this happens when",
    "to fix this",
    "to prevent this",
    "the problem is",
    "you need to",
    "always use",
    "never use",
]

# Phrases that indicate the scenario resolves itself (kills curiosity)
RESOLUTION_PHRASES = [
    "the fix was",
    "the solution was",
    "it turned out",
    "after fixing",
    "once they fixed",
    "after adding",
    "the team resolved",
    "and it worked",
]


def _count_words(text: str) -> int:
    return len(text.split())


def _has_concrete_detail(text: str) -> bool:
    """
    Check for at least one concrete detail:
    - A digit (number)
    - A capitalised proper noun that isn't sentence-start
    - A quoted phrase (something someone said)
    """
    # Contains a digit
    if re.search(r'\d', text):
        return True

    # Contains a quoted phrase (someone said something specific)
    if re.search(r'["\'](.+?)["\']', text):
        return True

    # Contains words that signal a real entity or event
    entity_signals = [
        "customer", "user", "engineer", "manager", "colleague",
        "monday", "tuesday", "wednesday", "thursday", "friday",
        "yesterday", "last week", "last month", "overnight",
        "production", "staging", "deployment",
    ]
    text_lower = text.lower()
    if any(signal in text_lower for signal in entity_signals):
        return True

    return False


def _find_forbidden_phrases(text: str, forbidden: list[str]) -> list[str]:
    text_lower = text.lower()
    return [phrase for phrase in forbidden if phrase.lower() in text_lower]


def _ends_open(text: str) -> bool:
    """
    Check that the anecdote does not resolve itself.
    A good anecdote ends with a question, uncertainty, or unresolved situation.
    """
    text_lower = text.lower().strip()

    # Contains a resolution phrase
    for phrase in RESOLUTION_PHRASES:
        if phrase in text_lower:
            return False

    return True


def run_objective_eval(
    anecdote: str,
    checks: dict | None = None,
) -> ObjectiveEvalResult:
    """
    Run all objective checks on a single anecdote.

    Args:
        anecdote: the generated anecdote text
        checks: optional override for check config (from test_cases.py)
                if None, uses defaults

    Returns:
        ObjectiveEvalResult with pass/fail for each check
    """
    cfg = checks or {}
    min_words = cfg.get("min_words", 30)
    max_words = cfg.get("max_words", 150)
    forbidden = cfg.get("forbidden_phrases", DEFAULT_FORBIDDEN_PHRASES)

    word_count = _count_words(anecdote)
    failure_reasons = []

    # Check 1: length
    length_pass = min_words <= word_count <= max_words
    if not length_pass:
        failure_reasons.append(
            f"Length {word_count} words — expected {min_words}–{max_words}"
        )

    # Check 2: concrete detail
    concrete_detail_pass = _has_concrete_detail(anecdote)
    if not concrete_detail_pass:
        failure_reasons.append(
            "No concrete detail found (digit, entity, quoted speech, or time reference)"
        )

    # Check 3: no forbidden phrases
    found_forbidden = _find_forbidden_phrases(anecdote, forbidden)
    no_forbidden_phrases_pass = len(found_forbidden) == 0
    if not no_forbidden_phrases_pass:
        failure_reasons.append(
            f"Contains forbidden phrases: {found_forbidden}"
        )

    # Check 4: ends open
    ends_open_pass = _ends_open(anecdote)
    if not ends_open_pass:
        failure_reasons.append(
            "Scenario appears to resolve itself — should end with unresolved curiosity"
        )

    checks_passed = sum([
        length_pass,
        concrete_detail_pass,
        no_forbidden_phrases_pass,
        ends_open_pass,
    ])
    total_checks = 4

    # Pass threshold: all 4 checks must pass
    passed = checks_passed == total_checks

    return ObjectiveEvalResult(
        anecdote=anecdote,
        word_count=word_count,
        length_pass=length_pass,
        concrete_detail_pass=concrete_detail_pass,
        no_forbidden_phrases_pass=no_forbidden_phrases_pass,
        forbidden_phrases_found=found_forbidden,
        ends_open_pass=ends_open_pass,
        total_checks=total_checks,
        checks_passed=checks_passed,
        passed=passed,
        failure_reasons=failure_reasons,
    )


def format_objective_result(result: ObjectiveEvalResult) -> str:
    """Human-readable summary of the objective eval result."""
    lines = []
    lines.append(f"Objective eval: {'PASS' if result.passed else 'FAIL'}")
    lines.append(f"  Words: {result.word_count} — {'✅' if result.length_pass else '❌'}")
    lines.append(f"  Concrete detail: {'✅' if result.concrete_detail_pass else '❌'}")
    lines.append(f"  No forbidden phrases: {'✅' if result.no_forbidden_phrases_pass else '❌'}")
    if result.forbidden_phrases_found:
        lines.append(f"    Found: {result.forbidden_phrases_found}")
    lines.append(f"  Ends open: {'✅' if result.ends_open_pass else '❌'}")
    lines.append(f"  Score: {result.checks_passed}/{result.total_checks}")
    if result.failure_reasons:
        lines.append("  Failures:")
        for reason in result.failure_reasons:
            lines.append(f"    - {reason}")
    return "\n".join(lines)
