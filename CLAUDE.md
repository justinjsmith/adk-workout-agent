# adk-workout-agent

Swim workout email parser built with Google ADK + Anthropic LLMs.

## Project Structure

- `agent/` — Google ADK agents
  - `root_agent.py` — Orchestrator: routes emails to triage → parser
  - `triage_agent.py` — Haiku classifier: workout vs logistics email
  - `parser_agent.py` — Sonnet parser: converts workout text to structured JSON
  - `prompts/parser.py` — System prompts for triage and parser agents
  - `tools/gmail.py` — Gmail API: fetch emails, strip reply chains
  - `tools/conventions.py` — Load abbreviation/rule knowledge base
  - `tools/validation.py` — Structural validation and flag_unknown
  - `tools/storage.py` — Store parsed workouts (local JSON → Firestore later)
- `shared/` — Shared code
  - `config.py` — Env var loading, model names, paths
  - `schema.py` — Pydantic models: Workout, Section, SetItem, Conventions, etc.
- `web/` — Flask web app (not yet implemented)
- `tests/` — Tests (pytest)
- `conventions/seed.json` — Initial abbreviation mappings and structural rules
- `scripts/` — Dev scripts
  - `oauth_flow.py` — Google OAuth2 Desktop flow for Gmail access
  - `run_parser.py` — CLI to test agent against real emails

## Commands

- `uv run python -m pytest tests/ -v` — run tests
- `uv run python -m ruff check .` — lint
- `uv run python -m ruff format .` — format
- `uv run python scripts/run_parser.py --list` — list recent coach emails
- `uv run python scripts/run_parser.py` — fetch & parse latest coach email
- `uv run python scripts/run_parser.py --id <msg_id>` — parse specific email

## Key Decisions

- **LLMs:** Anthropic models via LiteLLM (Haiku for triage/cleanup/validation, Sonnet for parsing/learning)
- **Orchestration:** Google ADK with sub-agents (triage → parser)
- **Storage:** Phase 1 = local JSON files in data/workouts/; Phase 2+ = Firestore
- **Deployment:** Cloud Run (future)
- **Package manager:** uv
- **Gmail:** OAuth2 Desktop flow, token in token.json (gitignored)

## Environment

Secrets and config in `.env` (gitignored). See `.env.example` for template.
Required: `ANTHROPIC_API_KEY`, `COACH_EMAIL`, `GCP_PROJECT_ID`.
OAuth credentials: `credentials.json` + `token.json` (both gitignored).
