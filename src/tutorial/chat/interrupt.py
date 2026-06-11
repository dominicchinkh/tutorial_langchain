"""
Multi-Agent Human-in-the-Loop (HITL) Interrupt and Execution Demonstration.

What it does:
    This script demonstrates an advanced orchestration pattern using LangGraph and LangChain 
    where a primary 'parent' agent coordinates file system operations and subagent jobs, 
    while enforcing Human-in-the-Loop constraints. It showcases two distinct paradigms for 
    interrupting an execution loop to gather human consensus:
    
    1. Automated Middleware Interrupts: Triggered automatically whenever specific sensitive tools 
       (e.g., `remove_file`) are targeted.
    2. Manual/Explicit Tool Interrupts: Declared explicitly inside a tool (`request_approval`) 
       using the LangGraph `interrupt()` primitive.

How it works:
    1. State Persistence: An `InMemorySaver` checkpointer is instantiated to capture and save 
       the state thread across steps, allowing safe suspension and resumption points.
       
    2. Architecture & Delegation:
       - Parent Agent: A high-level orchestrator (`gemini-3.5-flash`) handling file management, 
         email alerts, and subagent routing. It maps framework policy rules (`interrupt_on`) 
         specifying which actions demand human approval.
       - Subagent (approval-agent): A targeted subagent (`gemini-2.5-flash-lite`) dedicated 
         to assessing administrative approvals using an explicit `request_approval` utility.
         
    3. Hook & Trap Loop: The application issues a multi-part prompt demanding destructive file 
       actions and a subagent invocation. When the framework catches an action matching the 
       `interrupt_on` schema, execution freezes and bubbles a state snapshot up to the runtime loop.
       
    4. Programmatic Resume: The `main()` routine traps the pending interrupt, unpacks the 
       context configurations (allowed decisions, parameters, action schemas), automatically appends 
       an approval verdict payload, and uses `Command(resume=...)` to safely kickstart execution 
       from where it was frozen.

Expected outcome:
    - The script initializes and runs the parent agent, triggering a middleware block as soon 
      as the agent attempts to resolve the "Delete temp.txt" task via `remove_file`.
      
    - A log entry resembling the following is printed to stdout:
        Interrupt received
          Type: None
          Action: None
          Message: None
          Tool: remove_file
          Arguments: {'path': 'temp.txt'}
          Allowed decisions: ['approve', 'edit', 'reject', 'respond']

    - The local runtime loop constructs a structured response stating `{"type": "approve"}` 
      and passes it back to the graph.
      
    - The framework yields and completes the execution, printing a termination output:
        Resuming with approval...
        
        Execution completed
          Tool result: ...
        
"""
from dotenv import load_dotenv

from deepagents.graph import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent

from langchain_core.utils.uuid import uuid7
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

load_dotenv()

@tool
def remove_file(path: str) -> str:
    """Delete a file from the file system."""
    return f"Deleted {path}"

@tool
def fetch_file(path: str) -> str:
    """Read a file from the file system."""
    return f"Contents of {path}"

@tool 
def notify_email(to:str, subject: str, body: str) -> str:
    """Send an email."""
    return f"Sent email to {to} with the subject '{subject}'"

@tool(description="Request human approval before proceeding with an action.")
def request_approval(action_description: str) -> str:
    """Request human approval using the interrupt() primitive."""
    
    approval = interrupt({
        "type": "approval_request",
        "action": action_description,
        "message": f"Please approve or reject {action_description}"
    })
    
    if approval.get("approved"):
        return f"Action '{action_description}' was APPROVED. Proceeding..."
    else:
        return f"Action '{action_description}' was REJECTED. Reason: {approval.get('reason', 'No reason provided')}"

def main():
    # Human-in-the-loop requires a checkpointer to persist agent state between the interrupt and resume
    checkpointer = InMemorySaver()

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        max_tokens=4096
    )

    subagent = create_agent(
        model=model,
        tools=[request_approval],
        name="approval-agent"
    )
    
    parent_agent = create_deep_agent(
        model="google_genai:gemini-3.5-flash",
        tools=[fetch_file, notify_email, remove_file],
        interrupt_on={
            "remove_file": True,  # Default: approve, edit, reject, respond
            "fetch_file": False,  # No interrupts needed
            "notify_email": {"allowed_decisions": ["approve", "reject"]},  # No editing
        },
        checkpointer=checkpointer,
        subagents=[
            CompiledSubAgent(
                name="approval-agent",
                description="An agent that can request approvals",
                runnable=subagent,
                
                # Each subagent can have its own interrupt_on configuration that overrides the main agent’s settings
                tools=[fetch_file, remove_file],
                interrupt_on={
                    # Override: require approval for reads in this subagent
                    "delete_file": True,
                    "read_file": True,  # Different from parent agent!
                }
            )
        ]
    )
    
    # When resuming, you must use the same config with the same thread_id
    thread_config = {
        "configurable": {
            "thread_id": str(uuid7())
        }
    }
    
    print("Invoking agent - sub-agent will use request_approval tool...")
    
    result = parent_agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=
                      "Delete temp.txt and send an email to admin@example.com"
                      "Use the task tool to launch the approval-agent sub-agent. "
                      "Tell it to use the request_approval tool to request approval for 'deploying to production'."
                )
            ]
        },
        config=thread_config,
        version="v2",
    )
    
    # Check for interrupt
    if result.interrupts:
        
        while result.interrupts:
            resume = { "decisions": []}
            
            # The decisions list must match the order of action_requests
            for interrupt in result.interrupts:
                interrupt_value = interrupt.value

                print(f"\nInterrupt received")
                print(f"  Type: {interrupt_value.get('type')}")
                print(f"  Action: {interrupt_value.get('action')}")
                print(f"  Message: {interrupt_value.get('message')}")
                
                interrupt_id    = interrupt_value.get("id", "")
                action_requests = interrupt_value.get("action_requests", [])
                review_configs  = interrupt_value.get("review_configs", [])
                
                config_map = {cfg["action_name"]: cfg for cfg in review_configs}
                
                for action in action_requests:
                    review_config = config_map[action['name']]
                    print(f"  Tool: {action['name']}")
                    print(f"  Arguments: {action['args']}")
                    print(f"  Allowed decisions: {review_config['allowed_decisions']}")
                
                resume["decisions"].append({
                    "type": "approve"
                })
            
            print("\nResuming with approval...")
            
            result=parent_agent.invoke(
                Command(resume=resume),
                config=thread_config,
                version="v2"
            )
            
            if not result.interrupts:
                print(f"\nExecution completed")
                
                # Find the tool response
                tool_messages = [m for m in result.value.get('messages', []) if m.type == 'tool']
                if tool_messages:
                    print(f"  Tool result: {tool_messages[-1].content}")

    else:
        print("\n  no interrupt - the model may not have called request_approval")

if __name__ == '__main__':
    main()
