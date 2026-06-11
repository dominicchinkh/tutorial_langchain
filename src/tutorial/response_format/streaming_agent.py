"""
streaming_agent.py — Streaming Agent Output

What it does:
    Demonstrates how to stream an agent's execution step-by-step, showing
    intermediate messages and tool calls as they happen rather than waiting
    for the final result.

How it works:
    1. Loads environment variables from a .env file.
    2. Creates a LangChain agent using the Gemini 2.5 Flash Lite model with a
       simple system prompt.
    3. Streams the agent's response to a user query using `stream_mode="values"`,
       which yields the full conversation state after each step.
    4. For each chunk, extracts the latest message and prints it — showing user
       messages, AI responses, and tool calls as they occur.

Expected outcome:
    The agent processes the query "Search for AI news and summarize the findings",
    printing each step in real time: the original user message, any tool calls
    the agent makes, and the final AI summary response.
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.human import HumanMessage

# Load variables from .env into the system environment
load_dotenv()

agent = create_agent(
    model="google_genai:gemini-2.5-flash-lite",
    system_prompt="You are a helpful assistant",
)

for chunk in agent.stream({
    "messages": [{
        "role": "user", 
        "content": "Search for AI news and summarize the findings"
    }]},
    stream_mode="values"):
    
    # Each chunk contains the full state at that point
    latest_message = chunk["messages"][-1]
    
    if latest_message.content:
        
        if isinstance(latest_message, HumanMessage):
            print(f"User: {latest_message.content}")
            
        elif isinstance(latest_message, AIMessage):
            print(f"Agent: {latest_message.content}")
            
    elif latest_message.tool_calls:
        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
