"""Pure market analytics: no API requests or persistent provider-data storage."""
def median_deviation_percent(price, median):
    """Current minimum listing relative to provider seven-day median."""
    if price is None or median is None or median <= 0:
        return None
    return (price / median - 1) * 100


def price_signal(price, median, threshold=10):
    """Descriptive price position, not a prediction or buy/sell recommendation."""
    deviation = median_deviation_percent(price, median)
    if deviation is None:
        return "Insufficient history"
    if deviation <= -threshold:
        return "Below 7d median"
    if deviation >= threshold:
        return "Above 7d median"
    return "Near 7d median"


def eligible_for_estimate(price, age_hours, stale_after_hours=24):
    """Reject unknown, invalid or stale listing observations."""
    return (
        isinstance(price, (int, float)) and not isinstance(price, bool)
        and price >= 0 and isinstance(age_hours, (int, float))
        and 0 <= age_hours <= stale_after_hours
    )
