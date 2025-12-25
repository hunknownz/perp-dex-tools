"""Standalone script to test GRVT market order placement."""

import argparse
import asyncio
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from exchanges.grvt import GrvtClient


class SimpleConfig:
    """Lightweight config wrapper for GrvtClient."""

    def __init__(self, data: Dict[str, Any]):
        for key, value in data.items():
            setattr(self, key, value)


def load_env_file(env_path: str) -> None:
    path = Path(env_path)
    if not path.exists():
        return

    with path.open() as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


async def run_test(ticker: str, side: str, quantity: Decimal, dry_run: bool):
    config = SimpleConfig(
        {
            "ticker": ticker,
            "contract_id": "",
            "quantity": quantity,
            "tick_size": Decimal("0.01"),
            "close_order_side": "sell",
        }
    )

    client = GrvtClient(config)

    contract_id, tick_size = await client.get_contract_attributes()
    print(f"Contract: {contract_id} | tick_size: {tick_size}")

    if dry_run:
        print("Dry-run flag set; skipping order placement.")
        return

    try:
        result = await client.place_market_order(contract_id, quantity, side)
        print("Order response:")
        print(json.dumps(result, indent=2, default=str))
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Order failed: {exc}")


def parse_args():
    parser = argparse.ArgumentParser(description="Send a test market order to GRVT")
    parser.add_argument("--ticker", default="BTC", help="Base asset ticker, default BTC")
    parser.add_argument(
        "--side",
        choices=["buy", "sell"],
        default="buy",
        help="Order direction",
    )
    parser.add_argument(
        "--quantity",
        type=Decimal,
        default=Decimal("0.01"),
        help="Order size in base asset",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only fetch contract info without placing any order",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file containing GRVT credentials",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    load_env_file(args.env_file)
    asyncio.run(run_test(args.ticker, args.side, args.quantity, args.dry_run))


if __name__ == "__main__":
    main()
