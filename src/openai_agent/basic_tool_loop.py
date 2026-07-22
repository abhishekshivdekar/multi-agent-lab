import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from repo root, regardless of current working directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
load_dotenv(env_path, override=True)
print("Key loaded:", os.getenv("OPENAI_API_KEY")[:10] + "..." if os.getenv("OPENAI_API_KEY") else "NOT FOUND")
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

messages = [{"role": "user", "content": "What's the weather in Pune?"}]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)

message = response.choices[0].message

if message.tool_calls:
    tool_call = message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    result = get_weather(**args)

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
    print(final.choices[0].message.content)
else:
    print(message.content)