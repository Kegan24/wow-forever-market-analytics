# Issue #1: AHledger API contract and verification

Status: **documented contract verified; live API response not yet confirmed**.

Reference: https://ahledger.com/developers (checked 2026-11-18).

## Market and endpoint

- Market: `forever.normal.horde.us` (Forever, Normal/PvE, Horde, US).
- Markets discovery: `GET https://api.ahledger.com/v1/markets`.
- Copper Ore example (Blizzard item ID 2770):
  `GET https://api.ahledger.com/v1/prices/forever.normal.horde.us/2770?range=7d`
- Prices are **copper** (10,000 copper = 1 gold).
- The documented price response contains `market`, `item.id`, `latest`, and `series`.
- `latest.minBuyout`, `latest.median7d`, `latest.quantity`, and `latest.observedAt` are used by the dashboard.
- `latest=null` means no scan for that item; it is **not** evidence of zero market activity.
- A price/quantity is an auction listing observation, **not** a confirmed sale.

## Validation from Windows PowerShell

```powershell
py --version
python --version
git --version
git clone https://github.com/Kegan24/wow-forever-market-analytics.git
cd wow-forever-market-analytics
git fetch origin
git switch issue-1-validate-ahledger-api
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -v
python check_api.py --market forever.normal.horde.us --item 2770
```

A successful diagnostic prints market metadata, copper price (if available), observation age, response cache lifetime, and history length. If the provider cannot be reached or the item has no scan, the command exits nonzero with an actionable message. Do **not** paste an API key or secret into an issue.

## Status and limitations

- Verified: official docs specify the endpoint, market format, response fields, copper units, and `Cache-Control`.
- Not yet verified: a real successful HTTP response, current observed-at timestamp and item price, or provider availability from the developer's machine. The execution environment used for initial development cannot resolve `api.ahledger.com`.
- Existing `app.py` still uses its original 15-minute request cache and writes SQLite history. This PR adds a diagnostic/validation module but does **not** switch the Streamlit app to it. Integrate only after running the live diagnostic and settling provider data-retention terms.
- Provider terms announced 2026-11-10 take effect 2026-12-10. Without a key the documented limit will be 30 requests/minute and up to 7 days of history. Persisting responses past their cache period, archiving, or building long-term datasets requires the **Data** licence. The existing SQLite archival feature should be disabled until authorization is established.
- Respect origin `Cache-Control` and `Retry-After`; avoid bulk per-item polling. A future batch integration can investigate `/v1/tooltip/{market}` (up to 100 items/request), after validating its JSON schema.
- Provide visible AHledger attribution and link when displaying live provider data in community tools.

## Acceptance checklist

- [x] Document official endpoint, market ID, response contract and terms.
- [x] Add isolated provider client with actionable errors and observation age.
- [x] Add offline mock tests and GitHub Actions workflow.
- [ ] Run `python check_api.py` on a connected Windows development machine and record only **sanitized** output.
- [ ] Confirm current availability, schema, `Cache-Control`, and scan recency.
- [ ] Update Streamlit integration to use validated responses and permitted caching, then retest.

Do not close Issue #1 until live validation and integration are confirmed.
