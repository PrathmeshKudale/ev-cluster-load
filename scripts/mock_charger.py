"""Standalone CLI runner for OCPP 1.6J Mock Charger Client.

Connects to a running Central System WebSocket endpoint, sends the 5 core messages:
1. BootNotification
2. StatusNotification
3. StartTransaction
4. MeterValues
5. StopTransaction
And confirms session creation in the central system.

Usage:
    python scripts/mock_charger.py --url ws://localhost:8000/ocpp/CP-101 --charger-id CP-101
"""
import argparse
import asyncio
import logging
import sys

from app.services.mock_charger import run_mock_charging_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mock_charger_cli")


def main():
    parser = argparse.ArgumentParser(description="Simulate an OCPP 1.6J EVSE charge point session.")
    parser.add_argument(
        "--url",
        default="ws://localhost:8000/ocpp/CP-101",
        help="WebSocket URL of Central System (default: ws://localhost:8000/ocpp/CP-101)",
    )
    parser.add_argument(
        "--charger-id",
        default="CP-101",
        help="Charge point identifier (default: CP-101)",
    )
    parser.add_argument(
        "--vendor",
        default="ABB",
        help="Charge point vendor (default: ABB)",
    )
    parser.add_argument(
        "--model",
        default="Terra-54-Tri",
        help="Charge point model (default: Terra-54-Tri)",
    )
    parser.add_argument(
        "--id-tag",
        default="TAG-EV-9999",
        help="RFID ID tag token for driver authentication",
    )
    parser.add_argument(
        "--energy-kwh",
        type=float,
        default=14.8,
        help="Delivered energy in kWh (default: 14.8)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay in seconds between lifecycle steps (default: 0.2)",
    )

    args = parser.parse_args()

    logger.info("Connecting to Central System at %s as %s ...", args.url, args.charger_id)
    try:
        result = asyncio.run(
            run_mock_charging_session(
                ws_url=args.url,
                charger_id=args.charger_id,
                vendor=args.vendor,
                model=args.model,
                id_tag=args.id_tag,
                energy_kwh=args.energy_kwh,
                delay_between_steps=args.delay,
            )
        )
        logger.info("Charging session completed successfully: %s", result)
        print(f"\n[OK] Mock charging session complete: tx_id={result['transaction_id']}, energy={result['energy_kwh']} kWh")
    except Exception as e:
        logger.error("Failed to run mock charging session: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
