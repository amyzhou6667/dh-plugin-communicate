"""健康检查服务模块

负责检查系统各组件的健康状态。
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from src.services.feishu_client import FeishuClient
from src.services.harness_client import HarnessClient

logger = logging.getLogger(__name__)


class HealthStatusType(Enum):
    """健康状态类型"""
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'


@dataclass
class ComponentHealth:
    """组件健康状态"""

    name: str
    status: HealthStatusType
    message: str = ''
    latency_ms: float = 0.0
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'latency_ms': self.latency_ms,
        }
        if self.details:
            result['details'] = self.details
        return result


@dataclass
class HealthStatus:
    """健康状态"""

    status: HealthStatusType
    components: list = field(default_factory=list)
    timestamp: float = 0.0
    version: str = '1.0.0'

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'status': self.status.value,
            'timestamp': self.timestamp,
            'version': self.version,
            'components': [c.to_dict() for c in self.components],
        }


class HealthChecker:
    """健康检查服务"""

    def __init__(self, harness_client: Optional[HarnessClient] = None,
                 feishu_client: Optional[FeishuClient] = None):
        """初始化健康检查服务

        Args:
            harness_client: Harness客户端
            feishu_client: 飞书客户端
        """
        self.harness_client = harness_client
        self.feishu_client = feishu_client

    def check_health(self) -> HealthStatus:
        """执行健康检查

        Returns:
            HealthStatus: 健康状态
        """
        components = []

        # 检查各个组件
        harness_health = self.check_harness_connection()
        components.append(harness_health)

        feishu_health = self.check_feishu_connection()
        components.append(feishu_health)

        # 确定整体状态
        overall_status = self._determine_overall_status(components)

        return HealthStatus(
            status=overall_status,
            components=components,
            timestamp=time.time(),
        )

    def check_harness_connection(self) -> ComponentHealth:
        """检查Harness连接

        Returns:
            ComponentHealth: 组件健康状态
        """
        if not self.harness_client:
            return ComponentHealth(
                name='harness',
                status=HealthStatusType.UNHEALTHY,
                message='Harness client not configured',
            )

        start_time = time.time()

        try:
            is_healthy = self.harness_client.health_check()
            latency_ms = (time.time() - start_time) * 1000

            if is_healthy:
                return ComponentHealth(
                    name='harness',
                    status=HealthStatusType.HEALTHY,
                    message='Connection successful',
                    latency_ms=latency_ms,
                )
            else:
                return ComponentHealth(
                    name='harness',
                    status=HealthStatusType.UNHEALTHY,
                    message='Health check failed',
                    latency_ms=latency_ms,
                )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='harness',
                status=HealthStatusType.UNHEALTHY,
                message=f'Connection error: {str(e)}',
                latency_ms=latency_ms,
            )

    def check_feishu_connection(self) -> ComponentHealth:
        """检查飞书连接

        Returns:
            ComponentHealth: 组件健康状态
        """
        if not self.feishu_client:
            return ComponentHealth(
                name='feishu',
                status=HealthStatusType.UNHEALTHY,
                message='Feishu client not configured',
            )

        start_time = time.time()

        try:
            # 尝试获取 access token 来验证连接
            token = self.feishu_client.get_tenant_access_token()
            latency_ms = (time.time() - start_time) * 1000

            if token:
                return ComponentHealth(
                    name='feishu',
                    status=HealthStatusType.HEALTHY,
                    message='Connection successful',
                    latency_ms=latency_ms,
                )
            else:
                return ComponentHealth(
                    name='feishu',
                    status=HealthStatusType.UNHEALTHY,
                    message='Failed to get access token',
                    latency_ms=latency_ms,
                )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='feishu',
                status=HealthStatusType.UNHEALTHY,
                message=f'Connection error: {str(e)}',
                latency_ms=latency_ms,
            )

    def _determine_overall_status(self, components: list) -> HealthStatusType:
        """确定整体健康状态

        Args:
            components: 组件健康状态列表

        Returns:
            HealthStatusType: 整体健康状态
        """
        if not components:
            return HealthStatusType.UNHEALTHY

        unhealthy_count = sum(1 for c in components if c.status == HealthStatusType.UNHEALTHY)
        degraded_count = sum(1 for c in components if c.status == HealthStatusType.DEGRADED)

        if unhealthy_count > 0:
            # 如果有任何组件不健康，整体状态为不健康
            return HealthStatusType.UNHEALTHY
        elif degraded_count > 0:
            # 如果有任何组件降级，整体状态为降级
            return HealthStatusType.DEGRADED
        else:
            return HealthStatusType.HEALTHY
