"""CLI entry point for Raspberry Pi observation runs."""

from __future__ import annotations

import argparse
import logging

from app.config import Settings, configure_logging
from app.scheduler.observation_scheduler import run_observation_cycle

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Komatsuna Raspberry Pi observation runner")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run transports")
    parser.add_argument("command", choices=["once"], help="Run a single observation cycle")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings.from_env(force_dry_run=args.dry_run)
    configure_logging(settings.log_level)

    if args.command == "once":
        observation = run_observation_cycle(settings)
        logger.info(
            "Observation cycle completed: id=%s status=%s soil=%s",
            observation.id,
            observation.device_status,
            observation.soil_moisture_percent,
        )


if __name__ == "__main__":
    main()
