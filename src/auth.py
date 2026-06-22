"""
Authentication module.

This module provides simple password validation for the private MVP.

Current scope:
- Read APP_PASSWORD from environment/config.
- Validate a plain password entered by the user.
- Provide minimal helpers for future Streamlit integration.

Not included in this phase:
- User accounts.
- Roles and permissions.
- Password hashing.
- OAuth.
- Sessions.
- Streamlit UI.
"""

from __future__ import annotations

import hmac
import os
from typing import Any

from dotenv import load_dotenv


load_dotenv()


DEFAULT_INSECURE_PASSWORD = "change_me"


def get_app_password() -> str | None:
    """
    Return the configured application password.

    The password is read from the APP_PASSWORD environment variable,
    usually loaded from .env.

    Returns
    -------
    str | None
        Configured password or None if not set.
    """

    password = os.getenv("APP_PASSWORD")

    if password is None:
        return None

    password = password.strip()

    if password == "":
        return None

    return password


def is_auth_configured() -> bool:
    """
    Return whether a non-default application password is configured.

    Returns
    -------
    bool
        True if APP_PASSWORD exists and is not the default placeholder.
    """

    password = get_app_password()

    if password is None:
        return False

    return password != DEFAULT_INSECURE_PASSWORD


def validate_password(candidate_password: str | None) -> bool:
    """
    Validate a candidate password against APP_PASSWORD.

    Uses hmac.compare_digest to avoid simple timing differences.

    Parameters
    ----------
    candidate_password:
        Password provided by the user.

    Returns
    -------
    bool
        True if the password matches, otherwise False.
    """

    configured_password = get_app_password()

    if configured_password is None:
        return False

    if candidate_password is None:
        return False

    candidate = str(candidate_password).strip()

    return hmac.compare_digest(candidate, configured_password)


def get_auth_status() -> dict[str, Any]:
    """
    Return a compact authentication configuration status.

    This is useful for diagnostics without exposing the password.

    Returns
    -------
    dict
        Authentication status.
    """

    password = get_app_password()

    return {
        "app_password_defined": password is not None,
        "uses_default_password": password == DEFAULT_INSECURE_PASSWORD,
        "auth_configured": is_auth_configured(),
    }


def require_configured_auth() -> None:
    """
    Raise an error if authentication is not properly configured.

    This can be called by future entry points before launching a private app.

    Raises
    ------
    RuntimeError
        If APP_PASSWORD is missing or still set to the default placeholder.
    """

    status = get_auth_status()

    if not status["app_password_defined"]:
        raise RuntimeError(
            "APP_PASSWORD is not defined. Create a .env file from .env.example."
        )

    if status["uses_default_password"]:
        raise RuntimeError(
            "APP_PASSWORD is still set to the default placeholder. "
            "Change it in your .env file before using the private app."
        )


if __name__ == "__main__":
    status = get_auth_status()

    print("Authentication status:")
    for key, value in status.items():
        print(f"- {key}: {value}")

    print("\nPassword validation demo:")
    print("- Empty password accepted:", validate_password(""))
    print("- Default placeholder accepted:", validate_password(DEFAULT_INSECURE_PASSWORD))

    if not status["auth_configured"]:
        print(
            "\nWarning: authentication is not securely configured yet. "
            "Set APP_PASSWORD in your .env file before using a private interface."
        )
