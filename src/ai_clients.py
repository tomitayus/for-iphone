"""
Multi-AI API client module.
Calls Claude, ChatGPT, Gemini, and Grok in parallel with the same question.
"""

import asyncio
import os
import time
from dataclasses import dataclass, field

import anthropic
import openai
import httpx

try:
    import google.generativeai as genai
except ImportError:
    genai = None


@dataclass
class AIResponse:
    provider: str
    model: str
    content: str
    elapsed_sec: float
    error: str | None = None


@dataclass
class MultiAIResult:
    question: str
    responses: list[AIResponse] = field(default_factory=list)
    timestamp: str = ""


# ── Individual provider calls ──────────────────────────────────────

async def call_claude(question: str, model: str = "claude-sonnet-4-20250514") -> AIResponse:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return AIResponse("Claude", model, "", 0, "ANTHROPIC_API_KEY not set")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    start = time.monotonic()
    try:
        msg = await client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": question}],
        )
        content = msg.content[0].text
        return AIResponse("Claude", model, content, time.monotonic() - start)
    except Exception as e:
        return AIResponse("Claude", model, "", time.monotonic() - start, str(e))


async def call_chatgpt(question: str, model: str = "gpt-4o") -> AIResponse:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return AIResponse("ChatGPT", model, "", 0, "OPENAI_API_KEY not set")

    client = openai.AsyncOpenAI(api_key=api_key)
    start = time.monotonic()
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": question}],
            max_tokens=4096,
        )
        content = resp.choices[0].message.content or ""
        return AIResponse("ChatGPT", model, content, time.monotonic() - start)
    except Exception as e:
        return AIResponse("ChatGPT", model, "", time.monotonic() - start, str(e))


async def call_gemini(question: str, model: str = "gemini-2.0-flash") -> AIResponse:
    api_key = os.environ.get("GOOGLE_AI_API_KEY")
    if not api_key:
        return AIResponse("Gemini", model, "", 0, "GOOGLE_AI_API_KEY not set")
    if genai is None:
        return AIResponse("Gemini", model, "", 0, "google-generativeai not installed")

    genai.configure(api_key=api_key)
    gen_model = genai.GenerativeModel(model)
    start = time.monotonic()
    try:
        resp = await asyncio.to_thread(gen_model.generate_content, question)
        content = resp.text
        return AIResponse("Gemini", model, content, time.monotonic() - start)
    except Exception as e:
        return AIResponse("Gemini", model, "", time.monotonic() - start, str(e))


async def call_grok(question: str, model: str = "grok-3") -> AIResponse:
    """Call xAI Grok via their OpenAI-compatible API."""
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        return AIResponse("Grok", model, "", 0, "XAI_API_KEY not set")

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=120) as http:
            resp = await http.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": question}],
                    "max_tokens": 4096,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
        return AIResponse("Grok", model, content, time.monotonic() - start)
    except Exception as e:
        return AIResponse("Grok", model, "", time.monotonic() - start, str(e))


# ── Parallel execution ─────────────────────────────────────────────

async def ask_all(question: str) -> MultiAIResult:
    """Send the same question to all 4 AIs in parallel."""
    from datetime import datetime, timezone

    tasks = [
        call_claude(question),
        call_chatgpt(question),
        call_gemini(question),
        call_grok(question),
    ]
    responses = await asyncio.gather(*tasks)

    return MultiAIResult(
        question=question,
        responses=list(responses),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
