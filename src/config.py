"""
配置管理模块
"""
import os
import yaml
import json
from typing import Optional, Dict, Any


class Config:
    """配置类"""

    _instance = None

    def __init__(self, **kwargs):
        """初始化配置"""
        # DeepSeek Harness 配置
        self.harness_base_url = kwargs.get('harness_base_url', 'http://127.0.0.1:3080')
        self.harness_api_key = kwargs.get('harness_api_key', None)

        # 飞书配置
        self.feishu_app_id = kwargs.get('feishu_app_id', '')
        self.feishu_app_secret = kwargs.get('feishu_app_secret', '')
        self.feishu_encrypt_key = kwargs.get('feishu_encrypt_key', None)
        self.feishu_verification_token = kwargs.get('feishu_verification_token', None)

        # 插件配置
        self.bridge_port = kwargs.get('bridge_port', 5000)
        self.poll_interval_seconds = kwargs.get('poll_interval_seconds', 5)
        self.default_timeout_seconds = kwargs.get('default_timeout_seconds', 300)
        self.max_retry_count = kwargs.get('max_retry_count', 3)
        self.database_url = kwargs.get('database_url', 'sqlite:///:memory:')

        # 验证配置
        self._validate()

    def _validate(self):
        """验证配置"""
        # 验证端口
        if not (1 <= self.bridge_port <= 65535):
            raise ValueError('bridge_port must be between 1 and 65535')

        # 验证超时时间
        if self.default_timeout_seconds <= 0:
            raise ValueError('default_timeout_seconds must be positive')

        # 验证轮询间隔
        if self.poll_interval_seconds <= 0:
            raise ValueError('poll_interval_seconds must be positive')

        # 验证最大重试次数
        if self.max_retry_count < 0:
            raise ValueError('max_retry_count must be non-negative')

        # 验证URL格式
        if self.harness_base_url and not self._is_valid_url(self.harness_base_url):
            raise ValueError('Invalid URL format')

        # 验证飞书配置（测试环境可选）
        if not self.feishu_app_id:
            raise ValueError('feishu_app_id is required')

        if not self.feishu_app_secret:
            raise ValueError('feishu_app_secret is required')

    def _is_valid_url(self, url: str) -> bool:
        """验证URL格式"""
        if not url:
            return True

        # 简单验证HTTP/HTTPS URL
        return url.startswith('http://') or url.startswith('https://')

    @classmethod
    def from_env(cls) -> 'Config':
        """从环境变量创建配置"""
        return cls(
            harness_base_url=os.environ.get('HARNESS_BASE_URL', 'http://127.0.0.1:3080'),
            harness_api_key=os.environ.get('HARNESS_API_KEY'),
            feishu_app_id=os.environ.get('FEISHU_APP_ID', ''),
            feishu_app_secret=os.environ.get('FEISHU_APP_SECRET', ''),
            feishu_encrypt_key=os.environ.get('FEISHU_ENCRYPT_KEY'),
            feishu_verification_token=os.environ.get('FEISHU_VERIFICATION_TOKEN'),
            bridge_port=int(os.environ.get('BRIDGE_PORT', '5000')),
            poll_interval_seconds=int(os.environ.get('POLL_INTERVAL_SECONDS', '5')),
            default_timeout_seconds=int(os.environ.get('DEFAULT_TIMEOUT_SECONDS', '300')),
            max_retry_count=int(os.environ.get('MAX_RETRY_COUNT', '3')),
            database_url=os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """从字典创建配置"""
        return cls(**data)

    @classmethod
    def from_yaml(cls, file_path: str) -> 'Config':
        """从YAML文件创建配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_json(cls, file_path: str) -> 'Config':
        """从JSON文件创建配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不包含敏感信息）"""
        return {
            'harness_base_url': self.harness_base_url,
            'feishu_app_id': self.feishu_app_id,
            'bridge_port': self.bridge_port,
            'poll_interval_seconds': self.poll_interval_seconds,
            'default_timeout_seconds': self.default_timeout_seconds,
            'max_retry_count': self.max_retry_count,
            'database_url': self.database_url
        }

    def get_harness_url(self, path: str) -> str:
        """获取DeepSeek Harness URL"""
        base_url = self.harness_base_url.rstrip('/')
        path = path.lstrip('/')
        return f'{base_url}/{path}'

    def is_valid(self) -> bool:
        """检查配置是否有效"""
        try:
            self._validate()
            return True
        except ValueError:
            return False


def get_config() -> Config:
    """获取配置单例"""
    if Config._instance is None:
        Config._instance = Config.from_env()
    return Config._instance


def reload_config() -> Config:
    """重新加载配置"""
    Config._instance = Config.from_env()
    return Config._instance