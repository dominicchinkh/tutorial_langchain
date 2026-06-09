from langchain.messages import AIMessage, HumanMessage, ToolMessage

{
    "messages": [
        HumanMessage(
            content="Calculate the tenth Fibonacci number",
            additional_kwargs={},
            response_metadata={},
            id="7528021a-d65f-4c1e-9250-d9c76d210992",
        ),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "name": "eval",
                    "arguments": """{"code": "\
                        function fibonacci(n) {\
                            if (n <= 1) {\
                                return n;\
                            }\
                            let a = 0, b = 1;\
                            for (let i = 2; i <= n; i++) {\
                                let temp = a + b;\
                                a = b;\
                                b = temp;\
                            }\
                            return b;\
                        }\
                        console.log(fibonacci(10));\
                    "}""",
                }
            },
            response_metadata={
                "finish_reason": "STOP",
                "model_name": "gemini-2.5-flash-lite",
                "safety_ratings": [],
                "model_provider": "google_genai",
            },
            id="lc_run--019eabab-ca77-7d83-9561-a1fe9fc91e37-0",
            tool_calls=[
                {
                    "name": "eval",
                    "args": {
                        "code": """
                            function fibonacci(n) {
                                if (n <= 1) {
                                    return n;
                                }
                                let a = 0, b = 1;
                                for (let i = 2; i <= n; i++) {
                                    let temp = a + b;
                                    a = b;
                                    b = temp;
                                }
                                return b;
                            }
                            console.log(fibonacci(10));
                        """
                    },
                    "id": "0bb91447-f089-4c51-8dea-965c7da22fb5",
                    "type": "tool_call",
                }
            ],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 6705,
                "output_tokens": 112,
                "total_tokens": 6817,
                "input_token_details": {"cache_read": 0},
            },
        ),
        ToolMessage(
            content="<stdout>55</stdout><result>null</result>",
            name="eval",
            id="43a5c868-3355-49f0-9c08-dec0ee7304df",
            tool_call_id="0bb91447-f089-4c51-8dea-965c7da22fb5",
        ),
        AIMessage(
            content="The tenth Fibonacci number is 55.",
            additional_kwargs={},
            response_metadata={
                "finish_reason": "STOP",
                "model_name": "gemini-2.5-flash-lite",
                "safety_ratings": [],
                "model_provider": "google_genai",
            },
            id="lc_run--019eabab-d1d3-7f40-b3b9-09acecadbd2d-0",
            tool_calls=[],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 6847,
                "output_tokens": 9,
                "total_tokens": 6856,
                "input_token_details": {"cache_read": 0},
            },
        ),
    ],
    "files": {},
}
