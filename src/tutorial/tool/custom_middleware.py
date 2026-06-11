"""
Agent Tool Execution Interception using Decorator-Based Middleware.

What It Does
------------
This script demonstrates how to implement cross-cutting concerns (such as 
logging, auditing, or metrics collection) during an AI agent's execution lifecycle. 
It intercepts tool-calling requests made by the language model, captures metadata 
about the tool and its arguments before execution, and logs the outcome post-execution 
without altering the core tool logic itself.

How It Does It
--------------
1. Tool Definition: It creates a mock weather retrieval tool (`get_weather`) 
   using LangChain's `@tool` decorator.
2. Interception Hook: It utilizes the `@wrap_tool_call` decorator to define a 
   middleware function (`log_tool_calls`). This function acts as an around-advice 
   wrapper that:
   * Increments a global execution counter (`call_count`).
   * Inspects the incoming request object to extract the tool's name and arguments.
   * Forwards the execution payload to the underlying tool via the `handler(request)` callback.
   * Captures and logs the completion state before passing the result back to the LLM.
3. Agent Configuration: It instantiates a DeepAgent powered by `gemini-2.5-flash-lite`, 
   explicitly binding the `get_weather` tool and routing its execution pipeline through the 
   `log_tool_calls` middleware array.
4. Execution: When invoked with a query regarding Canberra, the model triggers a 
   tool call, which automatically routes through the logging decorator before and 
   after executing the weather function.

Expected Outcome
----------------
The script will print real-time intercept telemetry to the standard output as the 
agent reasons about the user request.

Example Console Output:
    Invoke agent...
    [Middleware] Tool call #1: get_weather
    [Middleware] Arguments: {'city': 'Canberra'}
    [Middleware] Tool call #1 completed
"""
from langchain.agents.middleware import wrap_tool_call
from langchain.tools import tool
from deepagents import create_deep_agent

@tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny."

call_count = [0]  # Use list to allow modification in nested function

@wrap_tool_call
def log_tool_calls(request, handler):
    """Intercept and log every tool call - demonstrates cross-cutting concern."""
    
    call_count[0] += 1
    tool_name = request.name if hasattr(request, "name") else str(request)

    print(f"[Middleware] Tool call #{call_count[0]}: {tool_name}")
    print(f"[Middleware] Arguments: {request.args if hasattr(request, 'args') else 'N/A'}")

    # Execute the tool call
    result = handler(request)

    # Log the result
    print(f"[Middleware] Tool call #{call_count[0]} completed")

    return result

model = "google_genai:gemini-2.5-flash-lite"

agent = create_deep_agent(
    model=model,
    tools=[get_weather],
    middleware=[log_tool_calls],
)

print("Invoke agent...")
result = agent.invoke(
    {
        "messages": [{
            "role": "user",
            "content": "How is Canberra weather?"
        }]
    }
)
