"""
Fibonacci Calculation via an Advanced Code-Interpreter Agent.

This script demonstrates how to initialize and execute a programmatic agent 
capable of writing and executing its own internal code to solve problems, rather 
than relying on iterative, step-by-step LLM reasoning loops.

How it works:
    1. Agent Creation: It instantiates a `deepagents` instance powered by the 
       `gemini-2.5-flash-lite` model.
    2. Programmable Tool Call (PTC) Middleware: It attaches a JavaScript-based 
       `CodeInterpreterMiddleware` via `langchain_quickjs`. This gives the agent 
       an in-memory QuickJS sandbox. Instead of making multiple round-trips to 
       the LLM for complex logic, the model generates a concise script to handle 
       the control flow and arithmetic internally.
    3. Asynchronous Execution: Because PTC bridges register as asynchronous 
       host functions within the QuickJS runtime, the script utilizes `ainvoke` 
       to prevent `ConcurrentEvalError` exceptions.
    4. Task Resolution: The agent is prompted to find the "fifth Fibonacci number". 
       It writes the logic inside its interpreter sandbox, executes it, and passes 
       the final result back.

Expected Outcome:
    When executed, the agent will internally compute the 5th Fibonacci number 
    (which is 5, assuming the sequence 1, 1, 2, 3, 5, 8, 13, 21, 34, 55). The 
    script will print the final return payload from the agent to the console:
    
    `The number is: [Agent Response Object/String containing 55]`
"""
import asyncio

from deepagents import create_deep_agent
from langchain_quickjs import CodeInterpreterMiddleware

agent = create_deep_agent(
    model="google_genai:gemini-2.5-flash-lite",
    
    # Interpreters give agents a programmable workspace where they can explore 
    # data, coordinate tool calls, and keep intermediate work out of the model 
    # context. The agent writes code to express its intent, then an in-memory 
    # runtime executes that code and returns the relevant results.
    
    # Instead of asking the model to choose every next step one tool call at a 
    # time, the agent can write a small program that runs control flow, calls 
    # allowlisted tools, stores variables, and returns a compact result to the 
    # model.
    
    middleware=[CodeInterpreterMiddleware(ptc=[
        "task"
    ])]
)

async def get_number() -> int:
    # Use `ainvoke` — PTC bridges register as async QuickJS host functions,
    # and sync `invoke` on a REPL with async bridges raises ConcurrentEvalError.
    result = await agent.ainvoke({
        "messages": [{
            "role": "user", 
            "content": "Calculate the tenth Fibonacci number"
        }]
    })

    return result

result = asyncio.run(get_number())
print(f"The number is: {result}")
