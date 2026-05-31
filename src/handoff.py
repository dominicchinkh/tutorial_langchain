"""
Customer Support Workflow Automation Agent

What it does:
    This program implements a multi-stage, stateful customer support agent 
    designed to guide a user through a structured device troubleshooting 
    and resolution funnel. It systematically transitions the interaction 
    through three distinct stages:
        1. Warranty Collection ('warranty_collector')
        2. Issue Classification ('issue_classifier')
        3. Resolution/Escalation ('resolution_specialist')

How it works:
    The application utilizes LangChain and LangGraph primitives to manage 
    dynamic prompts, tools, and execution state across separate conversation turns:
    
    * Stateful Tracking (SupportState): Inherits from AgentState to track custom 
      contextual variables (`current_step`, `warranty_status`, and `issue_type`)
      across the session.
    * Dynamic Middleware Architecture (apply_step_config): Intercepts LLM calls 
      using the `@wrap_model_call` decorator. It dynamically injects step-specific 
      system prompts and restricts the toolset available to the LLM based on 
      the `current_step` stored in memory.
    * State-Driven Tools: Rather than just returning plain strings, core workflow 
      tools (`record_warranty_status`, `record_issue_type`) return a LangGraph 
      `Command(update={...})` object. This forces an explicit state transition and 
      saves collected parameters into memory.
    * Persistence Layer (InMemorySaver): Leverages an in-memory checkpointer tied 
      to a unique `thread_id` (`state_schema=SupportState`) so that state variables 
      persist seamlessly across individual `.invoke()` calls.

Expected outcome:
    When executed, the program runs an end-to-end multi-turn simulation mimicking 
    a user reporting a cracked phone screen:
    
    * Turn 1: The agent greets the user and prompts for warranty details.
    * Turn 2: The user answers. The agent triggers `record_warranty_status`, 
              updates `warranty_status` to "in_warranty", transitions the 
              `current_step` to "issue_classifier", and asks the user to 
              describe the problem.
    * Turn 3: The user describes physical damage. The agent catches this, invokes 
              `record_issue_type` to log "hardware", updates `current_step` to 
              "resolution_specialist", and advances.
    * Turn 4: The agent assesses the collected state (In Warranty + Hardware 
              Issue), binds the `provide_solution` tool, and outputs instructions 
              detailing the warranty repair process (retail or mail-in options).
              
    Console outputs will display clean, step-by-step chat progress (via pretty_print)
    and explicitly verify state changes by printing the live `Current step` 
    at the end of each interaction turn.
"""

from dotenv import load_dotenv
from langchain_core.utils.uuid import uuid7
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, StateSnapshot
from typing import Callable, Literal

# It is a type hint used in Python to specify that a key in a TypedDict is optional
from typing_extensions import NotRequired 

load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

#---------------------
# Define custom state

# Define the possible workflow steps
SupportStep    = Literal["warranty_collector", "issue_classifier", "resolution_specialist"]
WarrantyStatus = Literal["in_warranty", "out_of_warranty"]
IssueType      = Literal["hardware", "software"]

class SupportState(AgentState):
    """State for customer support workflow"""
    current_step: NotRequired[SupportStep]
    warranty_status: NotRequired[WarrantyStatus]
    issue_type: NotRequired[IssueType]

#-----------------------------------------
# Create tools that manage workflow state

@tool
def record_warranty_status(
    status: WarrantyStatus,
    # Outputs nothing (None), and it manages a state of type SupportState
    runtime: ToolRuntime[None, SupportState] 
) -> Command:
    """Record the customer's warranty status and transition to issue classification."""
    return Command(
        update = {
            "messages": [
                ToolMessage(
                    content = f"Warranty status recorded as: {status}",
                    tool_call_id = runtime.tool_call_id
                )
            ],
            "warranty_status": status,
            "current_step": "issue_classifier"
        }
    )

@tool
def record_issue_type(
    issue_type: IssueType,
    runtime: ToolRuntime[None, SupportState]
) -> Command:
    """Record the type of issue and transition to resolution specialist."""
    return Command(
        update = {
            "messages": [
                ToolMessage(
                    content = f"Issue type recorded as: {issue_type}",
                    tool_call_id = runtime.tool_call_id
                )
            ],
            "issue_type": issue_type,
            "current_step": "resolution_specialist"
        }
    )

@tool
def escalate_to_human(reason: str) -> str:
    """Escalate the case to a human support specialist."""
    return f"Escalating to human support: Reason: {reason}"

@tool
def provide_solution(solution: str) -> str:
    """Provide a solution to the customer's issue."""
    return f"Solution provided: {solution}"

@tool
def go_back_to_warranty() -> Command:
    """Go back to warranty verification step."""
    return Command(update={"current_step": "warranty_collector"})

@tool
def go_back_to_classification() -> Command:
    """Go back to issue classification step."""
    return Command(update={"current_step": "issue_classifier"})

#----------------------------
# Define step configurations

# Define prompts as constants for easy reference
WARRANTY_COLLECTOR_PROMPT = """
    You are a customer support agent helping with device issues.

    CURRENT STAGE: Warranty verification

    At this step, you need to:
    1. Greet the customer warmly
    2. Ask if their device is under warranty
    3. Use record_warranty_status to record their response and move to the next step

    Be conversational and friendly. Don't ask multiple questions at once.
"""

ISSUE_CLASSIFIER_PROMPT = """
    You are a customer support agent helping with device issues.

    CURRENT STAGE: Issue classification
    CUSTOMER INFO: Warranty status is {warranty_status}

    At this step, you need to:
    1. Ask the customer to describe their issue
    2. Determine if it's a hardware issue (physical damage, broken parts) or software issue (app crashes, 
       performance)
    3. Use record_issue_type to record the classification and move to the next step

    If unclear, ask clarifying questions before classifying.
"""

RESOLUTION_SPECIALIST_PROMPT = """
    You are a customer support agent helping with device issues.

    CURRENT STAGE: Resolution
    CUSTOMER INFO: Warranty status is {warranty_status}, issue type is {issue_type}

    At this step, you need to:
    1. For SOFTWARE issues: provide troubleshooting steps using provide_solution
    2. For HARDWARE issues:
    - If IN WARRANTY: explain warranty repair process using provide_solution
    - If OUT OF WARRANTY: escalate_to_human for paid repair options

    If the customer indicates any information was wrong, use:
    - go_back_to_warranty to correct warranty status
    - go_back_to_classification to correct issue type

    Be specific and helpful in your solutions.
"""

# Step configuration: maps step name to (prompt, tools, required_state)

# This dictionary-based configuration makes it easy to:
#   * See all steps at a glance
#   * Add new steps (just add another entry)
#   * Understand the workflow dependencies (requires field)
#   * Use prompt templates with state variables (e.g., {warranty_status})

STEP_CONFIG = {
    "warranty_collector": {
        "prompt": WARRANTY_COLLECTOR_PROMPT,
        "tools": [record_warranty_status],
        "requires": []
    },
    "issue_classifier": {
        "prompt": ISSUE_CLASSIFIER_PROMPT,
        "tools": [record_issue_type],
        "requires": ["warranty_status"]
    },
    "resolution_specialist": {
        "prompt": RESOLUTION_SPECIALIST_PROMPT,
        "tools": [
            escalate_to_human, 
            provide_solution, 
            go_back_to_warranty, 
            go_back_to_classification
        ],
        "requires": ["warranty_status", "issue_type"]
    }
}

#------------------------------
# Create step-based middleware

@wrap_model_call
def apply_step_config(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Configure agent behavior based on the current step."""
    
    # Get current step (defaults to warranty_collector for first interaction)
    current_step = request.state.get("current_step", "warranty_collector")
    
    # Look up step configuration
    state_config = STEP_CONFIG[current_step]
    
    # Validate required state exists
    for key in state_config["requires"]:
        if request.state.get(key) is None:
            raise ValueError(f"{key} must be set before reaching {current_step}")
        
    # Format prompt with state values (supports {warranty_status}, {issue_type}, etc.)
    system_prompt = state_config["prompt"].format(**request.state)
    
    # Inject system prompt and step specific tools
    request = request.override(
        system_prompt = system_prompt,
        tools = state_config["tools"]
    )
    
    return handler(request)

#------------------
# Create the agent

# Collect all tools from all step configurations
all_tools = [
    record_warranty_status,
    record_issue_type,
    escalate_to_human,
    provide_solution,
    go_back_to_warranty, 
    go_back_to_classification
]

# Create the agent with step-based configuration
agent = create_agent(
    model,
    tools = all_tools,
    middleware = [apply_step_config],
    # The `checkpointer` maintains state across conversation turns. Without it, 
    # the `current_step` state would be lost between user messages, breaking the 
    # workflow.
    checkpointer = InMemorySaver(),
    # This tells create_agent to accept and track my custom keys `SupportState`
    state_schema = SupportState
)

#-------------------
# Test the workflow

def print_message(result) -> None:
    """Print messages"""
    for chunk in result:
        message = chunk["messages"][-1]
        
        if message.content:
            if isinstance(message, HumanMessage):
                print(f"User: {message.content}")
                
            elif isinstance(message, AIMessage):
                print(f"Agent: {message.content}")
                
        elif message.tool_calls:
            print(f"Calling tools: {[tc['name'] for tc in message.tool_calls]}")

def print_current_state(current_state: StateSnapshot) -> None:
    """Print agent current state"""

    # Fetch the actual live state from the checkpointer
    print(f"\nCurrent step: {current_state.values.get('current_step')}")
    print(f"Warranty status: {current_state.values.get('warranty_status')}")
    print(f"Issue type: {current_state.values.get('issue_type')}")

# Configuration for this conversation thread
thread_id = str(uuid7())
config = {
    "configurable": {
        "thread_id": thread_id
    }
}

# Turn 1: Initial message - starts with warranty_collector step
print("=== Turn 1: Warranty Collection ===")
result = agent.stream(
    {
        "messages": [HumanMessage(
            "Hi, my phone screen is cracked"
        )]
    }, 
    config=config,
    stream_mode="values"
)

print_message(result)
print_current_state(agent.get_state(config))

# Turn 2: User responds about warranty
print("\n=== Turn 2: Warranty Response ===")
result = agent.stream(
    {
        "messages": [
            HumanMessage("Yes, it's still under warranty")
        ]
    },
    config=config,
    stream_mode="values"
)

print_message(result)
print_current_state(agent.get_state(config))

# Turn 3: User describes the issue
print("\n=== Turn 3: Issue Description ===")
result = agent.stream(
    {
        "messages": [
            HumanMessage("The screen is physically cracked from dropping it")
        ]
    },
    config=config,
    stream_mode="values"
)

print_message(result)
print_current_state(agent.get_state(config))

# Turn 4: Resolution
print("\n=== Turn 4: Resolution ===")
result = agent.stream(
    {
        "messages": [
            HumanMessage("What should I do?")
        ]
    },
    config=config,
    stream_mode="values"
)

print_message(result)
print_current_state(agent.get_state(config))
