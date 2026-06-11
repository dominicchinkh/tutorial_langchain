from langchain.messages import AIMessage, HumanMessage, ToolMessage

response = {
    "messages": [
        HumanMessage(
            content="Create a hello world Python script in /tmp and run it",
            additional_kwargs={},
            response_metadata={},
            id="263a6d0c-16d0-4d06-aefd-da7a3d773486",
        ),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "name": "execute",
                    "arguments": '{"command": "python /tmp/hello.py"}',
                }
            },
            response_metadata={
                "finish_reason": "STOP",
                "model_name": "gemini-2.5-flash-lite",
                "safety_ratings": [],
                "model_provider": "google_genai",
            },
            id="lc_run--019e885a-f136-7762-a69e-afac1c6ae0e0-0",
            tool_calls=[
                {
                    "name": "write_file",
                    "args": {
                        "file_path": "/tmp/hello.py",
                        "content": 'print("Hello World!")',
                    },
                    "id": "9c085493-b2db-4fde-87fe-c3cb0839c5e4",
                    "type": "tool_call",
                },
                {
                    "name": "execute",
                    "args": {"command": "python /tmp/hello.py"},
                    "id": "1b7a6cec-1504-4be1-a174-199e19ba934a",
                    "type": "tool_call",
                },
            ],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 6622,
                "output_tokens": 51,
                "total_tokens": 6673,
                "input_token_details": {"cache_read": 0},
            },
        ),
        ToolMessage(
            content="Updated file /tmp/hello.py",
            name="write_file",
            id="0df999d1-762d-4dbc-8971-ccb77d7418f2",
            tool_call_id="9c085493-b2db-4fde-87fe-c3cb0839c5e4",
        ),
        ToolMessage(
            content="\n<stderr>python: can't open file '/tmp/hello.py': [Errno 2] No such file or directory</stderr>\n[Command failed with exit code 2]",
            name="execute",
            id="b11a073a-cbc8-42a8-9976-0852599f075b",
            tool_call_id="1b7a6cec-1504-4be1-a174-199e19ba934a",
        ),
        AIMessage(
            content="I encountered an error when trying to run the Python script. It seems the file `/tmp/hello.py` was not found. I will try writing the file again and then running it.",
            additional_kwargs={
                "function_call": {
                    "name": "execute",
                    "arguments": '{"command": "python /tmp/hello.py"}',
                }
            },
            response_metadata={
                "finish_reason": "STOP",
                "model_name": "gemini-2.5-flash-lite",
                "safety_ratings": [],
                "model_provider": "google_genai",
            },
            id="lc_run--019e885b-155d-7950-ae11-662cc230c71e-0",
            tool_calls=[
                {
                    "name": "write_file",
                    "args": {
                        "file_path": "/tmp/hello.py",
                        "content": 'print("Hello World!")',
                    },
                    "id": "94160135-a60d-486c-a851-8cb22823120e",
                    "type": "tool_call",
                },
                {
                    "name": "execute",
                    "args": {"command": "python /tmp/hello.py"},
                    "id": "2fc8639b-e6fe-4847-96ca-048d5c08657d",
                    "type": "tool_call",
                },
            ],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 6749,
                "output_tokens": 90,
                "total_tokens": 6839,
                "input_token_details": {"cache_read": 0},
            },
        ),
        ToolMessage(
            content="Error: File already exists: '/tmp/hello.py'",
            name="write_file",
            id="d27f9163-a153-4bf6-9092-00a8a2e99bb7",
            tool_call_id="94160135-a60d-486c-a851-8cb22823120e",
            status="error",
        ),
        ToolMessage(
            content="Hello World!\n\n[Command succeeded with exit code 0]",
            name="execute",
            id="1f201a78-062a-46aa-b3c8-b1241fe8cd32",
            tool_call_id="2fc8639b-e6fe-4847-96ca-048d5c08657d",
        ),
        AIMessage(
            content="Hello World!",
            additional_kwargs={},
            response_metadata={
                "finish_reason": "STOP",
                "model_name": "gemini-2.5-flash-lite",
                "safety_ratings": [],
                "model_provider": "google_genai",
            },
            id="lc_run--019e885b-2123-7b80-9d87-3a1aa159af2d-0",
            tool_calls=[],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 6853,
                "output_tokens": 3,
                "total_tokens": 6856,
                "input_token_details": {"cache_read": 0},
            },
        ),
    ]
}
