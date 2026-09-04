"""
配置管理模块测试
基于接口签名契约设计测试用例
"""
import pytest
import os
import tempfile


class TestConfig:
    """配置类测试"""

    def test_config_initialization_with_defaults(self):
        """测试配置类使用默认值初始化"""
        from src.config import Config

        # 测试环境需要提供飞书配置
        config = Config(
            feishu_app_id='test_app_id',
            feishu_app_secret='test_app_secret'
        )

        # 验证默认值
        assert config.harness_base_url == 'http://127.0.0.1:3080'
        assert config.harness_api_key is None
        assert config.feishu_app_id == 'test_app_id'
        assert config.feishu_app_secret == 'test_app_secret'
        assert config.feishu_encrypt_key is None
        assert config.feishu_verification_token is None
        assert config.bridge_port == 5000
        assert config.poll_interval_seconds == 5
        assert config.default_timeout_seconds == 300
        assert config.max_retry_count == 3
        assert config.database_url == 'sqlite:///:memory:'

    def test_config_initialization_with_custom_values(self):
        """测试配置类使用自定义值初始化"""
        from src.config import Config

        config = Config(
            harness_base_url='http://192.168.1.100:3080',
            harness_api_key='test_api_key',
            feishu_app_id='cli_test123',
            feishu_app_secret='test_secret',
            feishu_encrypt_key='test_encrypt_key',
            feishu_verification_token='test_token',
            bridge_port=8080,
            poll_interval_seconds=10,
            default_timeout_seconds=600,
            max_retry_count=5,
            database_url='sqlite:///test.db'
        )

        assert config.harness_base_url == 'http://192.168.1.100:3080'
        assert config.harness_api_key == 'test_api_key'
        assert config.feishu_app_id == 'cli_test123'
        assert config.feishu_app_secret == 'test_secret'
        assert config.feishu_encrypt_key == 'test_encrypt_key'
        assert config.feishu_verification_token == 'test_token'
        assert config.bridge_port == 8080
        assert config.poll_interval_seconds == 10
        assert config.default_timeout_seconds == 600
        assert config.max_retry_count == 5
        assert config.database_url == 'sqlite:///test.db'

    def test_config_from_env_variables(self, monkeypatch):
        """测试从环境变量加载配置"""
        from src.config import Config

        # 设置环境变量
        monkeypatch.setenv('HARNESS_BASE_URL', 'http://env.test:3080')
        monkeypatch.setenv('HARNESS_API_KEY', 'env_api_key')
        monkeypatch.setenv('FEISHU_APP_ID', 'env_app_id')
        monkeypatch.setenv('FEISHU_APP_SECRET', 'env_secret')
        monkeypatch.setenv('BRIDGE_PORT', '9090')
        monkeypatch.setenv('POLL_INTERVAL_SECONDS', '15')
        monkeypatch.setenv('DEFAULT_TIMEOUT_SECONDS', '900')
        monkeypatch.setenv('MAX_RETRY_COUNT', '10')
        monkeypatch.setenv('DATABASE_URL', 'sqlite:///env_test.db')

        config = Config.from_env()

        assert config.harness_base_url == 'http://env.test:3080'
        assert config.harness_api_key == 'env_api_key'
        assert config.feishu_app_id == 'env_app_id'
        assert config.feishu_app_secret == 'env_secret'
        assert config.bridge_port == 9090
        assert config.poll_interval_seconds == 15
        assert config.default_timeout_seconds == 900
        assert config.max_retry_count == 10
        assert config.database_url == 'sqlite:///env_test.db'

    def test_config_validation_invalid_port(self):
        """测试配置验证：无效端口"""
        from src.config import Config

        with pytest.raises(ValueError, match='bridge_port must be between 1 and 65535'):
            Config(bridge_port=0)

        with pytest.raises(ValueError, match='bridge_port must be between 1 and 65535'):
            Config(bridge_port=70000)

    def test_config_validation_invalid_timeout(self):
        """测试配置验证：无效超时时间"""
        from src.config import Config

        with pytest.raises(ValueError, match='default_timeout_seconds must be positive'):
            Config(default_timeout_seconds=0)

        with pytest.raises(ValueError, match='default_timeout_seconds must be positive'):
            Config(default_timeout_seconds=-1)

    def test_config_validation_invalid_poll_interval(self):
        """测试配置验证：无效轮询间隔"""
        from src.config import Config

        with pytest.raises(ValueError, match='poll_interval_seconds must be positive'):
            Config(poll_interval_seconds=0)

        with pytest.raises(ValueError, match='poll_interval_seconds must be positive'):
            Config(poll_interval_seconds=-1)

    def test_config_validation_invalid_max_retry_count(self):
        """测试配置验证：无效最大重试次数"""
        from src.config import Config

        with pytest.raises(ValueError, match='max_retry_count must be non-negative'):
            Config(max_retry_count=-1)

    def test_config_to_dict(self, sample_config):
        """测试配置转换为字典"""
        config_dict = sample_config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict['harness_base_url'] == 'http://127.0.0.1:3080'
        assert config_dict['feishu_app_id'] == 'test_app_id'
        assert config_dict['bridge_port'] == 5000
        assert 'feishu_app_secret' not in config_dict  # 敏感信息不应包含

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        from src.config import Config

        config_dict = {
            'harness_base_url': 'http://dict.test:3080',
            'feishu_app_id': 'dict_app_id',
            'feishu_app_secret': 'dict_secret',
            'bridge_port': 3000,
            'poll_interval_seconds': 20,
            'default_timeout_seconds': 1200,
            'max_retry_count': 7,
            'database_url': 'sqlite:///dict_test.db'
        }

        config = Config.from_dict(config_dict)

        assert config.harness_base_url == 'http://dict.test:3080'
        assert config.feishu_app_id == 'dict_app_id'
        assert config.feishu_app_secret == 'dict_secret'
        assert config.bridge_port == 3000

    def test_config_load_from_yaml_file(self, tmp_path):
        """测试从YAML文件加载配置"""
        from src.config import Config

        # 创建临时YAML文件
        yaml_content = """
harness_base_url: "http://yaml.test:3080"
feishu_app_id: "yaml_app_id"
feishu_app_secret: "yaml_secret"
bridge_port: 4000
poll_interval_seconds: 25
default_timeout_seconds: 1500
max_retry_count: 8
database_url: "sqlite:///yaml_test.db"
"""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(yaml_content)

        config = Config.from_yaml(str(yaml_file))

        assert config.harness_base_url == 'http://yaml.test:3080'
        assert config.feishu_app_id == 'yaml_app_id'
        assert config.bridge_port == 4000

    def test_config_load_from_json_file(self, tmp_path):
        """测试从JSON文件加载配置"""
        from src.config import Config
        import json

        # 创建临时JSON文件
        json_content = {
            "harness_base_url": "http://json.test:3080",
            "feishu_app_id": "json_app_id",
            "feishu_app_secret": "json_secret",
            "bridge_port": 5000,
            "poll_interval_seconds": 30,
            "default_timeout_seconds": 1800,
            "max_retry_count": 9,
            "database_url": "sqlite:///json_test.db"
        }
        json_file = tmp_path / "config.json"
        json_file.write_text(json.dumps(json_content))

        config = Config.from_json(str(json_file))

        assert config.harness_base_url == 'http://json.test:3080'
        assert config.feishu_app_id == 'json_app_id'
        assert config.bridge_port == 5000

    def test_config_missing_required_field(self):
        """测试缺少必需字段"""
        from src.config import Config

        # 飞书配置是必需的
        with pytest.raises(ValueError, match='feishu_app_id is required'):
            Config(feishu_app_id='', feishu_app_secret='test_secret')

        with pytest.raises(ValueError, match='feishu_app_secret is required'):
            Config(feishu_app_id='test_id', feishu_app_secret='')

    def test_config_invalid_url_format(self):
        """测试无效URL格式"""
        from src.config import Config

        with pytest.raises(ValueError, match='Invalid URL format'):
            Config(harness_base_url='invalid-url')

        with pytest.raises(ValueError, match='Invalid URL format'):
            Config(harness_base_url='ftp://invalid-protocol')

    def test_config_singleton_pattern(self, monkeypatch):
        """测试配置单例模式"""
        from src.config import Config, get_config

        # 重置单例
        Config._instance = None

        # 设置环境变量
        monkeypatch.setenv('FEISHU_APP_ID', 'test_app_id')
        monkeypatch.setenv('FEISHU_APP_SECRET', 'test_app_secret')

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_config_reload(self, monkeypatch):
        """测试配置重新加载"""
        from src.config import Config, get_config, reload_config

        # 重置单例
        Config._instance = None

        # 设置初始环境变量
        monkeypatch.setenv('HARNESS_BASE_URL', 'http://initial.test:3080')
        monkeypatch.setenv('FEISHU_APP_ID', 'test_app_id')
        monkeypatch.setenv('FEISHU_APP_SECRET', 'test_app_secret')
        config1 = get_config()
        assert config1.harness_base_url == 'http://initial.test:3080'

        # 修改环境变量
        monkeypatch.setenv('HARNESS_BASE_URL', 'http://reloaded.test:3080')
        config2 = reload_config()
        assert config2.harness_base_url == 'http://reloaded.test:3080'

        # 验证配置值已更新
        assert config2.harness_base_url == 'http://reloaded.test:3080'

    def test_config_get_harness_url(self, sample_config):
        """测试获取DeepSeek Harness URL"""
        url = sample_config.get_harness_url('/api/tasks/pending')
        assert url == 'http://127.0.0.1:3080/api/tasks/pending'

    def test_config_get_harness_url_with_trailing_slash(self):
        """测试获取DeepSeek Harness URL（末尾有斜杠）"""
        from src.config import Config

        config = Config(
            harness_base_url='http://127.0.0.1:3080/',
            feishu_app_id='test_app_id',
            feishu_app_secret='test_app_secret'
        )
        url = config.get_harness_url('/api/tasks/pending')
        assert url == 'http://127.0.0.1:3080/api/tasks/pending'

    def test_config_is_valid(self, sample_config):
        """测试配置有效性检查"""
        assert sample_config.is_valid() is True

    def test_config_is_valid_missing_feishu_credentials(self):
        """测试配置有效性检查：缺少飞书凭证"""
        from src.config import Config

        # 测试环境需要提供飞书配置，但这里测试验证逻辑
        try:
            config = Config(
                feishu_app_id='',
                feishu_app_secret='test_secret'
            )
            # 如果没有抛出异常，则is_valid应该返回False
            assert config.is_valid() is False
        except ValueError:
            # 如果抛出异常，也是预期的
            pass

    def test_config_is_valid_missing_harness_url(self):
        """测试配置有效性检查：缺少Harness URL"""
        from src.config import Config

        # 空URL应该被认为是有效的（可选字段）
        config = Config(
            harness_base_url='',
            feishu_app_id='test_id',
            feishu_app_secret='test_secret'
        )
        assert config.is_valid() is True