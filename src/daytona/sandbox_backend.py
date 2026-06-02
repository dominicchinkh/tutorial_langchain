"""
Daytona Sandbox Backend Driver for LangChain & Deep Agents.

What it does:
    Provisions a secure, remote Daytona sandbox and wraps it using the 
    `langchain_daytona` execution adapter. This enables LLM-driven agents 
    (such as Deep Agents) to securely run shell commands and manage state 
    inside an isolated environment.

How:
    1. Loads the authentication credentials (`DAYTONA_API_KEY`) from the local 
       `.env` file using `python-dotenv`.
    2. Initializes the base `Daytona` orchestration client with the configuration.
    3. Spins up a fresh runtime container instance via `daytona.create()`.
    4. Wraps the low-level sandbox instance inside a `DaytonaSandbox` backend 
       adapter, translating LangChain/Deep Agent tool execution calls into 
       container actions.
    5. Dispatches a basic shell command (`echo hello`) through the backend to 
       test connectivity and outputs the captured standard terminal stream.

Expected Outcome:
    On successful initialization and command execution, the remote instance 
    evaluates the string and prints its captured output directly to your local 
    terminal interface:
    
    hello

References:
    - LangChain Integrations: https://python.langchain.com/
    - Daytona Sandbox API Documentation: https://www.daytona.io/docs/
"""
import os

from daytona import Daytona, DaytonaConfig
from dotenv import load_dotenv

from langchain_daytona import DaytonaSandbox

# Load variables from .env into the system environment
load_dotenv()

# Define the configuration
config = DaytonaConfig(api_key=os.getenv("DAYTONA_API_KEY"))

# Initialize the Daytona client
daytona = Daytona(config)

# Create the sandbox instance
sandbox = daytona.create()

# Create a sandbox backend
backend = DaytonaSandbox(sandbox=sandbox)
result = backend.execute("echo hello")
print(result.output)

# Use with deep agents
