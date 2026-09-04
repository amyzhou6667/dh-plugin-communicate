"""监控指标收集器模块

负责收集和管理监控指标。
"""

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """指标值"""

    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """监控指标收集器"""

    def __init__(self):
        """初始化监控指标收集器"""
        self._counters: Dict[str, List[MetricValue]] = defaultdict(list)
        self._timings: Dict[str, List[MetricValue]] = defaultdict(list)
        self._gauges: Dict[str, List[MetricValue]] = defaultdict(list)
        self._lock = threading.Lock()

    def increment_counter(self, name: str, tags: Optional[Dict[str, str]] = None, value: float = 1.0):
        """增加计数器

        Args:
            name: 指标名称
            tags: 标签
            value: 增加值
        """
        with self._lock:
            metric = MetricValue(
                value=value,
                timestamp=time.time(),
                tags=tags or {},
            )
            self._counters[name].append(metric)

        logger.debug("Counter %s incremented by %f", name, value)

    def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """记录耗时

        Args:
            name: 指标名称
            duration: 耗时（秒）
            tags: 标签
        """
        with self._lock:
            metric = MetricValue(
                value=duration,
                timestamp=time.time(),
                tags=tags or {},
            )
            self._timings[name].append(metric)

        logger.debug("Timing %s recorded: %.3f seconds", name, duration)

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """设置仪表盘值

        Args:
            name: 指标名称
            value: 值
            tags: 标签
        """
        with self._lock:
            metric = MetricValue(
                value=value,
                timestamp=time.time(),
                tags=tags or {},
            )
            self._gauges[name].append(metric)

        logger.debug("Gauge %s set to %f", name, value)

    def get_counter_value(self, name: str) -> float:
        """获取计数器值

        Args:
            name: 指标名称

        Returns:
            float: 计数器值
        """
        with self._lock:
            metrics = self._counters.get(name, [])
            return sum(m.value for m in metrics)

    def get_timing_stats(self, name: str) -> Dict[str, float]:
        """获取耗时统计

        Args:
            name: 指标名称

        Returns:
            Dict[str, float]: 统计信息
        """
        with self._lock:
            metrics = self._timings.get(name, [])
            if not metrics:
                return {'count': 0, 'avg': 0, 'min': 0, 'max': 0, 'total': 0}

            values = [m.value for m in metrics]
            return {
                'count': len(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'total': sum(values),
            }

    def get_gauge_value(self, name: str) -> Optional[float]:
        """获取仪表盘值

        Args:
            name: 指标名称

        Returns:
            Optional[float]: 仪表盘值
        """
        with self._lock:
            metrics = self._gauges.get(name, [])
            if not metrics:
                return None
            return metrics[-1].value

    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标

        Returns:
            Dict[str, Any]: 所有指标
        """
        with self._lock:
            metrics = {}

            # 计数器
            for name, values in self._counters.items():
                metrics[f'counter.{name}'] = sum(m.value for m in values)

            # 耗时
            for name, values in self._timings.items():
                if values:
                    timing_values = [m.value for m in values]
                    metrics[f'timing.{name}.count'] = len(timing_values)
                    metrics[f'timing.{name}.avg'] = sum(timing_values) / len(timing_values)
                    metrics[f'timing.{name}.min'] = min(timing_values)
                    metrics[f'timing.{name}.max'] = max(timing_values)

            # 仪表盘
            for name, values in self._gauges.items():
                if values:
                    metrics[f'gauge.{name}'] = values[-1].value

            return metrics

    def reset(self):
        """重置所有指标"""
        with self._lock:
            self._counters.clear()
            self._timings.clear()
            self._gauges.clear()

        logger.info("All metrics reset")

    def get_summary(self) -> str:
        """获取指标摘要

        Returns:
            str: 指标摘要
        """
        metrics = self.get_metrics()

        if not metrics:
            return "No metrics collected"

        lines = ["Metrics Summary:"]

        # 计数器
        counters = {k: v for k, v in metrics.items() if k.startswith('counter.')}
        if counters:
            lines.append("\nCounters:")
            for name, value in sorted(counters.items()):
                lines.append(f"  {name}: {value}")

        # 耗时
        timings = {k: v for k, v in metrics.items() if k.startswith('timing.')}
        if timings:
            lines.append("\nTimings:")
            for name, value in sorted(timings.items()):
                lines.append(f"  {name}: {value:.3f}")

        # 仪表盘
        gauges = {k: v for k, v in metrics.items() if k.startswith('gauge.')}
        if gauges:
            lines.append("\nGauges:")
            for name, value in sorted(gauges.items()):
                lines.append(f"  {name}: {value}")

        return '\n'.join(lines)
