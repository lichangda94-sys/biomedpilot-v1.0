from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.app_identity import apply_app_identity
from app.main_window import MainWindow
from core.config import AppConfig
from core.data_dirs import DataDirectories
from core.logging_config import configure_logging
from core.task_status import TaskState, TaskStatus
from core.task_store import TaskStatusStore


def main() -> int:
    config = AppConfig.load()
    data_dirs = DataDirectories.for_app(config.app_slug)
    data_dirs.ensure_exists()
    log_file = configure_logging(data_dirs.logs_dir, debug=config.debug)
    logger = logging.getLogger(__name__)
    task_store = TaskStatusStore(data_dirs.state_dir)
    startup_status = TaskStatus(task_id="app.startup")
    startup_status.transition(TaskState.RUNNING, "desktop shell initialized")
    task_store.save(startup_status)
    logger.info("Application startup initialized. log_file=%s", log_file)

    app = QApplication(sys.argv)
    apply_app_identity(app)

    window = MainWindow(config=config, data_dirs=data_dirs)
    window.show()
    if config.startup_test_ms > 0:
        logger.info(
            "Startup self-check enabled; quitting after %sms.",
            config.startup_test_ms,
        )
        QTimer.singleShot(config.startup_test_ms, app.quit)
    return app.exec()
