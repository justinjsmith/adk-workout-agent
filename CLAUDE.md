# adk-workout-agent

Swim workout email parser built with Google ADK + Anthropic LLMs.

## Project Structure

- `agent/` — Google ADK agents (email monitor, workout parser, learning agent)
- `agent/tools/` — ADK tool definitions (conventions, validation, storage)
- `agent/prompts/` — Prompt templates for the parser agent
- `web/` — Flask web app (workout viewer, review UI, print layout)
- `shared/` — Shared code (Pydantic schema, Firestore client, config)
- `tests/` — Tests and fixtures
- `conventions/` — Seed data for the conventions system

## Commands

- `uv run pytest` — run tests
- `uv run ruff check .` — lint
- `uv run ruff format .` — format
- `uv run flask --app web.app run` — run web app locally

## Key Decisions

- **LLMs:** Anthropic models via LiteLLM (Haiku for triage/cleanup/validation, Sonnet for parsing/learning)
- **Orchestration:** Google ADK
- **Storage:** Firestore
- **Deployment:** Cloud Run
- **Package manager:** uv
