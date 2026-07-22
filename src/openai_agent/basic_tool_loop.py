import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from repo root, regardless of current working directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
load_dotenv(env_path, override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_weather(location: str) -> str:
    # placeholder — replace with a real API call later
    return f"It's sunny and 28°C in {location}."


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        },
    }
]


def ask(question: str):
    print(f"\n--- Question: {question} ---")

    messages = [{"role": "user", "content": question}]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )

    message = response.choices[0].message

    if message.tool_calls:
        # 2. Tool call branch — model decided it needs a function
        tool_call = message.tool_calls[0]
        print(f"[Tool call made] → {tool_call.function.name}({tool_call.function.arguments})")

        args = json.loads(tool_call.function.arguments)
        result = get_weather(**args)
        print(f"[Tool result] → {result}")

        messages.append(message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

        final = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
        )
        print("Answer:", final.choices[0].message.content)

    else:
        # 1. Generic question branch — no tool needed, model just answers
        print("[No tool call — answered directly]")
        print("Answer:", message.content)


# 1. Generic question — no tool needed
ask("What is the capital of France?")

# 2. Tool-requiring question — triggers get_weather
ask("What's the weather in Pune?")