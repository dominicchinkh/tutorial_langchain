"""
agent.py — Basic LangChain Agent with a Tool

What it does:
    Demonstrates how to create a simple LangChain agent that can use a custom tool
    (get_weather) to answer user questions.

How it works:
    1. Loads environment variables (e.g. API keys) from a .env file.
    2. Defines a `get_weather` tool that returns a hardcoded sunny forecast.
    3. Creates a LangChain agent using the Gemini 2.5 Flash Lite model, wired up
       with the tool and a basic system prompt.
    4. Invokes the agent with a user message asking about the weather in Canberra.

Expected outcome:
    The agent calls the `get_weather` tool and prints a response indicating
    "It's always sunny in Canberra!" (or a natural-language answer incorporating
    that tool result).
"""

from dotenv import load_dotenv
from langchain.agents import create_agent

# Load variables from .env into the system environment
load_dotenv()

def get_weather(city: str) -> str:
    """Get weather for a given city"""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="google_genai:gemini-2.5-flash-lite",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    { 
        "messages": [
            { 
                "role": "user", 
                "content": "What is the weather in Canberra?"
            }
        ]
    }
)

print(result["messages"][-1].content_blocks)
