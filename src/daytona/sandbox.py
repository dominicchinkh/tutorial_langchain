"""
Daytona Remote Code Execution Runner.

What it does:
    Provisions a secure, isolated remote container (sandbox) using the Daytona 
    platform and evaluates an arbitrary string of Python code within that 
    isolated environment.

How:
    1. Loads the `DAYTONA_API_KEY` from a local `.env` file using `python-dotenv`.
    2. Authenticates and initializes the `Daytona` client with the API key.
    3. Requests the Daytona API to spin up a new runtime sandbox instance.
    4. Transmits a Python execution payload (`print(...)`) to the sandbox's 
       internal process manager (`sandbox.process.code_run`).
    5. Evaluates the returned execution object's exit status code to determine 
       whether to print the standard output stream or log an error.

Expected Outcome:
    On Success (Exit Code 0):
        Prints the standard output stream captured from the sandbox to the 
        local terminal:
        Hello world from code!

    On Failure (Non-zero Exit Code):
        Prints a formatted error string containing the non-zero status code 
        and the captured error or stack trace payload:
        Error: [exit_code] [error_message]

References:
    Official Documentation: https://www.daytona.io/docs/
"""
import os

from daytona import Daytona, DaytonaConfig
from dotenv import load_dotenv

# Load variables from .env into the system environment
load_dotenv()

# Define the configuration
config = DaytonaConfig(api_key=os.getenv("DAYTONA_API_KEY"))

# Initialize the Daytona client
daytona = Daytona(config)

# Create the sandbox instance
sandbox = daytona.create()

# Run the code securely inside the sandbox
response = sandbox.process.code_run('print("Hello world from code!")')

if response.exit_code != 0:
    print(f"Error: {response.exit_code} {response.result}")
else:
    print(response.result)

# Refer to https://www.daytona.io/docs/ for more information
