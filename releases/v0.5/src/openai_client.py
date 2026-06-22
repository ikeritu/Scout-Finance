"""
OpenAI client module.

This module prepares a safe wrapper for future OpenAI usage.

Current scope:
- Read OpenAI-related environment variables.
- Check whether OpenAI is enabled.
- Validate API key presence.
- Estimate whether a request would exceed configured budgets.
- Provide a client factory only when explicitly enabled.
- Provide safe placeholder behavior when disabled.

Not included in this phase:
- Real analysis prompts.
- Batch company analysis.
- Streamlit UI.
- Database cost writes.
- Prompt engineering logic.
- Automatic retries.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv


load_dotenv()


DEFAULT_LIGHT_MODEL = "gpt-5.4-mini"
DEFAULT_STRONG_MODEL = "gpt-5.5"


@dataclass(frozen=True)
class OpenAISettings:
    """
    OpenAI configuration values loaded from environment variables.
    """

    api_key: str | None
    model_light: str
    model_strong: str
    enable_openai: bool
    enable_strong_model: bool
    max_companies_per_run: int
    daily_budget_usd: float
    monthly_budget_usd: float


class OpenAIDisabledError(RuntimeError):
    """
    Raised when OpenAI usage is requested but ENABLE_OPENAI is false.
    """


class OpenAIConfigurationError(RuntimeError):
    """
    Raised when OpenAI is enabled but configuration is incomplete.
    """


class OpenAIBudgetError(RuntimeError):
    """
    Raised when a projected call would exceed configured budget limits.
    """


def _env_bool(name: str, default: bool = False) -> bool:
    """
    Read a boolean value from environment variables.
    """

    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"true", "1", "yes", "y", "si", "sí"}


def _env_int(name: str, default: int) -> int:
    """
    Read an integer value from environment variables.
    """

    value = os.getenv(name)

    if value is None or value.strip() == "":
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    """
    Read a float value from environment variables.
    """

    value = os.getenv(name)

    if value is None or value.strip() == "":
        return default

    try:
        return float(value)
    except ValueError:
        return default


def load_openai_settings() -> OpenAISettings:
    """
    Load OpenAI settings from environment variables.

    Returns
    -------
    OpenAISettings
        Configuration object.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if api_key is not None:
        api_key = api_key.strip() or None

    return OpenAISettings(
        api_key=api_key,
        model_light=os.getenv("OPENAI_MODEL_LIGHT", DEFAULT_LIGHT_MODEL).strip(),
        model_strong=os.getenv("OPENAI_MODEL_STRONG", DEFAULT_STRONG_MODEL).strip(),
        enable_openai=_env_bool("ENABLE_OPENAI", default=False),
        enable_strong_model=_env_bool("ENABLE_STRONG_MODEL", default=False),
        max_companies_per_run=_env_int("MAX_OPENAI_COMPANIES_PER_RUN", default=5),
        daily_budget_usd=_env_float("OPENAI_DAILY_BUDGET_USD", default=5.0),
        monthly_budget_usd=_env_float("OPENAI_MONTHLY_BUDGET_USD", default=50.0),
    )


def is_openai_enabled() -> bool:
    """
    Return whether OpenAI usage is enabled.
    """

    return load_openai_settings().enable_openai


def get_selected_model(use_strong_model: bool = False) -> str:
    """
    Return the selected model name.

    Strong model usage is only allowed when ENABLE_STRONG_MODEL=true.
    """

    settings = load_openai_settings()

    if use_strong_model and settings.enable_strong_model:
        return settings.model_strong

    return settings.model_light


def validate_openai_ready(use_strong_model: bool = False) -> None:
    """
    Validate whether OpenAI can be used.

    Raises
    ------
    OpenAIDisabledError
        If ENABLE_OPENAI is false.
    OpenAIConfigurationError
        If OpenAI is enabled but the API key is missing.
    OpenAIConfigurationError
        If strong model is requested but disabled.
    """

    settings = load_openai_settings()

    if not settings.enable_openai:
        raise OpenAIDisabledError(
            "OpenAI is disabled. Set ENABLE_OPENAI=true in .env to enable it."
        )

    if settings.api_key is None or settings.api_key == "your_openai_api_key_here":
        raise OpenAIConfigurationError(
            "OPENAI_API_KEY is missing or still set to the placeholder value."
        )

    if use_strong_model and not settings.enable_strong_model:
        raise OpenAIConfigurationError(
            "Strong model requested but ENABLE_STRONG_MODEL=false."
        )


def get_openai_client(use_strong_model: bool = False) -> Any:
    """
    Create and return an OpenAI client.

    The client is only created when OpenAI is explicitly enabled and configured.

    Parameters
    ----------
    use_strong_model:
        Whether the caller intends to use the strong model.

    Returns
    -------
    Any
        OpenAI client instance.
    """

    validate_openai_ready(use_strong_model=use_strong_model)

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise OpenAIConfigurationError(
            "The openai package is not installed. Run: pip install openai"
        ) from exc

    settings = load_openai_settings()

    return OpenAI(api_key=settings.api_key)


def estimate_request_cost(
    input_tokens: int,
    output_tokens: int,
    input_cost_per_1m: float = 0.0,
    output_cost_per_1m: float = 0.0,
) -> float:
    """
    Estimate request cost from token usage and configurable rates.

    Rates are intentionally passed as parameters to avoid hardcoding prices
    that may change over time.

    Parameters
    ----------
    input_tokens:
        Estimated input tokens.
    output_tokens:
        Estimated output tokens.
    input_cost_per_1m:
        Cost in USD per 1M input tokens.
    output_cost_per_1m:
        Cost in USD per 1M output tokens.

    Returns
    -------
    float
        Estimated cost in USD.
    """

    input_cost = (max(input_tokens, 0) / 1_000_000) * input_cost_per_1m
    output_cost = (max(output_tokens, 0) / 1_000_000) * output_cost_per_1m

    return round(input_cost + output_cost, 6)


def validate_budget(
    estimated_cost: float,
    spent_today: float = 0.0,
    spent_this_month: float = 0.0,
) -> None:
    """
    Validate estimated cost against configured daily and monthly budgets.

    Parameters
    ----------
    estimated_cost:
        Projected cost for the next operation.
    spent_today:
        Already consumed budget today.
    spent_this_month:
        Already consumed budget this month.

    Raises
    ------
    OpenAIBudgetError
        If daily or monthly budget would be exceeded.
    """

    settings = load_openai_settings()

    if spent_today + estimated_cost > settings.daily_budget_usd:
        raise OpenAIBudgetError(
            "Projected OpenAI usage would exceed the daily budget. "
            f"spent_today={spent_today}, estimated_cost={estimated_cost}, "
            f"daily_budget={settings.daily_budget_usd}"
        )

    if spent_this_month + estimated_cost > settings.monthly_budget_usd:
        raise OpenAIBudgetError(
            "Projected OpenAI usage would exceed the monthly budget. "
            f"spent_this_month={spent_this_month}, estimated_cost={estimated_cost}, "
            f"monthly_budget={settings.monthly_budget_usd}"
        )


def validate_company_limit(number_of_companies: int) -> None:
    """
    Validate that a run does not exceed MAX_OPENAI_COMPANIES_PER_RUN.

    Raises
    ------
    ValueError
        If number_of_companies is above the configured limit.
    """

    settings = load_openai_settings()

    if number_of_companies > settings.max_companies_per_run:
        raise ValueError(
            "Too many companies requested for OpenAI analysis. "
            f"requested={number_of_companies}, "
            f"limit={settings.max_companies_per_run}"
        )


def get_openai_status() -> dict[str, Any]:
    """
    Return safe OpenAI configuration status without exposing the API key.
    """

    settings = load_openai_settings()

    return {
        "enable_openai": settings.enable_openai,
        "api_key_defined": settings.api_key is not None,
        "api_key_looks_placeholder": settings.api_key == "your_openai_api_key_here",
        "model_light": settings.model_light,
        "model_strong": settings.model_strong,
        "enable_strong_model": settings.enable_strong_model,
        "selected_default_model": get_selected_model(use_strong_model=False),
        "selected_strong_model_if_requested": get_selected_model(use_strong_model=True),
        "max_companies_per_run": settings.max_companies_per_run,
        "daily_budget_usd": settings.daily_budget_usd,
        "monthly_budget_usd": settings.monthly_budget_usd,
    }


def disabled_response(reason: str | None = None) -> dict[str, Any]:
    """
    Return a standard response when OpenAI is disabled.

    This is useful for future modules that want to avoid crashing when
    ENABLE_OPENAI=false.
    """

    return {
        "enabled": False,
        "status": "disabled",
        "reason": reason or "OpenAI is disabled by configuration.",
        "analysis": None,
        "estimated_cost": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_hit": False,
    }


def safe_client_check(use_strong_model: bool = False) -> dict[str, Any]:
    """
    Run a safe readiness check without making any API call.

    Returns
    -------
    dict
        Readiness result.
    """

    try:
        validate_openai_ready(use_strong_model=use_strong_model)
    except (OpenAIDisabledError, OpenAIConfigurationError) as exc:
        return {
            "ready": False,
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        }

    return {
        "ready": True,
        "error_type": None,
        "message": "OpenAI is enabled and configured.",
    }


if __name__ == "__main__":
    print("OpenAI status:")
    status = get_openai_status()

    for key, value in status.items():
        print(f"- {key}: {value}")

    print("\nSafe readiness check:")
    readiness = safe_client_check(use_strong_model=False)

    for key, value in readiness.items():
        print(f"- {key}: {value}")

    print("\nBudget check demo:")
    estimated_cost = estimate_request_cost(
        input_tokens=2_000,
        output_tokens=800,
        input_cost_per_1m=0.0,
        output_cost_per_1m=0.0,
    )
    print(f"- estimated_cost: {estimated_cost}")

    try:
        validate_budget(
            estimated_cost=estimated_cost,
            spent_today=0.0,
            spent_this_month=0.0,
        )
        print("- budget_status: ok")
    except OpenAIBudgetError as exc:
        print(f"- budget_status: {exc}")

    print("\nDisabled response demo:")
    print(disabled_response())
