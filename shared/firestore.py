"""Firestore client singleton for the workout agent."""

from __future__ import annotations

from google.cloud import firestore

from shared.config import FIRESTORE_DATABASE, GCP_PROJECT_ID

_client: firestore.Client | None = None


def get_firestore_client() -> firestore.Client:
    """Return a cached Firestore client.

    Uses GCP_PROJECT_ID and FIRESTORE_DATABASE from config.
    Raises if credentials are unavailable.
    """
    global _client
    if _client is None:
        _client = firestore.Client(
            project=GCP_PROJECT_ID,
            database=FIRESTORE_DATABASE,
        )
    return _client
