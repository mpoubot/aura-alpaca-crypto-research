from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from alpaca.trading.client import TradingClient

from .config import ROOT, load_settings


def fetch_crypto_universe() -> list[dict]:
    settings = load_settings(require_credentials=True)
    client = TradingClient(settings.api_key, settings.api_secret, paper=True)
    assets = client.get_all_assets()
    rows = []
    for asset in assets:
        if str(getattr(asset, "asset_class", "")).lower() != "crypto":
            continue
        rows.append(
            {
                "id": str(asset.id),
                "symbol": str(asset.symbol),
                "name": str(asset.name),
                "status": str(asset.status),
                "tradable": bool(asset.tradable),
                "fractionable": bool(getattr(asset, "fractionable", False)),
                "exchange": str(getattr(asset, "exchange", "")),
                "min_order_size": str(getattr(asset, "min_order_size", "")),
                "min_trade_increment": str(getattr(asset, "min_trade_increment", "")),
            }
        )
    return sorted(rows, key=lambda x: x["symbol"])


def save_snapshot(rows: list[dict]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "data" / "universe"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"alpaca_crypto_universe_{stamp}.json"
    path.write_text(json.dumps({"generated_at": stamp, "assets": rows}, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", action="store_true", help="Explicitly confirm paper mode")
    args = parser.parse_args()
    if not args.paper:
        raise SystemExit("Refusing to query trading assets without --paper")
    rows = fetch_crypto_universe()
    path = save_snapshot(rows)
    print(f"crypto_assets={len(rows)}")
    print(f"snapshot={path}")
    for row in rows:
        if row["tradable"]:
            print(row["symbol"])


if __name__ == "__main__":
    main()
