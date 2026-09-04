"""
轮询调度器测试
基于接口签名契约设计测试用例
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import time


class TestPollingScheduler:
    """PollingScheduler 测试"""

    def test_initialization(self):
        """测试轮询调度器初始化"""
        from src.services.polling_scheduler import PollingScheduler
        from src.services.task_discovery import TaskDiscovery

        mock_discovery = Mock(spec=TaskDiscovery)

        scheduler = PollingScheduler(mock_discovery, interval_seconds=10)
        assert scheduler.task_discovery == mock_discovery
        assert scheduler.interval_seconds == 10
        assert scheduler.is_running is False

    def test_initialization_default_interval(self):
        """测试轮询调度器初始化（默认间隔）"""
        from src.services.polling_scheduler import PollingScheduler
        from src.services.task_discovery import TaskDiscovery

        mock_discovery = Mock(spec=TaskDiscovery)

        scheduler = PollingScheduler(mock_discovery)
        assert scheduler.interval_seconds == 5

    def test_poll_once_success(self, db_session):
        """测试单次轮询成功"""
        from src.services.polling_scheduler import PollingScheduler
        from src.services.task_discovery import TaskDiscovery
        from src.models.task import Task, TaskStatus

        # Mock TaskDiscovery
        mock_discovery = Mock(spec=TaskDiscovery)
        mock_task = Task(
            id='task_1',
            harness_task_id='harness_1',
            content='测试任务',
            status=TaskStatus.PENDING
        )
        mock_discovery.discover_pending_tasks.return_value = [mock_task]

        scheduler = PollingScheduler(mock_discovery)
        tasks = scheduler.poll_once()

        assert len(tasks) == 1
        assert tasks[0].id == 'task_1'
        mock_discovery.discover_pending_tasks.assert_called_once()

    def test_poll_once_no_tasks(self, db_session):
        """测试单次轮询无任务"""
        from src.services.polling_scheduler import PollingScheduler
        from src.services.task_discovery import TaskDiscovery

        # Mock TaskDiscovery 返回空列表
        mock_discovery = Mock(spec=TaskDiscovery)
        mock_discovery.discover_pending_tasks.return_value = []

        scheduler = PollingScheduler(mock_discovery)
        tasks = scheduler.poll_once()

        assert len(tasks) == 0
        mock_discovery.discover_pending_tasks.assert_called_once()

    def test_poll_once_error(self, db_session):
        """测试单次轮询错误"""
        from src.services.polling_scheduler import PollingScheduler
        from src.services.task_discovery import TaskDiscovery
        from src.services.harness_client import HarnessConnectionError

        # Mock TaskDiscovery 抛出异常
        mock_discovery = Mock(spec=TaskDiscovery)
        mock_discovery.discover_pending_tasks.side_effect = HarnessConnectionError('Connection refused')

        scheduler = PollingScheduler(mock_discovery)

        # 应该捕获异常，不抛出
        tasks = scheduler.poll_once()

        assert len(tasks) == 0
        mock_discovery.discover_pending_tasks.assert_called_once()

    def test_start_stop(self):
        """测试启动和停止"""
        from src.services.polling_scheduler import PollingScheduler
        from src.services.task_discovery import TaskDiscovery

        mock_discovery = Mock(spec=TaskDiscovery)

        scheduler = PollingScheduler(mock_discovery, interval_seconds=1)

        # 启动
        scheduler.start()
        assert scheduler.is_running is True

        # 等待一小段时间让轮询执行
        time.sleep(0.1)

        # 停止
        scheduler.stop()
        assert scheduler.is_running is False

    def test_start_already_running(self):
        """测试重复启动"""
        from src.services.polling_scheduler import PollingScheduler
        from src.services.task_discovery import TaskDiscovery

        mock_discovery = Mock(spec=TaskDiscovery)

        scheduler = PollingScheduler(mock_discovery, interval_seconds=1)

        # 第一次启动
        scheduler.start()
        assert scheduler.is_running is True

        # 第二次启动（应该忽略）
        scheduler.start()
        assert scheduler.is_running is True

        # 停止
        scheduler.stop()

    def test_stop_not_running(self):
        """测试停止未运行的调度器"""
        from src.services.polling_scheduler import PollingScheduler
        from src.services.task_discovery import TaskDiscovery

        mock_discovery = Mock(spec=TaskDiscovery)

        scheduler = PollingScheduler(mock_discovery)

        # 停止未运行的调度器（应该忽略）
        scheduler.stop()
        assert scheduler.is_running is False

    def test_poll_loop(self):
        """测试轮询循环"""
        from src.services.polling_scheduler import PollingScheduler
        from src.services.task_discovery import TaskDiscovery
        import time

        mock_discovery = Mock(spec=TaskDiscovery)
        mock_discovery.discover_pending_tasks.return_value = []

        scheduler = PollingScheduler(mock_discovery, interval_seconds=1)

        # 启动调度器
        scheduler.start()

        # 等待一小段时间
        time.sleep(0.1)

        # 停止调度器
        scheduler.stop()

        # 验证轮询被调用
        assert mock_discovery.discover_pending_tasks.call_count >= 1
