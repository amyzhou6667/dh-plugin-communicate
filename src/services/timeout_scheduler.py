"""超时调度器模块

负责定期检查和处理超时任务。
"""

import logging
import threading
import time
from typing import List, Optional

from src.services.timeout_handler import TimeoutHandler, TimeoutResult

logger = logging.getLogger(__name__)


class TimeoutScheduler:
    """超时调度器"""

    def __init__(self, timeout_handler: TimeoutHandler, check_interval_seconds: int = 60):
        """初始化超时调度器

        Args:
            timeout_handler: 超时处理器
            check_interval_seconds: 检查间隔（秒）
        """
        self.timeout_handler = timeout_handler
        self.check_interval_seconds = check_interval_seconds
        self._is_running = threading.Event()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        """调度器是否正在运行

        Returns:
            bool: 是否正在运行
        """
        return self._is_running.is_set()

    def start(self):
        """启动调度器"""
        if self._is_running.is_set():
            logger.warning("Timeout scheduler is already running")
            return

        self._stop_event.clear()
        self._is_running.set()

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        logger.info("Timeout scheduler started with interval %d seconds", self.check_interval_seconds)

    def stop(self):
        """停止调度器"""
        if not self._is_running.is_set():
            logger.warning("Timeout scheduler is not running")
            return

        self._stop_event.set()
        self._is_running.clear()

        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

        logger.info("Timeout scheduler stopped")

    def check_once(self) -> List[TimeoutResult]:
        """执行一次检查

        Returns:
            List[TimeoutResult]: 检查结果列表
        """
        try:
            results = self.timeout_handler.check_timeout_tasks()
            return results
        except Exception as e:
            logger.error("Error checking timeout tasks: %s", e)
            return []

    def _run_loop(self):
        """运行循环"""
        logger.info("Timeout scheduler loop started")

        while not self._stop_event.is_set():
            try:
                self.check_once()
            except Exception as e:
                logger.error("Error in timeout scheduler loop: %s", e)

            # 等待下一次检查
            self._stop_event.wait(self.check_interval_seconds)

        logger.info("Timeout scheduler loop exited")
