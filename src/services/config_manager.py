"""配置管理器模块

负责加载、验证和管理配置。
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """配置类"""

    # DeepSeek Harness 配置
    harness_base_url: str = 'http://127.0.0.1:3080'
    harness_api_key: Optional[str] = None

    # 飞书配置
    feishu_app_id: str = ''
    feishu_app_secret: str = ''
    feishu_encrypt_key: Optional[str] = None
    feishu_verification_token: Optional[str] = None

    # 应用配置
    bridge_port: int = 8080
    poll_interval_seconds: int = 5
    default_timeout_seconds: int = 300
    max_retry_count: int = 3

    # 数据库配置
    database_url: str = 'sqlite:///bridge.db'

    # 日志配置
    log_level: str = 'INFO'
    log_file: Optional[str] = None

    def to_dict(self, mask_sensitive: bool = True) -> Dict[str, Any]:
        """转换为字典

        Args:
            mask_sensitive: 是否遮盖敏感信息

        Returns:
            Dict[str, Any]: 配置字典
        """
        result = {}

        for key, value in self.__dict__.items():
            if mask_sensitive and self._is_sensitive(key):
                result[key] = self._mask_value(value)
            else:
                result[key] = value

        return result

    def _is_sensitive(self, key: str) -> bool:
        """判断是否是敏感字段

        Args:
            key: 字段名

        Returns:
            bool: 是否敏感
        """
        sensitive_keywords = ['secret', 'key', 'token', 'password']
        return any(keyword in key.lower() for keyword in sensitive_keywords)

    def _mask_value(self, value: Any) -> Any:
        """遮盖敏感值

        Args:
            value: 原始值

        Returns:
            Any: 遮盖后的值
        """
        if value is None:
            return None
        if isinstance(value, str) and len(value) > 4:
            return value[:2] + '*' * (len(value) - 4) + value[-2:]
        return '***'


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file

    def load_config(self) -> Config:
        """加载配置

        配置来源优先级：
        1. 环境变量（最高优先级）
        2. 配置文件
        3. 默认值（最低优先级）

        Returns:
            Config: 配置对象
        """
        # 从配置文件加载
        file_config = self._load_from_file()

        # 从环境变量加载（覆盖文件配置）
        env_config = self._load_from_env()

        # 合并配置
        config = self._merge_config(file_config, env_config)

        logger.info("Configuration loaded successfully")
        return config

    def _load_from_file(self) -> Dict[str, Any]:
        """从配置文件加载

        Returns:
            Dict[str, Any]: 配置字典
        """
        if not self.config_file:
            return {}

        config_path = Path(self.config_file)
        if not config_path.exists():
            logger.warning("Config file not found: %s", self.config_file)
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if config is None:
                return {}

            logger.info("Loaded config from file: %s", self.config_file)
            return config

        except Exception as e:
            logger.error("Failed to load config file: %s", e)
            return {}

    def _load_from_env(self) -> Dict[str, Any]:
        """从环境变量加载

        Returns:
            Dict[str, Any]: 配置字典
        """
        env_mapping = {
            'HARNESS_BASE_URL': 'harness_base_url',
            'HARNESS_API_KEY': 'harness_api_key',
            'FEISHU_APP_ID': 'feishu_app_id',
            'FEISHU_APP_SECRET': 'feishu_app_secret',
            'FEISHU_ENCRYPT_KEY': 'feishu_encrypt_key',
            'FEISHU_VERIFICATION_TOKEN': 'feishu_verification_token',
            'BRIDGE_PORT': 'bridge_port',
            'POLL_INTERVAL_SECONDS': 'poll_interval_seconds',
            'DEFAULT_TIMEOUT_SECONDS': 'default_timeout_seconds',
            'MAX_RETRY_COUNT': 'max_retry_count',
            'DATABASE_URL': 'database_url',
            'LOG_LEVEL': 'log_level',
            'LOG_FILE': 'log_file',
        }

        config = {}
        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # 类型转换
                if config_key in ('bridge_port', 'poll_interval_seconds',
                                  'default_timeout_seconds', 'max_retry_count'):
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning("Invalid integer value for %s: %s", env_var, value)
                        continue

                config[config_key] = value

        if config:
            logger.info("Loaded config from environment variables")

        return config

    def _merge_config(self, file_config: Dict[str, Any], env_config: Dict[str, Any]) -> Config:
        """合并配置

        Args:
            file_config: 文件配置
            env_config: 环境变量配置

        Returns:
            Config: 配置对象
        """
        # 创建默认配置
        config = Config()

        # 应用文件配置
        for key, value in file_config.items():
            if hasattr(config, key):
                setattr(config, key, value)

        # 应用环境变量配置（优先级更高）
        for key, value in env_config.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    def validate_config(self, config: Config) -> List[str]:
        """验证配置

        Args:
            config: 配置对象

        Returns:
            List[str]: 错误消息列表，空列表表示验证通过
        """
        errors = []

        # 验证必填字段
        if not config.feishu_app_id:
            errors.append("feishu_app_id is required")

        if not config.feishu_app_secret:
            errors.append("feishu_app_secret is required")

        # 验证数值范围
        if config.bridge_port < 1 or config.bridge_port > 65535:
            errors.append(f"bridge_port must be between 1 and 65535, got {config.bridge_port}")

        if config.poll_interval_seconds < 1:
            errors.append(f"poll_interval_seconds must be positive, got {config.poll_interval_seconds}")

        if config.default_timeout_seconds < 1:
            errors.append(f"default_timeout_seconds must be positive, got {config.default_timeout_seconds}")

        if config.max_retry_count < 0:
            errors.append(f"max_retry_count must be non-negative, got {config.max_retry_count}")

        # 验证URL格式
        if not config.harness_base_url.startswith(('http://', 'https://')):
            errors.append(f"Invalid harness_base_url: {config.harness_base_url}")

        return errors

    def get_config_summary(self, config: Config) -> Dict[str, Any]:
        """获取配置摘要（脱敏）

        Args:
            config: 配置对象

        Returns:
            Dict[str, Any]: 配置摘要
        """
        return config.to_dict(mask_sensitive=True)
