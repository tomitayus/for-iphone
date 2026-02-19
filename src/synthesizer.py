"""
Synthesizer module.
Uses Claude to integrate all AI responses and generate a structured diagram.
"""

import os
import anthropic

from .ai_clients import MultiAIResult

SYNTHESIS_PROMPT = """\
あなたは情報統合の専門家です。以下の4つのAI（Claude, ChatGPT, Gemini, Grok）が
同じ質問に対して回答しました。これらを分析・統合してください。

## 質問
{question}

## 各AIの回答
{responses}

## タスク
以下のJSON形式で出力してください。他のテキストは一切含めないでください。

```json
{{
  "summary": "全体の統合要約（日本語、200字以内）",
  "consensus": ["全AIが一致している点1", "一致点2", ...],
  "differences": [
    {{"topic": "相違点のテーマ", "details": {{"Claude": "...", "ChatGPT": "...", "Gemini": "...", "Grok": "..."}}}}
  ],
  "unique_insights": [
    {{"provider": "AI名", "insight": "そのAIだけが言及した独自の視点"}}
  ],
  "reliability_notes": "情報の信頼性に関する注意点",
  "diagram_nodes": [
    {{"id": "node1", "label": "ノード名", "category": "consensus|difference|unique", "description": "説明"}}
  ],
  "diagram_edges": [
    {{"from": "node1", "to": "node2", "label": "関係性"}}
  ]
}}
```
"""


def _format_responses(result: MultiAIResult) -> str:
    parts = []
    for r in result.responses:
        status = f"(エラー: {r.error})" if r.error else f"({r.elapsed_sec:.1f}秒)"
        content = r.content if r.content else "[回答なし]"
        parts.append(f"### {r.provider} ({r.model}) {status}\n{content}")
    return "\n\n".join(parts)


async def synthesize(result: MultiAIResult) -> dict:
    """Use Claude to synthesize all AI responses into structured data."""
    import json

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required for synthesis")

    prompt = SYNTHESIS_PROMPT.format(
        question=result.question,
        responses=_format_responses(result),
    )

    client = anthropic.AsyncAnthropic(api_key=api_key)
    msg = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = msg.content[0].text

    # Extract JSON from markdown code block if present
    if "```json" in raw:
        raw = raw.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in raw:
        raw = raw.split("```", 1)[1].split("```", 1)[0]

    return json.loads(raw.strip())
