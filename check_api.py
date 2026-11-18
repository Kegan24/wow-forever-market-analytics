"""Manual AHledger connectivity check. No credentials or responses are saved."""
import argparse
import json
import sys

from market_api import DEFAULT_MARKET, MarketAPIError, fetch_markets, fetch_price


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check WoW Forever market API connectivity")
    parser.add_argument("--market", default=DEFAULT_MARKET)
    parser.add_argument("--item", type=int, default=2770, help="Copper Ore item ID")
    args = parser.parse_args(argv)
    try:
        markets, markets_ttl = fetch_markets()
        matching = [m for m in markets if isinstance(m, dict) and m.get("id") == args.market]
        if not matching:
            print(f"FAIL: Market {args.market!r} not in provider market list.")
            return 1
        print(f"OK market: {json.dumps(matching[0], sort_keys=True)} (cache max-age {markets_ttl}s)")
        payload, ttl, age = fetch_price(args.item, args.market)
        latest = payload["latest"]
        print(f"OK item: {payload['item'].get('name')} (ID {args.item})")
        print(f"Price: {latest.get('minBuyout')} copper; quantity: {latest.get('quantity')}")
        print(f"Observed: {latest.get('observedAt')} ({age:.1f} hours ago); cache max-age: {ttl}s")
        print(f"History buckets: {len(payload.get('series', []))}")
        if age > 24:
            print("WARNING: observation is more than 24 hours old; do not treat as live.")
        print("No raw responses or credentials were saved.")
        return 0
    except MarketAPIError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
