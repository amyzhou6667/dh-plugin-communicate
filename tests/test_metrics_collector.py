"""监控指标收集器测试"""

import pytest
from unittest.mock import patch

from src.services.metrics_collector import MetricsCollector, MetricValue


@pytest.fixture
def metrics_collector():
    """创建监控指标收集器实例"""
    return MetricsCollector()


class TestIncrementCounter:
    """测试增加计数器"""

    def test_increment_counter_default(self, metrics_collector):
        """测试默认增加值"""
        metrics_collector.increment_counter('test_counter')

        assert metrics_collector.get_counter_value('test_counter') == 1.0

    def test_increment_counter_custom_value(self, metrics_collector):
        """测试自定义增加值"""
        metrics_collector.increment_counter('test_counter', value=5.0)

        assert metrics_collector.get_counter_value('test_counter') == 5.0

    def test_increment_counter_multiple(self, metrics_collector):
        """测试多次增加"""
        metrics_collector.increment_counter('test_counter')
        metrics_collector.increment_counter('test_counter')
        metrics_collector.increment_counter('test_counter', value=2.0)

        assert metrics_collector.get_counter_value('test_counter') == 4.0

    def test_increment_counter_with_tags(self, metrics_collector):
        """测试带标签增加"""
        tags = {'method': 'GET', 'status': '200'}
        metrics_collector.increment_counter('http_requests', tags=tags)

        assert metrics_collector.get_counter_value('http_requests') == 1.0

    def test_increment_counter_nonexistent(self, metrics_collector):
        """测试不存在的计数器"""
        assert metrics_collector.get_counter_value('nonexistent') == 0.0


class TestRecordTiming:
    """测试记录耗时"""

    def test_record_timing(self, metrics_collector):
        """测试记录耗时"""
        metrics_collector.record_timing('test_timing', 0.5)

        stats = metrics_collector.get_timing_stats('test_timing')
        assert stats['count'] == 1
        assert stats['avg'] == 0.5
        assert stats['min'] == 0.5
        assert stats['max'] == 0.5
        assert stats['total'] == 0.5

    def test_record_timing_multiple(self, metrics_collector):
        """测试多次记录耗时"""
        metrics_collector.record_timing('test_timing', 0.5)
        metrics_collector.record_timing('test_timing', 1.0)
        metrics_collector.record_timing('test_timing', 0.2)

        stats = metrics_collector.get_timing_stats('test_timing')
        assert stats['count'] == 3
        assert stats['avg'] == pytest.approx(0.5667, abs=0.001)
        assert stats['min'] == 0.2
        assert stats['max'] == 1.0
        assert stats['total'] == pytest.approx(1.7, abs=0.001)

    def test_record_timing_with_tags(self, metrics_collector):
        """测试带标签记录耗时"""
        tags = {'operation': 'database_query'}
        metrics_collector.record_timing('db_query', 0.1, tags=tags)

        stats = metrics_collector.get_timing_stats('db_query')
        assert stats['count'] == 1

    def test_record_timing_nonexistent(self, metrics_collector):
        """测试不存在的耗时"""
        stats = metrics_collector.get_timing_stats('nonexistent')
        assert stats['count'] == 0
        assert stats['avg'] == 0
        assert stats['min'] == 0
        assert stats['max'] == 0
        assert stats['total'] == 0


class TestSetGauge:
    """测试设置仪表盘值"""

    def test_set_gauge(self, metrics_collector):
        """测试设置仪表盘值"""
        metrics_collector.set_gauge('test_gauge', 42.0)

        assert metrics_collector.get_gauge_value('test_gauge') == 42.0

    def test_set_gauge_overwrite(self, metrics_collector):
        """测试覆盖仪表盘值"""
        metrics_collector.set_gauge('test_gauge', 42.0)
        metrics_collector.set_gauge('test_gauge', 100.0)

        assert metrics_collector.get_gauge_value('test_gauge') == 100.0

    def test_set_gauge_with_tags(self, metrics_collector):
        """测试带标签设置仪表盘值"""
        tags = {'host': 'server1'}
        metrics_collector.set_gauge('cpu_usage', 75.5, tags=tags)

        assert metrics_collector.get_gauge_value('cpu_usage') == 75.5

    def test_set_gauge_nonexistent(self, metrics_collector):
        """测试不存在的仪表盘"""
        assert metrics_collector.get_gauge_value('nonexistent') is None


class TestGetMetrics:
    """测试获取所有指标"""

    def test_get_metrics_empty(self, metrics_collector):
        """测试获取空指标"""
        metrics = metrics_collector.get_metrics()

        assert metrics == {}

    def test_get_metrics_with_data(self, metrics_collector):
        """测试获取有数据的指标"""
        metrics_collector.increment_counter('requests')
        metrics_collector.record_timing('response_time', 0.1)
        metrics_collector.set_gauge('active_connections', 10)

        metrics = metrics_collector.get_metrics()

        assert 'counter.requests' in metrics
        assert 'timing.response_time.count' in metrics
        assert 'gauge.active_connections' in metrics


class TestReset:
    """测试重置指标"""

    def test_reset(self, metrics_collector):
        """测试重置"""
        metrics_collector.increment_counter('test_counter')
        metrics_collector.record_timing('test_timing', 0.5)
        metrics_collector.set_gauge('test_gauge', 42.0)

        metrics_collector.reset()

        assert metrics_collector.get_counter_value('test_counter') == 0.0
        assert metrics_collector.get_timing_stats('test_timing')['count'] == 0
        assert metrics_collector.get_gauge_value('test_gauge') is None


class TestGetSummary:
    """测试获取指标摘要"""

    def test_get_summary_empty(self, metrics_collector):
        """测试获取空摘要"""
        summary = metrics_collector.get_summary()

        assert summary == "No metrics collected"

    def test_get_summary_with_data(self, metrics_collector):
        """测试获取有数据的摘要"""
        metrics_collector.increment_counter('requests')
        metrics_collector.record_timing('response_time', 0.1)
        metrics_collector.set_gauge('active_connections', 10)

        summary = metrics_collector.get_summary()

        assert 'Counters:' in summary
        assert 'Timings:' in summary
        assert 'Gauges:' in summary
        assert 'counter.requests' in summary
        assert 'timing.response_time' in summary
        assert 'gauge.active_connections' in summary


class TestMetricValue:
    """测试指标值"""

    def test_metric_value_creation(self):
        """测试创建指标值"""
        metric = MetricValue(
            value=42.0,
            timestamp=1234567890.0,
            tags={'key': 'value'},
        )

        assert metric.value == 42.0
        assert metric.timestamp == 1234567890.0
        assert metric.tags == {'key': 'value'}

    def test_metric_value_default_tags(self):
        """测试默认标签"""
        metric = MetricValue(
            value=42.0,
            timestamp=1234567890.0,
        )

        assert metric.tags == {}
