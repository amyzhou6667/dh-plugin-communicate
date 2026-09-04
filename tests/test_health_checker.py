"""健康检查服务测试"""

import pytest
from unittest.mock import MagicMock

from src.services.feishu_client import FeishuClient
from src.services.harness_client import HarnessClient
from src.services.health_checker import HealthChecker, HealthStatus, HealthStatusType, ComponentHealth


@pytest.fixture
def mock_harness_client():
    """模拟Harness客户端"""
    return MagicMock(spec=HarnessClient)


@pytest.fixture
def mock_feishu_client():
    """模拟飞书客户端"""
    return MagicMock(spec=FeishuClient)


@pytest.fixture
def health_checker(mock_harness_client, mock_feishu_client):
    """创建健康检查服务实例"""
    return HealthChecker(
        harness_client=mock_harness_client,
        feishu_client=mock_feishu_client,
    )


class TestCheckHealth:
    """测试健康检查"""

    def test_check_health_healthy(self, health_checker, mock_harness_client, mock_feishu_client):
        """测试健康状态"""
        mock_harness_client.health_check.return_value = True
        mock_feishu_client.get_tenant_access_token.return_value = 'test_token'

        status = health_checker.check_health()

        assert status.status == HealthStatusType.HEALTHY
        assert len(status.components) == 2

    def test_check_health_degraded(self, health_checker, mock_harness_client, mock_feishu_client):
        """测试降级状态"""
        mock_harness_client.health_check.return_value = True
        mock_feishu_client.get_tenant_access_token.side_effect = Exception('Token error')

        status = health_checker.check_health()

        assert status.status == HealthStatusType.UNHEALTHY

    def test_check_health_unhealthy(self, health_checker, mock_harness_client, mock_feishu_client):
        """测试不健康状态"""
        mock_harness_client.health_check.return_value = False
        mock_feishu_client.get_tenant_access_token.side_effect = Exception('Token error')

        status = health_checker.check_health()

        assert status.status == HealthStatusType.UNHEALTHY


class TestCheckHarnessConnection:
    """测试检查Harness连接"""

    def test_check_harness_connection_success(self, health_checker, mock_harness_client):
        """测试Harness连接成功"""
        mock_harness_client.health_check.return_value = True

        result = health_checker.check_harness_connection()

        assert result.name == 'harness'
        assert result.status == HealthStatusType.HEALTHY
        assert result.latency_ms >= 0

    def test_check_harness_connection_failure(self, health_checker, mock_harness_client):
        """测试Harness连接失败"""
        mock_harness_client.health_check.return_value = False

        result = health_checker.check_harness_connection()

        assert result.name == 'harness'
        assert result.status == HealthStatusType.UNHEALTHY

    def test_check_harness_connection_error(self, health_checker, mock_harness_client):
        """测试Harness连接错误"""
        mock_harness_client.health_check.side_effect = Exception('Connection error')

        result = health_checker.check_harness_connection()

        assert result.name == 'harness'
        assert result.status == HealthStatusType.UNHEALTHY
        assert 'Connection error' in result.message

    def test_check_harness_connection_no_client(self):
        """测试没有Harness客户端"""
        checker = HealthChecker(harness_client=None, feishu_client=None)

        result = checker.check_harness_connection()

        assert result.name == 'harness'
        assert result.status == HealthStatusType.UNHEALTHY
        assert 'not configured' in result.message


class TestCheckFeishuConnection:
    """测试检查飞书连接"""

    def test_check_feishu_connection_success(self, health_checker, mock_feishu_client):
        """测试飞书连接成功"""
        mock_feishu_client.get_tenant_access_token.return_value = 'test_token'

        result = health_checker.check_feishu_connection()

        assert result.name == 'feishu'
        assert result.status == HealthStatusType.HEALTHY
        assert result.latency_ms >= 0

    def test_check_feishu_connection_failure(self, health_checker, mock_feishu_client):
        """测试飞书连接失败"""
        mock_feishu_client.get_tenant_access_token.return_value = None

        result = health_checker.check_feishu_connection()

        assert result.name == 'feishu'
        assert result.status == HealthStatusType.UNHEALTHY

    def test_check_feishu_connection_error(self, health_checker, mock_feishu_client):
        """测试飞书连接错误"""
        mock_feishu_client.get_tenant_access_token.side_effect = Exception('Auth error')

        result = health_checker.check_feishu_connection()

        assert result.name == 'feishu'
        assert result.status == HealthStatusType.UNHEALTHY
        assert 'Auth error' in result.message

    def test_check_feishu_connection_no_client(self):
        """测试没有飞书客户端"""
        checker = HealthChecker(harness_client=None, feishu_client=None)

        result = checker.check_feishu_connection()

        assert result.name == 'feishu'
        assert result.status == HealthStatusType.UNHEALTHY
        assert 'not configured' in result.message


class TestComponentHealth:
    """测试组件健康状态"""

    def test_component_health_to_dict(self):
        """测试转换为字典"""
        health = ComponentHealth(
            name='test',
            status=HealthStatusType.HEALTHY,
            message='OK',
            latency_ms=10.5,
        )

        d = health.to_dict()

        assert d['name'] == 'test'
        assert d['status'] == 'healthy'
        assert d['message'] == 'OK'
        assert d['latency_ms'] == 10.5

    def test_component_health_to_dict_with_details(self):
        """测试转换为字典（带详情）"""
        health = ComponentHealth(
            name='test',
            status=HealthStatusType.HEALTHY,
            message='OK',
            details={'key': 'value'},
        )

        d = health.to_dict()

        assert d['details'] == {'key': 'value'}


class TestHealthStatus:
    """测试健康状态"""

    def test_health_status_to_dict(self):
        """测试转换为字典"""
        components = [
            ComponentHealth(name='test1', status=HealthStatusType.HEALTHY),
            ComponentHealth(name='test2', status=HealthStatusType.HEALTHY),
        ]

        status = HealthStatus(
            status=HealthStatusType.HEALTHY,
            components=components,
            timestamp=1234567890.0,
            version='1.0.0',
        )

        d = status.to_dict()

        assert d['status'] == 'healthy'
        assert d['timestamp'] == 1234567890.0
        assert d['version'] == '1.0.0'
        assert len(d['components']) == 2
