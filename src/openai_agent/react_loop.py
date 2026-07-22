import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE_DB = {
    "pune": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "new york": "America/New_York",
    "london": "Europe/London",
}

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
load_dotenv(env_path, override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Tool implementation with a "not found" case ---
WEATHER_DB = {
    "pune": "Sunny, 28°C",
    "mumbai": "Humid, 31°C",
    "delhi": "Hazy, 26°C",
}

def get_weather(location: str) -> dict:
    key = location.strip().lower()
    if key in WEATHER_DB:
        return {"status": "ok", "location": location, "weather": WEATHER_DB[key]}
    # Missing data — return a clear error, don't guess
    return {"status": "not_found", "location": location,
             "error": f"No weather data available for '{location}'."}


def get_timezone(location: str) -> dict:
    key = location.strip().lower()
    if key in TIMEZONE_DB:
        return {
            "status": "ok",
            "location": location,
            "timezone": TIMEZONE_DB[key]
        }

    return {
        "status": "not_found",
        "location": location,
        "error": f"No timezone data available for '{location}'."
    }


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location. Returns an error if the location is unknown.",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timezone",
            "description": "Get the timezone for a location. Returns an error if the location is unknown.",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        },
    }    





]

TOOL_IMPLEMENTATIONS = {
    "get_weather": get_weather,
    "get_timezone": get_timezone
}

SYSTEM_PROMPT = (
    "You are a helpful assistant. Use tools when needed. "
    "If a tool returns an error or 'not_found', tell the user honestly that the "
    "data isn't available — never guess or make up an answer."
)


def react_loop(question: str, max_steps: int = 5):
    print(f"\n=== Question: {question} ===")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for step in range(1, max_steps + 1):
        print(f"\n[Step {step}] Reasoning...")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
        )
        message = response.choices[0].message

        # No tool call → model is done reasoning, give final answer
        if not message.tool_calls:
            print("[Step %d] No tool call — final answer reached." % step)
            print("Answer:", message.content)
            return message.content

        # Tool call(s) present → Action phase
        messages.append(message)

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"[Step {step}] Action → {name}({args})")

            func = TOOL_IMPLEMENTATIONS.get(name)
            if func is None:
                observation = {"status": "error", "error": f"Unknown tool '{name}'"}
            else:
                observation = func(**args)

            print(f"[Step {step}] Observation → {observation}")

            # Feed observation back as the tool result — this is the "Repeat" part
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(observation),
            })

    print("[Stopped] Max steps reached without a final answer.")
    return None


if __name__ == "__main__":
    react_loop("What is the capital of France?")
    react_loop("What's the weather in Pune?")
    react_loop("What's the weather in Antarctica City?")  # triggers not_found
    react_loop("What timezone is Mumbai in?")
    react_loop("What timezone is Tokyo in?")  # not in TIMEZONE_DB — tests not_found path