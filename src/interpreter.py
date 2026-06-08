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
            "content": "Calculate the fifth Fibonacci number"
        }]
    })

    return result

result = asyncio.run(get_number())
print(f"The number is: {result}")
