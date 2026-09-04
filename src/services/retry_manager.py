"""重试管理器模块

负责实现重试机制，支持指数退避策略。
"""

import logging
import time
from typing import Any, Callable, Optional, Tuple, Type

from src.services.error_handler import ErrorHandler, ErrorCategory

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """重试耗尽错误"""

    def __init__(self, message: str, last_error: Exception, attempts: int):
        """初始化重试耗尽错误"""
        super().__init__(message)
        self.last_error = last_error
        self.attempts = attempts


class RetryManager:
    """重试管理器"""

    # 不可重试的错误类型
    NON_RETRYABLE_CATEGORIES = {
        ErrorCategory.AUTHENTICATION,
        ErrorCategory.VALIDATION,
        ErrorCategory.NOT_FOUND,
    }

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, exponential_base: float = 2.0,
                 error_handler: Optional[ErrorHandler] = None):
        """初始化重试管理器

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            exponential_base: 指数退避基数
            error_handler: 错误处理器
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.error_handler = error_handler or ErrorHandler()

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """执行带重试的函数

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Any: 函数返回值

        Raises:
            RetryExhaustedError: 重试耗尽
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e

                # 检查是否应该重试
                if not self.should_retry(e, attempt):
                    logger.warning("Error not retryable, raising immediately: %s", e)
                    raise

                # 最后一次尝试失败
                if attempt == self.max_retries:
                    break

                # 计算延迟时间
                delay = self.get_delay(attempt)

                logger.warning(
                    "Attempt %d/%d failed: %s. Retrying in %.1f seconds...",
                    attempt + 1, self.max_retries + 1, e, delay
                )

                # 等待
                time.sleep(delay)

        # 所有重试都失败了
        raise RetryExhaustedError(
            f"All {self.max_retries + 1} attempts failed",
            last_error=last_error,
            attempts=self.max_retries + 1,
        )

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试

        Args:
            error: 异常对象
            attempt: 当前尝试次数

        Returns:
            bool: 是否应该重试
        """
        # 检查是否超过最大重试次数
        if attempt >= self.max_retries:
            return False

        # 分类错误
        category = self.error_handler.categorize_error(error)

        # 检查是否是不可重试的错误类型
        if category in self.NON_RETRYABLE_CATEGORIES:
            logger.debug("Error category %s is not retryable", category.value)
            return False

        return True

    def get_delay(self, attempt: int) -> float:
        """获取重试延迟时间

        使用指数退避策略：delay = base_delay * (exponential_base ^ attempt)

        Args:
            attempt: 当前尝试次数

        Returns:
            float: 延迟时间（秒）
        """
        delay = self.base_delay * (self.exponential_base ** attempt)

        # 限制最大延迟
        delay = min(delay, self.max_delay)

        return delay

    def execute_with_retry_and_fallback(
        self,
        func: Callable,
        fallback: Callable,
        *args,
        **kwargs
    ) -> Tuple[Any, bool]:
        """执行带重试和降级的函数

        Args:
            func: 要执行的函数
            fallback: 降级函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Tuple[Any, bool]: (返回值, 是否使用了降级)
        """
        try:
            result = self.execute_with_retry(func, *args, **kwargs)
            return result, False
        except RetryExhaustedError:
            logger.warning("All retries exhausted, using fallback")
            result = fallback(*args, **kwargs)
            return result, True
