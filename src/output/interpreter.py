from langchain.messages import AIMessage, HumanMessage, ToolMessage

{
    "messages": [
        HumanMessage(
            content="Calculate the fifth Fibonacci number",
            additional_kwargs={},
            response_metadata={},
            id="1996bf29-9365-4646-8138-51ba8a85b81c",
        ),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "name": "eval",
                    "arguments": '{"code": "\\nfunction fibonacci(n) {\\n  if (n <= 1) {\\n    return n;\\n  }\\n  let a = 0, b = 1;\\n  for (let i = 2; i <= n; i++) {\\n    let temp = a + b;\\n    a = b;\\n    b = temp;\\n  }\\n  return b;\\n}\\nconsole.log(fibonacci(5));\\n"}',
                }
            },
            response_metadata={
                "finish_reason": "STOP",
                "model_name": "gemini-2.5-flash-lite",
                "safety_ratings": [],
                "model_provider": "google_genai",
            },
            id="lc_run--019ea943-63de-7d32-b4e8-6dd144045bc3-0",
            tool_calls=[
                {
                    "name": "eval",
                    "args": {
                        "code": "\nfunction fibonacci(n) {\n  if (n <= 1) {\n    return n;\n  }\n  let a = 0, b = 1;\n  for (let i = 2; i <= n; i++) {\n    let temp = a + b;\n    a = b;\n    b = temp;\n  }\n  return b;\n}\nconsole.log(fibonacci(5));\n"
                    },
                    "id": "ff375c6d-f107-4074-b649-5ec36676457f",
                    "type": "tool_call",
                }
            ],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 6705,
                "output_tokens": 111,
                "total_tokens": 6816,
                "input_token_details": {"cache_read": 0},
            },
        ),
        ToolMessage(
            content="<stdout>\n5\n</stdout>\n<result>null</result>",
            name="eval",
            id="04ab9353-ecce-442b-bc5d-44617f47790b",
            tool_call_id="ff375c6d-f107-4074-b649-5ec36676457f",
        ),
        AIMessage(
            content="The fifth Fibonacci number is 5.",
            additional_kwargs={},
            response_metadata={
                "finish_reason": "STOP",
                "model_name": "gemini-2.5-flash-lite",
                "safety_ratings": [],
                "model_provider": "google_genai",
            },
            id="lc_run--019ea943-6af1-74c2-a66e-c1c0c1b52804-0",
            tool_calls=[],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 6845,
                "output_tokens": 8,
                "total_tokens": 6853,
                "input_token_details": {"cache_read": 0},
            },
        ),
    ],
    "files": {},
}
