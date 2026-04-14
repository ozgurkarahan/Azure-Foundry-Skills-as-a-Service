"""LLM-as-judge evaluation for Foundry Skills agent.

Uses a second LLM call to evaluate agent responses on:
1. Skill routing — did the agent pick the correct skill?
2. Format adherence — did the agent follow the skill's output format?
3. Hallucination — did the agent add information not in the source?
4. Rule compliance — did the agent follow the skill's rules?

Usage:
    python -m tests.test_eval              # Run all eval cases
    python -m tests.test_eval translate    # Filter by name
"""

import sys
import time
import json

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from openai import AzureOpenAI

from src.agent.config import PROJECT_ENDPOINT, AGENT_NAME


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

_client = None
_openai = None
_judge = None


def get_clients():
    global _client, _openai, _judge
    if _client is None:
        _client = AIProjectClient(
            endpoint=PROJECT_ENDPOINT,
            credential=DefaultAzureCredential(),
        )
        _openai = _client.get_openai_client()
        _judge = _openai  # Use same client for judge (gpt-4o direct)
    return _openai, _judge


def invoke_agent(message: str) -> str:
    openai, _ = get_clients()
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


def judge_response(
    user_message: str,
    agent_response: str,
    expected_skill: str,
    skill_format: str,
    criteria: str,
) -> dict:
    """Use LLM-as-judge to evaluate an agent response.

    Returns dict with: skill_correct, format_score, hallucination_score,
    rule_compliance_score, overall_score, reasoning.
    """
    _, judge = get_clients()

    judge_prompt = f"""You are an expert evaluator for an AI agent that uses skill files to respond.

Evaluate the agent's response on these criteria:

1. **Skill Routing** (correct/incorrect): Did the agent use the "{expected_skill}" skill?
2. **Format Adherence** (1-5): Does the response match this expected format?
   {skill_format}
3. **Hallucination** (1-5, where 5=no hallucination): Did the agent add information NOT present in the user's input?
4. **Rule Compliance** (1-5): Did the agent follow these rules?
   {criteria}

## User Message
{user_message}

## Agent Response
{agent_response}

Respond in this exact JSON format (no markdown, no code fences):
{{"skill_correct": true/false, "format_score": 1-5, "hallucination_score": 1-5, "rule_compliance_score": 1-5, "overall_score": 1-5, "reasoning": "brief explanation"}}"""

    result = judge.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": judge_prompt}],
        temperature=0,
    )

    text = result.choices[0].message.content.strip()
    # Clean markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(text)


# ---------------------------------------------------------------------------
# Eval cases
# ---------------------------------------------------------------------------

EVAL_CASES = []


def eval_case(name: str, description: str, expected_skill: str, skill_format: str, criteria: str):
    def decorator(func):
        EVAL_CASES.append({
            "name": name,
            "description": description,
            "expected_skill": expected_skill,
            "skill_format": skill_format,
            "criteria": criteria,
            "get_message": func,
        })
        return func
    return decorator


@eval_case(
    "eval-summarize-format",
    "Summarize skill produces bullet points with bold key points",
    expected_skill="Summarize",
    skill_format="Bullet points with **Key point** — explanation pattern. Should include action items if mentioned.",
    criteria="Never add information not in the source. Cap at 30% of original length. Preserve original tone.",
)
def eval_summarize():
    return (
        "Summarize this: Our Q3 results exceeded expectations with revenue of $42M, up 18% YoY. "
        "The enterprise segment grew 25% driven by three major deals. Consumer revenue declined 4% "
        "due to increased competition. We plan to double down on enterprise sales and explore strategic "
        "partnerships. Action items: hire 5 enterprise AEs, launch partner program by Q4."
    )


@eval_case(
    "eval-translate-format",
    "Translate skill uses Source/Target language headers and preserves proper nouns",
    expected_skill="Translate",
    skill_format="Must include **Source language:** and **Target language:** headers, followed by --- separator, translated text, --- separator, and optional Translation notes.",
    criteria="Preserve proper nouns and brand names. Never add content not in the original. For technical docs prefer accuracy over fluency.",
)
def eval_translate():
    return (
        "Translate to German: Microsoft Azure provides enterprise-grade cloud computing services. "
        "The AI Foundry platform enables developers to build intelligent agents using GPT-4o and other models."
    )


@eval_case(
    "eval-sentiment-format",
    "Sentiment skill outputs all 5 required sections with evidence citations",
    expected_skill="Analyze Sentiment",
    skill_format="Must have: **Overall Sentiment:**, **Confidence:**, **Emotions Detected:**, **Key Themes:**, **Summary:**",
    criteria="Always cite specific phrases as evidence. Distinguish product sentiment from experience sentiment. Never inject own opinion.",
)
def eval_sentiment():
    return (
        "Analyze sentiment: The onboarding process was smooth and the documentation is excellent. "
        "But the pricing is confusing — we got billed for features we didn't enable, and the support "
        "team took 3 days to respond. The product itself is solid though."
    )


@eval_case(
    "eval-sentiment-foreign",
    "Sentiment skill handles foreign text by translating first (skill composition)",
    expected_skill="Analyze Sentiment",
    skill_format="Must have all 5 sections. Should mention that analysis was on translated text.",
    criteria="If input is not English, translate first then analyze. Include note about translated text.",
)
def eval_sentiment_foreign():
    return "Analyze the sentiment: Ce produit est fantastique mais la livraison était catastrophique."


@eval_case(
    "eval-fallback",
    "Agent uses general knowledge and mentions no skill was needed",
    expected_skill="None/General Knowledge",
    skill_format="Should be a direct, factual answer without skill formatting.",
    criteria="Respond with general knowledge. Optionally mention no specific skill was used.",
)
def eval_fallback():
    return "What year was the Eiffel Tower built?"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_evals(filter_name: str = None):
    cases = EVAL_CASES
    if filter_name:
        cases = [c for c in cases if filter_name.lower() in c["name"].lower()]

    total = len(cases)
    results = []

    print(f"\n{'='*70}")
    print(f"  Foundry Skills — LLM-as-Judge Evaluation ({total} cases)")
    print(f"  Agent: {AGENT_NAME}")
    print(f"{'='*70}\n")

    for i, case in enumerate(cases, 1):
        name = case["name"]
        print(f"[{i}/{total}] {name}: {case['description']}")
        sys.stdout.write(f"       Invoking agent... ")
        sys.stdout.flush()

        start = time.time()
        user_msg = case["get_message"]()
        agent_response = invoke_agent(user_msg)
        agent_time = time.time() - start
        print(f"({agent_time:.1f}s)")

        sys.stdout.write(f"       Judging... ")
        sys.stdout.flush()

        start = time.time()
        verdict = judge_response(
            user_message=user_msg,
            agent_response=agent_response,
            expected_skill=case["expected_skill"],
            skill_format=case["skill_format"],
            criteria=case["criteria"],
        )
        judge_time = time.time() - start
        print(f"({judge_time:.1f}s)")

        skill_ok = verdict.get("skill_correct", False)
        fmt = verdict.get("format_score", 0)
        hal = verdict.get("hallucination_score", 0)
        rules = verdict.get("rule_compliance_score", 0)
        overall = verdict.get("overall_score", 0)
        reasoning = verdict.get("reasoning", "")

        status = "PASS" if overall >= 4 and skill_ok else "FAIL"
        print(f"       {status} | skill={'OK' if skill_ok else 'WRONG'} format={fmt}/5 hallucination={hal}/5 rules={rules}/5 overall={overall}/5")
        print(f"       Judge: {reasoning}")
        print()

        results.append({
            "name": name,
            "status": status,
            "skill_correct": skill_ok,
            "format_score": fmt,
            "hallucination_score": hal,
            "rule_compliance_score": rules,
            "overall_score": overall,
            "reasoning": reasoning,
        })

    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    avg_overall = sum(r["overall_score"] for r in results) / total if total else 0

    print(f"{'='*70}")
    print(f"  Results: {passed} passed, {failed} failed, {total} total")
    print(f"  Average overall score: {avg_overall:.1f}/5")
    print(f"{'='*70}")

    if failed > 0:
        print("\n  Failed cases:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"    x {r['name']}: {r['reasoning']}")

    return all(r["status"] == "PASS" for r in results)


if __name__ == "__main__":
    filter_arg = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_evals(filter_arg)
    sys.exit(0 if success else 1)
