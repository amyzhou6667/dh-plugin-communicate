"""超时调度器测试"""

import pytest
import time
from unittest.mock import MagicMock, patch

from src.services.timeout_handler import TimeoutHandler, TimeoutResult
from src.services.timeout_scheduler import TimeoutScheduler


@pytest.fixture
def mock_timeout_handler():
    """模拟超时处理器"""
    return MagicMock(spec=TimeoutHandler)


@pytest.fixture
def scheduler(mock_timeout_handler):
    """创建超时调度器实例"""
    return TimeoutScheduler(
        timeout_handler=mock_timeout_handler,
        check_interval_seconds=1,  # 1秒间隔用于测试
    )


class TestTimeoutSchedulerInit:
    """测试超时调度器初始化"""

    def test_initialization(self, scheduler, mock_timeout_handler):
        """测试初始化"""
        assert scheduler.timeout_handler == mock_timeout_handler
        assert scheduler.check_interval_seconds == 1
        assert scheduler.is_running is False


class TestStartStop:
    """测试启动和停止"""

    def test_start(self, scheduler):
        """测试启动"""
        scheduler.start()

        assert scheduler.is_running is True

        # 清理
        scheduler.stop()

    def test_start_already_running(self, scheduler, mock_timeout_handler):
        """测试重复启动"""
        scheduler.start()

        # 再次启动应该不会出错
        scheduler.start()

        assert scheduler.is_running is True

        # 清理
        scheduler.stop()

    def test_stop(self, scheduler):
        """测试停止"""
        scheduler.start()
        scheduler.stop()

        assert scheduler.is_running is False

    def test_stop_not_running(self, scheduler):
        """测试停止未运行的调度器"""
        # 停止未运行的调度器应该不会出错
        scheduler.stop()

        assert scheduler.is_running is False


class TestCheckOnce:
    """测试执行一次检查"""

    def test_check_once_success(self, scheduler, mock_timeout_handler):
        """测试执行一次检查成功"""
        mock_result = TimeoutResult(
            task_id='task_123',
            action='reminder',
            success=True,
            message='Reminder sent',
        )
        mock_timeout_handler.check_timeout_tasks.return_value = [mock_result]

        results = scheduler.check_once()

        assert len(results) == 1
        assert results[0].task_id == 'task_123'
        mock_timeout_handler.check_timeout_tasks.assert_called_once()

    def test_check_once_no_tasks(self, scheduler, mock_timeout_handler):
        """测试执行一次检查无任务"""
        mock_timeout_handler.check_timeout_tasks.return_value = []

        results = scheduler.check_once()

        assert len(results) == 0

    def test_check_once_error(self, scheduler, mock_timeout_handler):
        """测试执行一次检查出错"""
        mock_timeout_handler.check_timeout_tasks.side_effect = Exception('Test error')

        results = scheduler.check_once()

        assert len(results) == 0


class TestRunLoop:
    """测试运行循环"""

    def test_run_loop(self, scheduler, mock_timeout_handler):
        """测试运行循环"""
        mock_timeout_handler.check_timeout_tasks.return_value = []

        scheduler.start()
        time.sleep(0.5)  # 等待循环执行几次
        scheduler.stop()

        # 验证检查被调用过
        assert mock_timeout_handler.check_timeout_tasks.call_count >= 1
