"""Test script to invoke the Foundry Skills agent."""

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from src.agent.config import PROJECT_ENDPOINT, AGENT_NAME


def invoke_agent(message: str) -> str:
    """Send a message to the agent and return the response text."""
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

    parts = []
    for item in response.output:
        if hasattr(item, "content"):
            for c in item.content:
                if hasattr(c, "text"):
                    parts.append(c.text)
    return "\n".join(parts)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = "What skills do you have available?"

    print(f"User: {message}\n")
    print(f"Agent:\n{invoke_agent(message)}")
