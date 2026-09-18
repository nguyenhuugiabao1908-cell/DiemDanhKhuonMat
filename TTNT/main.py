# StudentAttendance/main.py
from __future__ import annotations

import logging
import sys
from pathlib import Path

from gui.login import LoginWindow
from utils.database import DatabaseManager
from utils.helpers import ensure_project_structure, setup_logging

BASE_DIR = Path(__file__).resolve().parent


def main() -> None:
    ensure_project_structure(BASE_DIR)
    setup_logging(BASE_DIR / "logs")
    logging.info("Starting StudentAttendance application")

    try:
        db = DatabaseManager()
        
        app = LoginWindow(
            db=db,
            base_dir=BASE_DIR,
        )
        app.run()
    except Exception as exc:
        logging.exception("Application failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
