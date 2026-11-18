# WoW Forever Gold Dashboard

A local, on-demand dashboard for **US Normal Horde** using AHledger's public market API.

## Run on Windows (PowerShell)

```powershell
cd path\to\wow_forever_gold_dashboard
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the localhost URL Streamlit displays (typically http://localhost:8501).

## Features

- Latest observed item prices, quantities, and seven-day medians
- Mining and Herbalism skill filters
- Editable gathering yield estimates for realized gold/hour
- Ore-to-bar comparisons and historical price chart
- CSV export, refresh button, 15-minute request cache

## Important limitations

- A refresh requests the **latest available provider observation**, not a guaranteed live scan of the game.
- Auction listing prices and inferred sales estimates are not actual confirmed sales.
- Profit model uses a configurable sale-price realization factor and auction fee; it excludes deposit losses and travel costs.
- Mining skill requirements and item IDs are reference defaults; validate against the current Forever client.
- Requires internet connectivity and depends on a third-party service; inspect https://ahledger.com/developers for access/licensing terms.
- Does not require or read your Auctionator file. Auctionator can remain your in-game tool.

## v1.1: local price history

The dashboard now saves unique price observations in `market_history.sqlite3` using SQLite.
It adds a saved-price chart and CSV export. No database server is needed. The file is
created automatically after valid provider observations are received. Repeated requests
for an unchanged observation do not create artificial history.

**Validation:** Run `py -m unittest discover -v` from the project folder.
The tests cover SQLite storage and deduplication, **not** the live third-party API.

**Important:** The external AHledger endpoint and response schema are unverified in this
release. If it returns errors or no records, the app will not have usable market prices;
do not interpret an empty table as proof of zero market activity. Verify endpoint,
market identifier, access conditions, and returned JSON before relying on any estimates.

**Data quality:** Auction listings are not confirmed sales. The dashboard's farming
returns are user-supplied yield estimates, not empirically verified gold/hour. The
smelting comparison now charges the Auction House fee to bar-sale proceeds only.

**Privacy and publishing:** `market_history.sqlite3` is local user data and should not
be committed to a public GitHub repository. Keep any API credentials out of source code.
