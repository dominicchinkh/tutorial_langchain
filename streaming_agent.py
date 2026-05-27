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

for chunk in agent.stream({"messages": [{"role": "user", "content": "Search for AI news and summarize the findings"}]}, stream_mode="values"):
    
    # Each chunk contains the full state at that point
    latest_message = chunk["messages"][-1]
    
    if latest_message.content:
        
        if isinstance(latest_message, HumanMessage):
            print(f"User: {latest_message.content}")
            
        elif isinstance(latest_message, AIMessage):
            print(f"Agent: {latest_message.content}")
            
    elif latest_message.tool_calls:
        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
