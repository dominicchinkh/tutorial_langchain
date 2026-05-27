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
