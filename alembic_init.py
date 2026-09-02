"""Run `alembic upgrade head` with explicit error handling and logging.

Railway's preDeployCommand runs before the app container starts. If the
migration fails silently (e.g. because the database is unreachable), the
app still starts and attempts to write to tables that were never created,
failing silently downstream.

This script wraps the Alembic upgrade command, logs the outcome, and
exits with a non-zero status code on failure so Railway can surface the
failure and stop the deploy instead of proceeding with a stale schema.
"""

import logging
import os
import sys

from alembic import command
from alembic.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("alembic_init")


def run_migrations() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error(
            "DATABASE_URL is not set. Alembic cannot connect to the database."
        )
        sys.exit(1)

    logger.info("Starting Alembic upgrade to 'head'...")

    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:  # noqa: BLE001 - we want to log and re-raise as exit code
        logger.error("Alembic upgrade failed: %s", exc, exc_info=True)
        sys.exit(1)

    logger.info("Alembic upgrade completed successfully.")


if __name__ == "__main__":
    run_migrations()
