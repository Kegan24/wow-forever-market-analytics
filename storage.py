"""Local SQLite price history for the WoW Forever dashboard."""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).with_name('market_history.sqlite3')


def initialize(path=DEFAULT_DB):
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            min_buyout_copper INTEGER NOT NULL CHECK(min_buyout_copper >= 0),
            quantity INTEGER,
            UNIQUE(market, item_id, observed_at, min_buyout_copper)
        )''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_prices_item_time ON price_snapshots(market,item_id,observed_at)')


def save_snapshot(market, row, path=DEFAULT_DB):
    """Save one valid observation; ignore duplicate observations across refreshes."""
    price = row.get('Copper/unit')
    observed = row.get('Observed at')
    if price is None or observed is None or not str(observed).strip():
        return False
    try:
        price = int(price)
        if price < 0:
            return False
        item_id = int(row['Item ID'])
    except (ValueError, TypeError, KeyError):
        return False
    initialize(path)
    with closing(sqlite3.connect(path)) as conn, conn:
        cursor = conn.execute('''INSERT OR IGNORE INTO price_snapshots
            (market,item_id,item_name,observed_at,fetched_at,min_buyout_copper,quantity)
            VALUES (?,?,?,?,?,?,?)''',
            (market,item_id,row['Material'],str(observed),datetime.now(timezone.utc).isoformat(),price,row.get('Quantity listed')))
        return cursor.rowcount > 0


def load_history(market, item_id=None, path=DEFAULT_DB):
    initialize(path)
    with closing(sqlite3.connect(path)) as conn:
        conn.row_factory = sqlite3.Row
        if item_id is None:
            result = conn.execute('SELECT * FROM price_snapshots WHERE market=? ORDER BY observed_at', (market,))
        else:
            result = conn.execute('SELECT * FROM price_snapshots WHERE market=? AND item_id=? ORDER BY observed_at', (market,item_id))
        return [dict(row) for row in result]
