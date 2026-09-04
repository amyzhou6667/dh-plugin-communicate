"""错误处理器模块

负责错误分类、处理和响应生成。
"""

import logging
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from src.services.harness_client import HarnessConnectionError, HarnessAPIError
from src.services.feishu_client import FeishuAuthError, FeishuAPIError

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """错误分类"""
    CONNECTION = 'connection'
    AUTHENTICATION = 'authentication'
    VALIDATION = 'validation'
    NOT_FOUND = 'not_found'
    TIMEOUT = 'timeout'
    RATE_LIMIT = 'rate_limit'
    INTERNAL = 'internal'
    UNKNOWN = 'unknown'


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass
class ErrorResponse:
    """错误响应"""

    success: bool = False
    error_code: str = ''
    message: str = ''
    category: ErrorCategory = ErrorCategory.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    details: Optional[Dict[str, Any]] = None
    traceback: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        result = {
            'success': self.success,
            'error_code': self.error_code,
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
        }
        if self.details:
            result['details'] = self.details
        return result


class ErrorHandler:
    """错误处理器"""

    # 错误分类映射
    ERROR_CATEGORY_MAP = {
        HarnessConnectionError: ErrorCategory.CONNECTION,
        HarnessAPIError: ErrorCategory.INTERNAL,
        FeishuAuthError: ErrorCategory.AUTHENTICATION,
        FeishuAPIError: ErrorCategory.INTERNAL,
        ConnectionError: ErrorCategory.CONNECTION,
        TimeoutError: ErrorCategory.TIMEOUT,
        ValueError: ErrorCategory.VALIDATION,
        KeyError: ErrorCategory.VALIDATION,
        FileNotFoundError: ErrorCategory.NOT_FOUND,
        PermissionError: ErrorCategory.AUTHENTICATION,
    }

    # 严重程度映射
    SEVERITY_MAP = {
        ErrorCategory.CONNECTION: ErrorSeverity.HIGH,
        ErrorCategory.AUTHENTICATION: ErrorSeverity.HIGH,
        ErrorCategory.VALIDATION: ErrorSeverity.LOW,
        ErrorCategory.NOT_FOUND: ErrorSeverity.LOW,
        ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
        ErrorCategory.RATE_LIMIT: ErrorSeverity.MEDIUM,
        ErrorCategory.INTERNAL: ErrorSeverity.HIGH,
        ErrorCategory.UNKNOWN: ErrorSeverity.MEDIUM,
    }

    # 错误代码映射
    ERROR_CODE_MAP = {
        ErrorCategory.CONNECTION: 'ERR_CONNECTION',
        ErrorCategory.AUTHENTICATION: 'ERR_AUTH',
        ErrorCategory.VALIDATION: 'ERR_VALIDATION',
        ErrorCategory.NOT_FOUND: 'ERR_NOT_FOUND',
        ErrorCategory.TIMEOUT: 'ERR_TIMEOUT',
        ErrorCategory.RATE_LIMIT: 'ERR_RATE_LIMIT',
        ErrorCategory.INTERNAL: 'ERR_INTERNAL',
        ErrorCategory.UNKNOWN: 'ERR_UNKNOWN',
    }

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorResponse:
        """处理错误

        Args:
            error: 异常对象
            context: 上下文信息

        Returns:
            ErrorResponse: 错误响应
        """
        # 分类错误
        category = self.categorize_error(error)

        # 获取严重程度
        severity = self.get_severity(category)

        # 获取错误代码
        error_code = self.ERROR_CODE_MAP.get(category, 'ERR_UNKNOWN')

        # 构建错误消息
        message = self._build_error_message(error, category)

        # 构建详情
        details = self._build_error_details(error, context)

        # 记录日志
        self._log_error(error, category, severity, context)

        return ErrorResponse(
            success=False,
            error_code=error_code,
            message=message,
            category=category,
            severity=severity,
            details=details,
            traceback=traceback.format_exc(),
        )

    def categorize_error(self, error: Exception) -> ErrorCategory:
        """分类错误

        Args:
            error: 异常对象

        Returns:
            ErrorCategory: 错误分类
        """
        # 直接映射
        for error_type, category in self.ERROR_CATEGORY_MAP.items():
            if isinstance(error, error_type):
                return category

        # 根据错误消息判断
        error_msg = str(error).lower()
        if 'timeout' in error_msg:
            return ErrorCategory.TIMEOUT
        elif 'connection' in error_msg or 'refused' in error_msg:
            return ErrorCategory.CONNECTION
        elif 'auth' in error_msg or 'token' in error_msg:
            return ErrorCategory.AUTHENTICATION
        elif 'not found' in error_msg or '404' in error_msg:
            return ErrorCategory.NOT_FOUND
        elif 'rate limit' in error_msg or '429' in error_msg:
            return ErrorCategory.RATE_LIMIT
        elif 'validation' in error_msg or 'invalid' in error_msg:
            return ErrorCategory.VALIDATION

        return ErrorCategory.UNKNOWN

    def get_severity(self, category: ErrorCategory) -> ErrorSeverity:
        """获取错误严重程度

        Args:
            category: 错误分类

        Returns:
            ErrorSeverity: 严重程度
        """
        return self.SEVERITY_MAP.get(category, ErrorSeverity.MEDIUM)

    def _build_error_message(self, error: Exception, category: ErrorCategory) -> str:
        """构建错误消息

        Args:
            error: 异常对象
            category: 错误分类

        Returns:
            str: 错误消息
        """
        base_messages = {
            ErrorCategory.CONNECTION: '连接失败，请检查网络或服务状态',
            ErrorCategory.AUTHENTICATION: '认证失败，请检查凭据',
            ErrorCategory.VALIDATION: '数据验证失败',
            ErrorCategory.NOT_FOUND: '资源不存在',
            ErrorCategory.TIMEOUT: '操作超时',
            ErrorCategory.RATE_LIMIT: '请求过于频繁，请稍后重试',
            ErrorCategory.INTERNAL: '内部服务错误',
            ErrorCategory.UNKNOWN: '未知错误',
        }

        base_msg = base_messages.get(category, '未知错误')
        return f'{base_msg}: {str(error)}'

    def _build_error_details(self, error: Exception, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """构建错误详情

        Args:
            error: 异常对象
            context: 上下文信息

        Returns:
            Optional[Dict[str, Any]]: 错误详情
        """
        details = {}

        if context:
            details['context'] = context

        details['error_type'] = type(error).__name__
        details['error_message'] = str(error)

        return details if details else None

    def _log_error(self, error: Exception, category: ErrorCategory,
                   severity: ErrorSeverity, context: Optional[Dict[str, Any]]):
        """记录错误日志

        Args:
            error: 异常对象
            category: 错误分类
            severity: 严重程度
            context: 上下文信息
        """
        log_message = f'[{category.value}] {str(error)}'

        if context:
            log_message += f' | Context: {context}'

        if severity in (ErrorSeverity.HIGH, ErrorSeverity.CRITICAL):
            logger.error(log_message, exc_info=True)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
