"""错误处理器测试"""

import pytest
from unittest.mock import MagicMock

from src.services.error_handler import ErrorHandler, ErrorResponse, ErrorCategory, ErrorSeverity
from src.services.harness_client import HarnessConnectionError, HarnessAPIError
from src.services.feishu_client import FeishuAuthError, FeishuAPIError


@pytest.fixture
def error_handler():
    """创建错误处理器实例"""
    return ErrorHandler()


class TestCategorizeError:
    """测试错误分类"""

    def test_categorize_connection_error(self, error_handler):
        """测试连接错误分类"""
        error = HarnessConnectionError('Connection refused')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.CONNECTION

    def test_categorize_auth_error(self, error_handler):
        """测试认证错误分类"""
        error = FeishuAuthError('Invalid token')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.AUTHENTICATION

    def test_categorize_api_error(self, error_handler):
        """测试API错误分类"""
        error = HarnessAPIError('API error')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.INTERNAL

    def test_categorize_timeout_error(self, error_handler):
        """测试超时错误分类"""
        error = TimeoutError('Request timed out')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.TIMEOUT

    def test_categorize_value_error(self, error_handler):
        """测试值错误分类"""
        error = ValueError('Invalid value')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.VALIDATION

    def test_categorize_file_not_found(self, error_handler):
        """测试文件不存在错误分类"""
        error = FileNotFoundError('File not found')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.NOT_FOUND

    def test_categorize_permission_error(self, error_handler):
        """测试权限错误分类"""
        error = PermissionError('Permission denied')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.AUTHENTICATION

    def test_categorize_unknown_error(self, error_handler):
        """测试未知错误分类"""
        error = RuntimeError('Unknown error')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.UNKNOWN

    def test_categorize_by_message_timeout(self, error_handler):
        """测试通过消息分类超时错误"""
        error = Exception('Connection timeout occurred')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.TIMEOUT

    def test_categorize_by_message_connection(self, error_handler):
        """测试通过消息分类连接错误"""
        error = Exception('Connection refused by server')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.CONNECTION

    def test_categorize_by_message_auth(self, error_handler):
        """测试通过消息分类认证错误"""
        error = Exception('Authentication token expired')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.AUTHENTICATION

    def test_categorize_by_message_not_found(self, error_handler):
        """测试通过消息分类资源不存在错误"""
        error = Exception('Resource not found 404')
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.NOT_FOUND


class TestGetSeverity:
    """测试获取严重程度"""

    def test_get_severity_connection(self, error_handler):
        """测试连接错误严重程度"""
        severity = error_handler.get_severity(ErrorCategory.CONNECTION)
        assert severity == ErrorSeverity.HIGH

    def test_get_severity_auth(self, error_handler):
        """测试认证错误严重程度"""
        severity = error_handler.get_severity(ErrorCategory.AUTHENTICATION)
        assert severity == ErrorSeverity.HIGH

    def test_get_severity_validation(self, error_handler):
        """测试验证错误严重程度"""
        severity = error_handler.get_severity(ErrorCategory.VALIDATION)
        assert severity == ErrorSeverity.LOW

    def test_get_severity_not_found(self, error_handler):
        """测试资源不存在错误严重程度"""
        severity = error_handler.get_severity(ErrorCategory.NOT_FOUND)
        assert severity == ErrorSeverity.LOW

    def test_get_severity_timeout(self, error_handler):
        """测试超时错误严重程度"""
        severity = error_handler.get_severity(ErrorCategory.TIMEOUT)
        assert severity == ErrorSeverity.MEDIUM

    def test_get_severity_rate_limit(self, error_handler):
        """测试限流错误严重程度"""
        severity = error_handler.get_severity(ErrorCategory.RATE_LIMIT)
        assert severity == ErrorSeverity.MEDIUM

    def test_get_severity_internal(self, error_handler):
        """测试内部错误严重程度"""
        severity = error_handler.get_severity(ErrorCategory.INTERNAL)
        assert severity == ErrorSeverity.HIGH

    def test_get_severity_unknown(self, error_handler):
        """测试未知错误严重程度"""
        severity = error_handler.get_severity(ErrorCategory.UNKNOWN)
        assert severity == ErrorSeverity.MEDIUM


class TestHandleError:
    """测试处理错误"""

    def test_handle_connection_error(self, error_handler):
        """测试处理连接错误"""
        error = HarnessConnectionError('Connection refused')
        response = error_handler.handle_error(error)

        assert response.success is False
        assert response.error_code == 'ERR_CONNECTION'
        assert response.category == ErrorCategory.CONNECTION
        assert response.severity == ErrorSeverity.HIGH
        assert '连接失败' in response.message

    def test_handle_auth_error(self, error_handler):
        """测试处理认证错误"""
        error = FeishuAuthError('Invalid token')
        response = error_handler.handle_error(error)

        assert response.success is False
        assert response.error_code == 'ERR_AUTH'
        assert response.category == ErrorCategory.AUTHENTICATION
        assert response.severity == ErrorSeverity.HIGH
        assert '认证失败' in response.message

    def test_handle_validation_error(self, error_handler):
        """测试处理验证错误"""
        error = ValueError('Invalid value')
        response = error_handler.handle_error(error)

        assert response.success is False
        assert response.error_code == 'ERR_VALIDATION'
        assert response.category == ErrorCategory.VALIDATION
        assert response.severity == ErrorSeverity.LOW
        assert '数据验证失败' in response.message

    def test_handle_error_with_context(self, error_handler):
        """测试处理带上下文的错误"""
        error = Exception('Test error')
        context = {'task_id': 'task_123', 'operation': 'submit_reply'}
        response = error_handler.handle_error(error, context)

        assert response.success is False
        assert response.details is not None
        assert response.details['context'] == context

    def test_handle_error_response_to_dict(self, error_handler):
        """测试错误响应转换为字典"""
        error = Exception('Test error')
        response = error_handler.handle_error(error)
        d = response.to_dict()

        assert d['success'] is False
        assert 'error_code' in d
        assert 'message' in d
        assert 'category' in d
        assert 'severity' in d


class TestErrorResponse:
    """测试错误响应"""

    def test_error_response_default(self):
        """测试错误响应默认值"""
        response = ErrorResponse()
        assert response.success is False
        assert response.error_code == ''
        assert response.message == ''
        assert response.category == ErrorCategory.UNKNOWN
        assert response.severity == ErrorSeverity.MEDIUM
        assert response.details is None
        assert response.traceback is None

    def test_error_response_to_dict(self):
        """测试错误响应转换为字典"""
        response = ErrorResponse(
            success=False,
            error_code='ERR_TEST',
            message='Test error',
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.HIGH,
            details={'key': 'value'},
        )
        d = response.to_dict()

        assert d['success'] is False
        assert d['error_code'] == 'ERR_TEST'
        assert d['message'] == 'Test error'
        assert d['category'] == 'internal'
        assert d['severity'] == 'high'
        assert d['details'] == {'key': 'value'}
