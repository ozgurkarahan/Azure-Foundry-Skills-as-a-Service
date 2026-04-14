"""Inspect agent response to verify FileSearchTool traces."""

import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from src.agent.config import PROJECT_ENDPOINT, AGENT_NAME


def inspect_response(message: str):
    client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    openai = client.get_openai_client()

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

    print(f"User: {message}\n")
    print(f"{'='*70}")
    print(f"Response has {len(response.output)} output items")
    print(f"{'='*70}\n")

    for i, item in enumerate(response.output):
        item_type = getattr(item, "type", "unknown")
        print(f"--- Item {i}: type={item_type} ---")

        if item_type == "file_search_call":
            print(f"  id: {getattr(item, 'id', '?')}")
            print(f"  status: {getattr(item, 'status', '?')}")
            queries = getattr(item, "queries", [])
            print(f"  queries: {queries}")
            results = getattr(item, "results", None) or []
            print(f"  results: {len(results)} files matched")
            for r in results:
                fname = getattr(r, "filename", "?")
                score = getattr(r, "score", "?")
                text = getattr(r, "text", "")
                preview = text[:200] + "..." if len(text) > 200 else text
                print(f"    [{score:.3f}] {fname}")
                print(f"           {preview}")
            print()

        elif item_type == "message":
            for c in getattr(item, "content", []):
                if hasattr(c, "text"):
                    print(f"  Agent response:")
                    print(f"  {c.text[:500]}")
            print()

        else:
            # Dump unknown types
            if hasattr(item, "model_dump"):
                d = item.model_dump()
                print(f"  {json.dumps(d, indent=2, default=str)[:500]}")
            print()


if __name__ == "__main__":
    import sys

    tests = [
        ("Translate to French: Hello, how are you today?", "TRANSLATE"),
        ("Summarize: AI is transforming every industry. Companies are investing billions.", "SUMMARIZE"),
        ("Analyze the sentiment: I absolutely hate waiting in long lines.", "SENTIMENT"),
        ("What is 2+2?", "FALLBACK (no skill)"),
    ]

    if len(sys.argv) > 1:
        # Single custom message
        inspect_response(" ".join(sys.argv[1:]))
    else:
        for msg, label in tests:
            print(f"\n{'#'*70}")
            print(f"# TEST: {label}")
            print(f"{'#'*70}\n")
            inspect_response(msg)
