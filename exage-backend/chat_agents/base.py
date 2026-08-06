import json
import time

from openai import AsyncOpenAI

from config import settings


client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url="https://openrouter.ai/api/v1",
)


async def call_llm(
    system_prompt: str,
    user_content: str,
    expect_json: bool = True,
) -> tuple:
    start = time.monotonic()

    kwargs = {
        "model": settings.model,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }

    if expect_json:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)

    latency_ms = int((time.monotonic() - start) * 1000)
    raw = response.choices[0].message.content or ""

    if expect_json:
        cleaned = raw.strip()

        # Some models wrap JSON in Markdown code fences.
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        return json.loads(cleaned), latency_ms

    return raw, latency_ms