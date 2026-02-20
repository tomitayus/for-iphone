#!/usr/bin/env python3
"""
Multi-AI Diagram Automation
============================
Send the same question to Claude, ChatGPT, Gemini, and Grok in parallel,
synthesize the responses, generate an interactive HTML diagram,
and send notifications.

Usage:
  python main.py "Your question here"
  python main.py --file questions.txt
  python main.py --interactive
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent / ".env")

from src.ai_clients import ask_all
from src.synthesizer import synthesize
from src.renderer import render_html
from src.notifier import notify_all


async def process_question(question: str, output_path: str | None = None, notify: bool = True) -> str:
    """Full pipeline: ask -> synthesize -> render -> notify."""

    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}\n")

    # Step 1: Ask all AIs in parallel
    print("[1/4] Sending question to Claude, ChatGPT, Gemini, Grok...")
    result = await ask_all(question)

    for r in result.responses:
        status = f"OK ({r.elapsed_sec:.1f}s)" if not r.error else f"ERROR: {r.error}"
        print(f"  {r.provider}: {status}")

    # Step 2+3: Generate HTML diagram directly with Claude Opus 4.6
    print("\n[2/4] Generating diagram with Claude Opus 4.6...")
    html_content = await synthesize(result)
    print(f"  HTML generated ({len(html_content):,} chars)")

    # Step 3: Save HTML to file
    print("\n[3/4] Saving HTML diagram...")
    html_path = render_html(result, html_content, output_path)
    abs_path = os.path.abspath(html_path)
    print(f"  Saved to: {abs_path}")

    # Step 4: Notify
    if notify:
        print("\n[4/4] Sending notifications...")
        # Use public URL if configured, otherwise use file path
        public_base = os.environ.get("PUBLIC_BASE_URL", "")
        if public_base:
            html_url = f"{public_base.rstrip('/')}/{Path(html_path).name}"
        else:
            html_url = f"file://{abs_path}"

        notify_result = await notify_all(
            subject=question[:60],
            html_url=html_url,
            summary=f"4つのAIによる図解分析: {question[:100]}",
        )

        if notify_result.get("email"):
            print("  Email: sent")
        if notify_result.get("webhook"):
            print("  Webhook: sent")
        if notify_result.get("reminder"):
            print("  Reminder: added")
    else:
        print("\n[4/4] Notifications skipped.")

    print(f"\n{'='*60}")
    print(f"Done! Open the diagram: file://{abs_path}")
    print(f"{'='*60}\n")

    return html_path


async def interactive_mode():
    """Interactive REPL for asking questions."""
    print("\nMulti-AI Diagram Automation - Interactive Mode")
    print("Type your question and press Enter. Type 'quit' to exit.\n")

    while True:
        try:
            question = input("Question> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not question or question.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        await process_question(question)


async def batch_mode(filepath: str):
    """Process questions from a file (one per line)."""
    lines = Path(filepath).read_text(encoding="utf-8").strip().splitlines()
    questions = [l.strip() for l in lines if l.strip() and not l.startswith("#")]

    print(f"Processing {len(questions)} questions from {filepath}...\n")

    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i}/{len(questions)} ---")
        await process_question(question)


def main():
    parser = argparse.ArgumentParser(
        description="Multi-AI Diagram Automation: Query 4 AIs, synthesize, diagram, notify.",
    )
    parser.add_argument("question", nargs="?", help="The question to ask all AIs")
    parser.add_argument("--file", "-f", help="File with questions (one per line)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--output", "-o", help="Output HTML file path")
    parser.add_argument("--no-notify", action="store_true", help="Skip notifications")
    parser.add_argument("--server", action="store_true", help="Start Web API server")
    parser.add_argument("--host", default="127.0.0.1", help="Server bind host")
    parser.add_argument("--port", type=int, default=8000, help="Server bind port")

    args = parser.parse_args()

    if args.server:
        from server import start_server
        start_server(args.host, args.port)
    elif args.interactive:
        asyncio.run(interactive_mode())
    elif args.file:
        asyncio.run(batch_mode(args.file))
    elif args.question:
        asyncio.run(process_question(args.question, args.output, not args.no_notify))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
