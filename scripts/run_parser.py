"""CLI script to test the workout parser against real Gmail emails.

Usage:
    uv run python scripts/run_parser.py                    # Fetch & parse latest coach email
    uv run python scripts/run_parser.py --list             # List recent coach emails
    uv run python scripts/run_parser.py --id <message_id>  # Parse a specific email
    uv run python scripts/run_parser.py --text             # Parse workout text from stdin
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load .env before any imports that need env vars (LiteLLM reads ANTHROPIC_API_KEY)
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from agent.root_agent import root_agent  # noqa: E402
from agent.tools.gmail import fetch_coach_emails, fetch_email_by_id  # noqa: E402


async def run_agent(user_message: str) -> None:
    """Run the root agent with a user message and print the response."""
    runner = InMemoryRunner(agent=root_agent, app_name="workout_agent")

    user_id = "dev_user"
    session = await runner.session_service.create_session(
        app_name="workout_agent", user_id=user_id
    )

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    )

    print("\n--- Agent Processing ---\n")

    # InMemoryRunner.run() returns a sync Generator but create_session is async
    for event in runner.run(
        user_id=user_id,
        session_id=session.id,
        new_message=content,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)
                elif part.function_call:
                    print(f"\n🔧 Tool call: {part.function_call.name}")
                elif part.function_response:
                    resp_text = str(part.function_response.response)
                    if len(resp_text) > 200:
                        resp_text = resp_text[:200] + "..."
                    print(f"   → {resp_text}")

    print("\n--- Done ---\n")


def cmd_list(args):
    """List recent emails from the coach."""
    print(f"Fetching up to {args.max} recent emails from coach...")
    emails = fetch_coach_emails(max_results=args.max)

    if not emails:
        print("No emails found from coach.")
        return

    for i, email in enumerate(emails):
        print(f"\n[{i+1}] {email['subject']}")
        print(f"    ID: {email['message_id']}")
        print(f"    Date: {email['date']}")
        body_preview = email["body"][:150].replace("\n", " ")
        print(f"    Preview: {body_preview}...")


def cmd_parse_latest(args):
    """Fetch and parse the latest coach email."""
    print("Fetching latest email from coach...")
    emails = fetch_coach_emails(max_results=1)

    if not emails:
        print("No emails found from coach.")
        return

    email = emails[0]
    print(f"Found: {email['subject']} ({email['date']})")
    print(f"Body length: {len(email['body'])} chars")
    print(f"\n--- Email Body ---\n{email['body']}\n--- End ---\n")

    prompt = (
        f"Parse this swim workout email.\n\n"
        f"Subject: {email['subject']}\n"
        f"Date: {email['date']}\n"
        f"Email Message ID: {email['message_id']}\n"
        f"Thread ID: {email['thread_id']}\n\n"
        f"Body:\n{email['body']}"
    )

    asyncio.run(run_agent(prompt))


def cmd_parse_id(args):
    """Parse a specific email by ID."""
    print(f"Fetching email {args.id}...")
    email = fetch_email_by_id(args.id)

    print(f"Found: {email['subject']} ({email['date']})")

    prompt = (
        f"Parse this swim workout email.\n\n"
        f"Subject: {email['subject']}\n"
        f"Date: {email['date']}\n"
        f"Email Message ID: {email['message_id']}\n"
        f"Thread ID: {email['thread_id']}\n\n"
        f"Body:\n{email['body']}"
    )

    asyncio.run(run_agent(prompt))


def cmd_parse_stdin(args):
    """Parse workout text from stdin."""
    print("Enter workout text (Ctrl+D when done):")
    text = sys.stdin.read()

    prompt = f"Parse this swim workout text directly:\n\n{text}"
    asyncio.run(run_agent(prompt))


def main():
    parser = argparse.ArgumentParser(description="Test the workout parser agent")
    parser.add_argument("--list", action="store_true", help="List recent coach emails")
    parser.add_argument("--id", type=str, help="Parse a specific email by Gmail message ID")
    parser.add_argument("--text", action="store_true", help="Parse workout text from stdin")
    parser.add_argument("--max", type=int, default=10, help="Max emails to list (default: 10)")

    args = parser.parse_args()

    if args.list:
        cmd_list(args)
    elif args.id:
        cmd_parse_id(args)
    elif args.text:
        cmd_parse_stdin(args)
    else:
        cmd_parse_latest(args)


if __name__ == "__main__":
    main()
