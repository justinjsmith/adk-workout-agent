"""Centralized configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Google Cloud
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "adk-workout-agent")
FIRESTORE_DATABASE = os.getenv("FIRESTORE_DATABASE", "(default)")

# Gmail
COACH_EMAIL = os.getenv("COACH_EMAIL", "")
USER_EMAIL = os.getenv("USER_EMAIL", "")
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Model identifiers for ADK (uses LiteLLM provider format)
MODEL_SONNET = "anthropic/claude-sonnet-4-20250514"
MODEL_HAIKU = "anthropic/claude-haiku-4-5-20251001"

# Flask
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me")
