"""HTTP-only FastAPI client for Whitfield CLI commands."""

from dataclasses import dataclass
from typing import Any

import httpx


EXIT_CODES = {401: 3, 403: 4, 404: 5, 409: 6, 422: 7}


class CLIError(Exception):
    """Represent a normalized, client-safe FastAPI or network failure."""

    def __init__(self, message: str, exit_code: int) -> None:
        """Store a safe display message and deterministic CLI exit code.

        Args:
            message: Client-safe error message.
            exit_code: Process exit code for scripts.
        """
        super().__init__(message)
        self.exit_code = exit_code


@dataclass
class APIClient:
    """Call existing Whitfield FastAPI endpoints with an optional bearer token."""

    api_url: str
    token: str | None
    timeout: float = 15.0

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, payload: dict[str, Any] | None = None, authenticated: bool = True) -> Any:
        """Send one bounded HTTP request and normalize its response.

        Args:
            method: HTTP method supported by the existing FastAPI route.
            path: Route path beginning with `/`.
            params: Optional query parameters with nulls omitted.
            payload: Optional JSON request body.
            authenticated: Whether a bearer token is required for this route.

        Returns:
            Any: Parsed JSON response from the backend.

        Raises:
            CLIError: For authentication, authorization, domain, or network failures.
        """
        if authenticated and not self.token:
            raise CLIError("Authentication required. Run `whitfield auth login` first.", 3)
        headers = {"Authorization": f"Bearer {self.token}"} if authenticated and self.token else {}
        clean_params = {key: value for key, value in (params or {}).items() if value is not None}
        try:
            response = httpx.request(method, f"{self.api_url.rstrip('/')}{path}", headers=headers, params=clean_params, json=payload, timeout=self.timeout)
        except httpx.RequestError as error:
            raise CLIError("Whitfield WMS is unavailable. Check the API URL and backend status.", 8) from error
        if response.is_success:
            return response.json() if response.content else None
        detail = _detail(response)
        if response.status_code == 401:
            message = "Authentication required or session expired. Run `whitfield auth login`."
        elif response.status_code == 403:
            message = f"Access denied: {detail}"
        elif response.status_code == 404:
            message = f"Not found: {detail}"
        elif response.status_code == 409:
            message = f"Business conflict: {detail}"
        elif response.status_code == 422:
            message = f"Invalid request: {detail}"
        else:
            message = "Whitfield WMS returned an unexpected server error."
        raise CLIError(message, EXIT_CODES.get(response.status_code, 1))


def _detail(response: httpx.Response) -> str:
    """Extract a bounded backend detail value without exposing implementation data.

    Args:
        response: Failed HTTP response from FastAPI.

    Returns:
        str: Safe error detail suitable for terminal display.
    """
    try:
        detail = response.json().get("detail", "Request failed")
    except ValueError:
        return "Request failed"
    if isinstance(detail, list):
        return "; ".join(str(item.get("msg", "Invalid value")) for item in detail[:3])
    return str(detail)
