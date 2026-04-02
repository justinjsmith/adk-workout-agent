# adk-workout-agent

A Google ADK agent that monitors Gmail for swim workout emails, parses them into structured format, and serves them through a web UI for viewing and printing.

## Setup

```bash
# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Run web app locally
uv run flask --app web.app run

# Run tests
uv run pytest
```

## Architecture

See [SPEC.md](SPEC.md) for the full product specification.
