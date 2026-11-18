"""Validated read-only access to AHledger's WoW Forever API.

Data is transient: API responses must not be archived without the appropriate licence.
See https://ahledger.com/developers#terms
"""
from datetime import datetime, timezone
import re

import requests

BASE_URL = "https://api.ahledger.com"
DEFAULT_MARKET = "forever.normal.horde.us"


class MarketAPIError(RuntimeError):
    """A provider, transport, or response-validation problem."""


def cache_seconds(header):
    """Respect the origin's max-age; missing/uncacheable responses get zero seconds."""
    value = (header or "").lower()
    if "no-store" in value or "no-cache" in value:
        return 0
    match = re.search(r"(?:^|,)\s*max-age\s*=\s*(\d+)", value)
    return min(int(match.group(1)), 3600) if match else 0


def observation_age_hours(value, now=None):
    """Return age in hours, or None when no valid timestamp is available."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        reference = now or datetime.now(timezone.utc)
        return (reference - parsed.astimezone(timezone.utc)).total_seconds() / 3600
    except ValueError:
        return None


def validate_price(payload, market, item_id):
    """Validate essential provider fields without assuming an auction is always present."""
    if not isinstance(payload, dict):
        raise MarketAPIError("API returned a non-object JSON response.")
    if payload.get("market") != market:
        raise MarketAPIError(
            f"Market mismatch: requested {market}, received {payload.get('market')!r}."
        )
    item = payload.get("item")
    if not isinstance(item, dict) or item.get("id") != item_id:
        raise MarketAPIError(f"Item mismatch: expected item ID {item_id}.")
    latest = payload.get("latest")
    if latest is None:
        raise MarketAPIError(
            "The market has no scan for this item yet (latest=null). "
            "Try another item or check again after a provider scan."
        )
    if not isinstance(latest, dict):
        raise MarketAPIError("Field 'latest' must be an object or null.")
    age = observation_age_hours(latest.get("observedAt"))
    if age is None:
        raise MarketAPIError("Missing or invalid 'latest.observedAt' UTC timestamp.")
    if age < -0.1:
        raise MarketAPIError("Provider observation timestamp is in the future.")
    for key in ("minBuyout", "median7d", "quantity"):
        value = latest.get(key)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0
        ):
            raise MarketAPIError(f"Invalid nonnegative numeric field: latest.{key}.")
    if not isinstance(payload.get("series", []), list):
        raise MarketAPIError("Field 'series' must be an array.")
    return age


def _get(path, params=None, session=None):
    requester = session if session is not None else requests
    try:
        response = requester.get(
            f"{BASE_URL}{path}", params=params, timeout=12,
            headers={"Accept": "application/json", "User-Agent": "WoWForeverMarketAnalytics/1.1"},
        )
    except requests.RequestException as exc:
        raise MarketAPIError(f"Unable to contact AHledger: {exc}") from exc
    if response.status_code != 200:
        retry = response.headers.get("Retry-After")
        hints = {
            401: "Check authentication/API key.",
            403: "Access denied; verify the requested history range or API entitlement.",
            404: "Endpoint or market not found; confirm the URL and market identifier.",
            429: "Rate limit exceeded; reduce polling.",
            503: "Provider temporarily unavailable; retry later.",
        }
        message = hints.get(response.status_code, "Check provider status and request.")
        if retry:
            message += f" Retry-After: {retry} seconds."
        raise MarketAPIError(f"AHledger HTTP {response.status_code}. {message}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise MarketAPIError("AHledger returned invalid JSON.") from exc
    return payload, cache_seconds(response.headers.get("Cache-Control"))


def fetch_markets(session=None):
    payload, ttl = _get("/v1/markets", session=session)
    markets = payload.get("markets") if isinstance(payload, dict) else None
    if not isinstance(markets, list):
        raise MarketAPIError("Markets response is missing a 'markets' array.")
    return markets, ttl


def fetch_price(item_id, market=DEFAULT_MARKET, session=None):
    payload, ttl = _get(
        f"/v1/prices/{market}/{item_id}", params={"range": "7d"}, session=session
    )
    age_hours = validate_price(payload, market, item_id)
    return payload, ttl, age_hours
