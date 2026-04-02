"""Batch parse test fixtures to evaluate parser quality.

Usage:
    uv run python scripts/batch_parse.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from google.adk.runners import InMemoryRunner
from google.genai import types

from agent.parser_agent import parser_agent

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "emails"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "parse_results"


async def parse_single(fixture_path: Path) -> dict:
    """Parse a single fixture and return results."""
    data = json.loads(fixture_path.read_text())
    label = data["label"]

    print(f"\n{'='*60}")
    print(f"Parsing: {label} ({data['date'][:10]})")
    print(f"Subject: {data['subject'][:60]}")
    print(f"Body: {len(data['body'])} chars")
    print(f"{'='*60}")

    prompt = (
        f"Parse this swim workout email into a structured Workout JSON object.\n\n"
        f"Subject: {data['subject']}\n"
        f"Date: {data['date']}\n"
        f"Email Message ID: {data['message_id']}\n"
        f"Thread ID: {data['thread_id']}\n\n"
        f"Body:\n{data['body']}"
    )

    runner = InMemoryRunner(agent=parser_agent, app_name="batch_parse")
    session = await runner.session_service.create_session(
        app_name="batch_parse", user_id="batch"
    )

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    tool_calls = []
    agent_text = []

    start = time.time()

    for event in runner.run(
        user_id="batch",
        session_id=session.id,
        new_message=content,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    agent_text.append(part.text)
                elif part.function_call:
                    tool_calls.append(part.function_call.name)
                    print(f"  🔧 {part.function_call.name}")

    elapsed = time.time() - start

    result = {
        "label": label,
        "date": data["date"][:10],
        "elapsed_seconds": round(elapsed, 1),
        "tool_calls": tool_calls,
        "agent_response_length": sum(len(t) for t in agent_text),
        "agent_response": "\n".join(agent_text),
    }

    print(f"  ⏱ {elapsed:.1f}s | Tools: {', '.join(tool_calls)}")
    return result


async def main():
    fixtures = sorted(FIXTURES_DIR.glob("*.json"))
    if not fixtures:
        print(f"No fixtures found in {FIXTURES_DIR}")
        return

    print(f"Found {len(fixtures)} fixtures to parse")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for fixture in fixtures:
        try:
            result = await parse_single(fixture)
            results.append(result)

            # Save individual result
            result_path = RESULTS_DIR / f"{result['label']}_result.json"
            result_path.write_text(json.dumps(result, indent=2))
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append({"label": fixture.stem, "error": str(e)})

    # Summary
    print(f"\n\n{'='*60}")
    print("BATCH PARSE SUMMARY")
    print(f"{'='*60}")
    total_time = sum(r.get("elapsed_seconds", 0) for r in results)
    successes = sum(1 for r in results if "error" not in r)
    print(f"Total: {len(results)} | Success: {successes} | Failed: {len(results)-successes}")
    print(f"Total time: {total_time:.1f}s | Avg: {total_time/len(results):.1f}s per email")
    for r in results:
        status = "✅" if "error" not in r else "❌"
        elapsed = r.get("elapsed_seconds", 0)
        tools = ", ".join(r.get("tool_calls", []))
        print(f"  {status} {r['label']:30s} {elapsed:5.1f}s  tools=[{tools}]")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
