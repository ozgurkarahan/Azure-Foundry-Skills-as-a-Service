"""End-to-end test suite for the Foundry Skills agent.

Tests that each skill is correctly discovered and followed by the agent.
Uses keyword/pattern assertions on agent responses to verify skill adherence.

Usage:
    python -m tests.test_e2e                 # Run all tests
    python -m tests.test_e2e summarize       # Run only summarize tests
    python -m tests.test_e2e sentiment       # Run only sentiment tests
"""

import re
import sys
import time

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from src.agent.config import PROJECT_ENDPOINT, AGENT_NAME


# ---------------------------------------------------------------------------
# Agent invocation helper
# ---------------------------------------------------------------------------

_client = None
_openai = None


def get_client():
    global _client, _openai
    if _client is None:
        _client = AIProjectClient(
            endpoint=PROJECT_ENDPOINT,
            credential=DefaultAzureCredential(),
        )
        _openai = _client.get_openai_client()
    return _openai


def invoke_agent(message: str) -> str:
    """Send a message to the agent and return the full response text."""
    openai = get_client()
    response = openai.responses.create(
        model="gpt-4o",
        input=message,
        extra_body={
            "agent_reference": {
                "type": "agent_reference",
                "name": AGENT_NAME,
            }
        },
    )
    parts = []
    for item in response.output:
        if hasattr(item, "content"):
            for c in item.content:
                if hasattr(c, "text"):
                    parts.append(c.text)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

def assert_contains(response: str, keywords: list[str], case_sensitive: bool = False):
    """Assert that the response contains ALL keywords."""
    check = response if case_sensitive else response.lower()
    missing = []
    for kw in keywords:
        target = kw if case_sensitive else kw.lower()
        if target not in check:
            missing.append(kw)
    if missing:
        raise AssertionError(f"Missing keywords: {missing}")


def assert_contains_any(response: str, keywords: list[str], case_sensitive: bool = False):
    """Assert that the response contains AT LEAST ONE of the keywords."""
    check = response if case_sensitive else response.lower()
    for kw in keywords:
        target = kw if case_sensitive else kw.lower()
        if target in check:
            return
    raise AssertionError(f"Expected at least one of: {keywords}")


def assert_not_contains(response: str, keywords: list[str], case_sensitive: bool = False):
    """Assert that the response does NOT contain any of the keywords."""
    check = response if case_sensitive else response.lower()
    found = []
    for kw in keywords:
        target = kw if case_sensitive else kw.lower()
        if target in check:
            found.append(kw)
    if found:
        raise AssertionError(f"Unexpected keywords found: {found}")


def assert_has_section(response: str, section_header: str):
    """Assert that the response contains a markdown bold section like **Header:**."""
    pattern = rf"\*\*{re.escape(section_header)}"
    if not re.search(pattern, response, re.IGNORECASE):
        raise AssertionError(f"Missing section: **{section_header}**")


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TEST_CASES = []


def test_case(name: str, description: str):
    """Decorator to register a test case."""
    def decorator(func):
        TEST_CASES.append({"name": name, "description": description, "func": func})
        return func
    return decorator


# ===== SUMMARIZE SKILL =====

@test_case(
    "summarize-bullet-points",
    "Summarize skill returns bullet points with key themes and action items",
)
def test_summarize_basic():
    response = invoke_agent(
        "Summarize this: The quarterly sales report shows a 15% increase in revenue "
        "compared to last quarter. The North American market performed exceptionally well, "
        "growing by 22%. However, the European market declined by 3% due to regulatory "
        "changes. The team recommends increasing investment in the North American market "
        "and conducting a regulatory impact assessment for Europe. Action items include "
        "hiring two additional sales representatives and scheduling a strategy meeting "
        "for next Tuesday."
    )
    assert_contains(response, ["north america", "europe"])
    assert_contains_any(response, ["action item", "next step", "recommendation", "hiring", "strategy meeting"])
    return response


@test_case(
    "summarize-executive-format",
    "Summarize skill returns executive summary format with Context/Findings/Recommendations",
)
def test_summarize_executive():
    response = invoke_agent(
        "Give me an executive summary of this: Our cloud migration project is 75% complete. "
        "We have successfully migrated 12 out of 16 applications to Azure. The remaining 4 "
        "applications require custom networking configurations. Budget utilization is at 68%. "
        "Key risk: the SAP migration is blocked by a vendor dependency expected to resolve "
        "by end of month."
    )
    assert_contains_any(response, ["context", "key finding", "recommendation", "next step"])
    assert_contains_any(response, ["75%", "12", "16"])
    return response


@test_case(
    "summarize-short-text-guard",
    "Summarize skill tells user text is already concise when under 100 words",
)
def test_summarize_short():
    response = invoke_agent(
        "Summarize this: The meeting is at 3pm tomorrow."
    )
    assert_contains_any(response, ["concise", "already", "short", "brief"])
    return response


# ===== TRANSLATE SKILL =====

@test_case(
    "translate-to-french",
    "Translate skill outputs Source/Target language headers and French text",
)
def test_translate_french():
    response = invoke_agent(
        "Translate to French: The project deadline has been extended by two weeks. "
        "Please update your timelines accordingly."
    )
    assert_has_section(response, "Source language")
    assert_has_section(response, "Target language")
    assert_contains_any(response, ["english", "anglais"])
    assert_contains_any(response, ["french", "fran"])
    assert_contains_any(response, ["projet", "semaine", "calendrier", "prolonge", "mise"])
    return response


@test_case(
    "translate-to-spanish",
    "Translate skill preserves bullet-point formatting in Spanish",
)
def test_translate_spanish():
    response = invoke_agent(
        "Translate to Spanish:\n"
        "- Item 1: Review the budget\n"
        "- Item 2: Schedule the meeting\n"
        "- Item 3: Send the report"
    )
    assert_has_section(response, "Target language")
    assert_contains_any(response, ["spanish", "espa"])
    assert_contains_any(response, ["presupuesto", "reuni", "informe", "revisar", "enviar"])
    return response


@test_case(
    "translate-preserve-code",
    "Translate skill leaves code blocks unchanged per its rules",
)
def test_translate_code():
    response = invoke_agent(
        "Translate to German: Here is an example:\n"
        "```python\nprint('hello world')\n```\n"
        "This code prints a greeting."
    )
    assert_contains(response, ["print"])
    assert_contains_any(response, ["hello world", "hello"])
    assert_has_section(response, "Target language")
    return response


# ===== ANALYZE SENTIMENT SKILL =====

@test_case(
    "sentiment-positive-review",
    "Sentiment skill detects positive sentiment with all required sections",
)
def test_sentiment_positive():
    response = invoke_agent(
        "Analyze the sentiment: This is the best product I have ever purchased! "
        "The quality is amazing, delivery was super fast, and the customer support "
        "team was incredibly helpful when I had a question."
    )
    assert_has_section(response, "Overall Sentiment")
    assert_has_section(response, "Confidence")
    assert_has_section(response, "Emotions Detected")
    assert_has_section(response, "Key Themes")
    assert_has_section(response, "Summary")
    assert_contains_any(response, ["positive"])
    return response


@test_case(
    "sentiment-negative-review",
    "Sentiment skill detects negative sentiment and cites evidence from text",
)
def test_sentiment_negative():
    response = invoke_agent(
        "What's the sentiment of this review: Terrible experience. The product "
        "arrived broken, customer service was rude and unhelpful, and they refused "
        "to give me a refund. I will never buy from this company again."
    )
    assert_has_section(response, "Overall Sentiment")
    assert_contains_any(response, ["negative"])
    assert_contains_any(response, ["broken", "rude", "refund", "terrible"])
    return response


@test_case(
    "sentiment-mixed-review",
    "Sentiment skill detects mixed sentiment when text has both positive and negative",
)
def test_sentiment_mixed():
    response = invoke_agent(
        "Analyze sentiment: The food was absolutely delicious and the ambiance was "
        "lovely. However, the service was painfully slow, we waited 45 minutes for "
        "our main course, and the waiter got our order wrong twice."
    )
    assert_has_section(response, "Overall Sentiment")
    assert_contains_any(response, ["mixed"])
    return response


# ===== SKILL DISCOVERY & FALLBACK =====

@test_case(
    "registry-list-skills",
    "Agent lists available skills from registry when asked",
)
def test_registry():
    response = invoke_agent("What skills do you have available?")
    assert_contains_any(response, ["summarize", "summary"])
    assert_contains_any(response, ["translate", "translation"])
    assert_contains_any(response, ["sentiment", "analyze"])
    return response


@test_case(
    "fallback-general-knowledge",
    "Agent responds with general knowledge when no skill matches",
)
def test_fallback():
    response = invoke_agent("What is the capital of France?")
    assert_contains(response, ["paris"])
    return response


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_tests(filter_name: str = None):
    """Run all registered test cases (or filtered by name substring)."""
    cases = TEST_CASES
    if filter_name:
        cases = [tc for tc in cases if filter_name.lower() in tc["name"].lower()]

    total = len(cases)
    passed = 0
    failed = 0
    errors = []

    print(f"\n{'='*70}")
    print(f"  Foundry Skills - E2E Test Suite ({total} tests)")
    print(f"  Agent: {AGENT_NAME} @ {PROJECT_ENDPOINT}")
    print(f"{'='*70}\n")

    for i, tc in enumerate(cases, 1):
        name = tc["name"]
        desc = tc["description"]
        print(f"[{i}/{total}] {name}")
        print(f"       {desc}")
        sys.stdout.write(f"       ")
        sys.stdout.flush()

        start = time.time()
        try:
            response = tc["func"]()
            elapsed = time.time() - start
            print(f"PASSED ({elapsed:.1f}s)")
            passed += 1
        except Exception as e:
            elapsed = time.time() - start
            print(f"FAILED ({elapsed:.1f}s)")
            print(f"       Error: {e}")
            failed += 1
            errors.append({"name": name, "error": str(e)})
        print()

    # Summary
    print(f"{'='*70}")
    status = "ALL PASSED" if failed == 0 else f"{failed} FAILED"
    print(f"  {status} | {passed} passed, {failed} failed, {total} total")
    print(f"{'='*70}")

    if errors:
        print("\n  Failed tests:")
        for e in errors:
            print(f"    x {e['name']}: {e['error']}")
        print()

    return failed == 0


if __name__ == "__main__":
    filter_arg = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_tests(filter_arg)
    sys.exit(0 if success else 1)
