"""配置管理器测试"""

import os
import pytest
import tempfile
import yaml
from unittest.mock import patch

from src.services.config_manager import Config, ConfigManager


@pytest.fixture
def config_manager():
    """创建配置管理器实例"""
    return ConfigManager()


@pytest.fixture
def sample_config_file():
    """示例配置文件"""
    config = {
        'harness_base_url': 'http://test:3080',
        'feishu_app_id': 'test_app_id',
        'feishu_app_secret': 'test_app_secret',
        'bridge_port': 9090,
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        return f.name


class TestConfig:
    """测试配置类"""

    def test_config_default_values(self):
        """测试配置默认值"""
        config = Config()

        assert config.harness_base_url == 'http://127.0.0.1:3080'
        assert config.feishu_app_id == ''
        assert config.bridge_port == 8080
        assert config.poll_interval_seconds == 5

    def test_config_to_dict(self):
        """测试转换为字典"""
        config = Config()
        d = config.to_dict(mask_sensitive=False)

        assert d['harness_base_url'] == 'http://127.0.0.1:3080'
        assert d['feishu_app_id'] == ''

    def test_config_to_dict_masked(self):
        """测试转换为字典（遮盖敏感信息）"""
        config = Config(feishu_app_secret='test_secret_123')
        d = config.to_dict(mask_sensitive=True)

        assert d['feishu_app_secret'] != 'test_secret_123'
        assert '*' in d['feishu_app_secret']

    def test_config_is_sensitive(self):
        """测试判断敏感字段"""
        config = Config()

        assert config._is_sensitive('feishu_app_secret') is True
        assert config._is_sensitive('harness_api_key') is True
        assert config._is_sensitive('feishu_encrypt_key') is True
        assert config._is_sensitive('harness_base_url') is False
        assert config._is_sensitive('bridge_port') is False

    def test_config_mask_value(self):
        """测试遮盖值"""
        config = Config()

        assert config._mask_value(None) is None
        # 'short' 长度为5，大于4，所以会遮盖
        assert config._mask_value('short') == 'sh*rt'
        # 'long_value_here' 长度为14，保留前2后2，中间用*替换
        assert config._mask_value('long_value_here') == 'lo***********re'


class TestLoadConfig:
    """测试加载配置"""

    def test_load_config_from_file(self, config_manager, sample_config_file):
        """测试从文件加载配置"""
        config_manager.config_file = sample_config_file
        config = config_manager.load_config()

        assert config.feishu_app_id == 'test_app_id'
        assert config.bridge_port == 9090

        # 清理
        os.unlink(sample_config_file)

    def test_load_config_from_env(self, config_manager):
        """测试从环境变量加载配置"""
        with patch.dict(os.environ, {
            'FEISHU_APP_ID': 'env_app_id',
            'FEISHU_APP_SECRET': 'env_app_secret',
            'BRIDGE_PORT': '9090',
        }):
            config = config_manager.load_config()

            assert config.feishu_app_id == 'env_app_id'
            assert config.feishu_app_secret == 'env_app_secret'
            assert config.bridge_port == 9090

    def test_load_config_env_overrides_file(self, config_manager, sample_config_file):
        """测试环境变量覆盖文件配置"""
        config_manager.config_file = sample_config_file

        with patch.dict(os.environ, {
            'FEISHU_APP_ID': 'env_app_id',
        }):
            config = config_manager.load_config()

            assert config.feishu_app_id == 'env_app_id'

        # 清理
        os.unlink(sample_config_file)

    def test_load_config_no_file(self, config_manager):
        """测试没有配置文件"""
        config = config_manager.load_config()

        assert config.feishu_app_id == ''

    def test_load_config_nonexistent_file(self, config_manager):
        """测试不存在的配置文件"""
        config_manager.config_file = '/nonexistent/config.yaml'
        config = config_manager.load_config()

        assert config.feishu_app_id == ''


class TestValidateConfig:
    """测试验证配置"""

    def test_validate_config_valid(self, config_manager):
        """测试验证有效配置"""
        config = Config(
            feishu_app_id='test_app_id',
            feishu_app_secret='test_app_secret',
        )

        errors = config_manager.validate_config(config)

        assert len(errors) == 0

    def test_validate_config_missing_required(self, config_manager):
        """测试验证缺少必填字段"""
        config = Config()

        errors = config_manager.validate_config(config)

        assert len(errors) > 0
        assert any('feishu_app_id' in e for e in errors)
        assert any('feishu_app_secret' in e for e in errors)

    def test_validate_config_invalid_port(self, config_manager):
        """测试验证无效端口"""
        config = Config(
            feishu_app_id='test_app_id',
            feishu_app_secret='test_app_secret',
            bridge_port=99999,
        )

        errors = config_manager.validate_config(config)

        assert len(errors) > 0
        assert any('bridge_port' in e for e in errors)

    def test_validate_config_invalid_interval(self, config_manager):
        """测试验证无效轮询间隔"""
        config = Config(
            feishu_app_id='test_app_id',
            feishu_app_secret='test_app_secret',
            poll_interval_seconds=0,
        )

        errors = config_manager.validate_config(config)

        assert len(errors) > 0
        assert any('poll_interval_seconds' in e for e in errors)


class TestGetConfigSummary:
    """测试获取配置摘要"""

    def test_get_config_summary(self, config_manager):
        """测试获取配置摘要"""
        config = Config(
            feishu_app_id='test_app_id',
            feishu_app_secret='test_app_secret',
        )

        summary = config_manager.get_config_summary(config)

        assert 'feishu_app_id' in summary
        assert 'feishu_app_secret' in summary
        assert summary['feishu_app_secret'] != 'test_app_secret'
        assert '*' in summary['feishu_app_secret']
