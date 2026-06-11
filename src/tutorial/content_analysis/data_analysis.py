"""
Multi-Agent Data Analytics and Visualization Workflow using Daytona Sandboxes.

What It Does
------------
This script orchestrates a secure, cloud-isolated data analysis workflow. It
spins up a remote Daytona development environment (sandbox), securely uploads a 
raw CSV dataset and a markdown-based skill manual, and invokes a middleware-driven 
LangChain agent. The agent processes the file, delegating specific sub-tasks 
(like chart generation) to specialized sub-agents, analyzes revenue metrics, 
and safely tears down the sandbox when finished.

How It Does It
--------------
1. Sandbox Isolation & Lifecycle: It initializes a `Daytona` client using 
   environment variables. It checks for an existing sandbox tied to a unique 
   `assistant_id`; if none exists, it provisions a new container sandbox from a 
   snapshot. A `finally` block ensures the sandbox is gracefully stopped to 
   prevent resource leaks.
2. Direct File Uploads: It mocks a sales dataset into an in-memory CSV buffer 
   and uses Daytona's native SDK filesystem manager (`sdk.fs.upload_file`) to 
   inject the data (`/tmp/sales.csv`) and a skills definition file directly 
   into the isolated container workspace.
3. Layered Agent Middleware: It constructs a core LangChain agent wrapped with 
   a robust middleware stack powered by `deepagents.middleware`:
   * `FilesystemMiddleware`: Exposes container read/write tools to the LLM.
   * `SummarizationMiddleware`: Manages and condenses heavy files or outputs.
   * `SkillsMiddleware`: Feeds the agent pre-defined domain expertise or code patterns.
   * `TodoListMiddleware`: Tracks execution state and planning.
   * `SubAgentMiddleware`: Registers a specialized `visualizer` sub-agent.
4. Orchestrated Execution: The main agent receives a prompt to read the file 
   and compute total product revenue. While answering, the primary LLM 
   (`gemini-2.5-flash-lite`) coordinates with its specialized `visualizer` 
   sub-agent - which is instructed to write `matplotlib`/`seaborn` scripts—to 
   complete the task within the sandbox environment.

Expected Outcome
----------------
Upon successful execution, the script yields a finalized text analysis printed to 
the console containing the calculated total revenue per product (e.g., Widget A, 
Widget B, Widget C). Because the visualizer sub-agent is registered and invoked via 
middleware, the underlying workspace container will also contain generated `.png` 
chart files representing the data distribution before the sandbox is halted.

"""
import csv, io, os

from daytona import \
    CreateSandboxFromSnapshotParams, Daytona, DaytonaConfig

from deepagents import SubAgent
from deepagents.middleware import \
        FilesystemMiddleware, SkillsMiddleware, SubAgentMiddleware, SummarizationMiddleware

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain_daytona import DaytonaSandbox

# Load variables from .env into the system environment
load_dotenv()

# Define the configuration
config = DaytonaConfig(api_key=os.getenv("DAYTONA_API_KEY"))

# Initialize the Daytona client
client = Daytona(config)

# Define the configuration required
assistant_id = "my-unique-assistant-123"

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

# Upload a CSV and invoke
rows = [
    ["Date", "Product", "Units", "Revenue"],
    ["2025-08-01", "Widget A", 10, 250],
    ["2025-08-02", "Widget B", 5, 125],
    ["2025-08-03", "Widget A", 7, 175],
    ["2025-08-04", "Widget C", 3, 90],
]
buf = io.StringIO()
csv.writer(buf).writerows(rows)

# 1. Grab the native client
sdk = backend._sandbox

# 2. Upload using the native filesystem manager (takes string data directly)
sdk.fs.upload_file(buf.getvalue().encode(), "/tmp/sales.csv")
sdk.fs.upload_file('../skills/pandas-patterns/SKILL.md', "/tmp/skills/pandas-patterns/SKILL.md")

model = "google_genai:gemini-2.5-flash-lite"

visualizer: SubAgent = {
    "name": "visualizer",
    "model": model,
    "description": "Generates charts and visualizations from data files in the sandbox.",
    "system_prompt": 
        "You are a data visualization specialist." 
        "Write Python scripts using matplotlib and seaborn."
        "Save all figures as PNG files.",
    "tools": [],
}

try:
    # The agent
    agent = create_agent(
        model=model,
        tools=[],
        middleware=[
            FilesystemMiddleware(backend=backend),
            SummarizationMiddleware(model=model, backend=backend),
            SkillsMiddleware(backend=backend, sources=["/tmp/skills"]),
            TodoListMiddleware(),
            SubAgentMiddleware(backend=backend, subagents=[visualizer])
        ]
    )

    result = agent.invoke({
        "messages": [{
            "role": "user", 
            "content": 
                "I have uploaded the sales data to the workspace at `/tmp/sales.csv`. "
                "Please read this file using your filesystem tools and analyze the "
                "total revenue generated by each product."
        }]
    })

    print(result);
    
finally:
    if sandbox is not None:
        # If the Daytona client is async, you must 'await' the stop method:
        print("Stopping sandbox...")
        sandbox.stop()
        print("Sandbox stopped successfully.")
