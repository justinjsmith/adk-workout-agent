"""Run the Google OAuth2 Desktop flow to obtain a refresh token for Gmail API access."""

import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"


def main():
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: {CREDENTIALS_FILE} not found. Create it first.")
        return

    # Force Chrome as the browser
    os.environ["BROWSER"] = "open -a 'Google Chrome' %s"

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)

    print("Starting OAuth flow — Chrome will open for authorization...")
    creds = flow.run_local_server(port=8090)

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
    }

    TOKEN_FILE.write_text(json.dumps(token_data, indent=2))
    print(f"\nToken saved to {TOKEN_FILE}")
    print(f"Refresh token: {creds.refresh_token[:20]}...")
    print("Done! You can now use the Gmail API.")


if __name__ == "__main__":
    main()
