"""Safe user-local session helpers for the Whitfield CLI."""

import json
import os
from pathlib import Path


def session_path() -> Path:
    """Return the user-local CLI session location.

    Stores a short-lived access token outside the repository and never stores a password.

    Returns:
        Path: User-local JSON session path.
    """
    root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Whitfield"
    return root / "cli-session.json"


def load_token() -> tuple[str | None, str | None]:
    """Load an access token from environment or the user-local session file.

    Environment configuration takes precedence so automation can avoid a session file.

    Returns:
        tuple[str | None, str | None]: Token and its safe source label.
    """
    token = os.getenv("WHITFIELD_TOKEN")
    if token:
        return token, "environment"
    path = session_path()
    if not path.is_file():
        return None, None
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get("access_token")
        return value if isinstance(value, str) and value else None, "local session"
    except (OSError, json.JSONDecodeError):
        return None, None


def save_token(token: str) -> None:
    """Persist an access token in the user-local session directory.

    Args:
        token: Authenticated access token returned by FastAPI.
    """
    path = session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"access_token": token}), encoding="utf-8")


def clear_token() -> None:
    """Remove the user-local session token when it exists."""
    path = session_path()
    if path.exists():
        path.unlink()
