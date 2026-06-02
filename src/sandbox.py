"""
Persistent LLM Agent Orchestration with Isolated Daytona Sandbox.

What it does:
    Initializes a persistent or fresh remote Daytona sandbox, binds it to a 
    LangChain-compatible execution backend, and pairs it with a Deep Agent 
    driven by Gemini 2.5 Flash Lite to safely compile, execute, and verify 
    Python scripts inside an isolated environment.

How:
    1. Loads infrastructure credentials via `dotenv` and instantiates the Daytona client.
    2. Uses `get_agent_and_sandbox()` to query the Daytona API for an existing sandbox 
       matching a specific `assistant_id` label. If none is found, a new container is 
       instantiated from a snapshot.
    3. Wraps the active container inside a `DaytonaSandbox` instance to act as the tool 
       execution backend layer.
    4. Compiles a Deep Agent using `google_genai:gemini-2.5-flash-lite`, assigning the 
       Daytona backend as its execution runtime.
    5. Invokes the agent synchronously via `agent.invoke()`, blocking local thread 
       execution while the LLM issues terminal commands to write and run code inside the container.
    6. Ensures strict infrastructure lifecycle management by tearing down the remote 
       compute resources using a `try...finally` block that calls `sandbox.stop()`.

Expected Outcome:
    Terminal logs will trace the structural setup, synchronous agent blocking, the LLM's 
    final evaluation text, and a graceful shutdown sequence:

    Getting agent and sandbox...
    Invoke agent...
    Agent Response: [Sample output in src/output/sandbox.py]
    Stopping sandbox...
    Sandbox stopped successfully.

References:
    - Daytona APIs & Lifecycle: https://www.daytona.io/docs/
    - LangChain Runnables Interface: https://python.langchain.com/
"""
import os

from daytona import CreateSandboxFromSnapshotParams, Daytona, DaytonaConfig
from dotenv import load_dotenv

from langchain_core.runnables import RunnableConfig
from langchain_daytona import DaytonaSandbox
from deepagents import create_deep_agent

# Load variables from .env into the system environment
load_dotenv()

# Define the configuration
config = DaytonaConfig(api_key=os.getenv("DAYTONA_API_KEY"))

# Initialize the Daytona client
client = Daytona(config)

def get_agent_and_sandbox(config: RunnableConfig):
    assistant_id = config["configurable"]["assistant_id"]

    try:
        sandbox = client.find_one(
            labels={
                "assistant_id": assistant_id
            }
        )
    
    except Exception:
        sandbox = client.create(
            CreateSandboxFromSnapshotParams(labels={"assistant_id": assistant_id})
        )

    # Create a sandbox backend
    backend = DaytonaSandbox(sandbox=sandbox)
    
    agent = create_deep_agent(
        model="google_genai:gemini-2.5-flash-lite",
        tools=[],
        system_prompt="You are a Python coding assistant with sandbox access.",
        backend=backend
    )
        
    return agent, sandbox

def main():
    # Define the configuration required
    run_config = {
        "configurable": {
            "assistant_id": "my-unique-assistant-123"
        }
    }
    
    sandbox = None
    
    try:
        print("Getting agent and sandbox...")
        agent, sandbox = get_agent_and_sandbox(run_config)

        # Invoke the agent
        print("Invoke agent...")
        result = agent.invoke(
            {
                "messages": [{
                    "role": "user",
                    "content": "Create a hello world Python script in /tmp and run it"
                }]
            }
        )
        
        print("Agent Response:", result)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        if sandbox is not None:
            # If the Daytona client is async, you must 'await' the stop method:
            print("Stopping sandbox...")
            sandbox.stop()
            print("Sandbox stopped successfully.")
    

if __name__ == '__main__':
    main()
