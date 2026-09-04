# 迭代5：DeepSeek Harness 回复提交技术设计

**创建日期**：2026-09-03
**版本**：v1.0
**状态**：设计阶段

## 功能目标

实现将用户回复提交给 DeepSeek Harness 的功能，包括：
1. 回复提交功能实现
2. DeepSeek Harness API 集成
3. 错误处理与重试机制
4. 任务状态同步

## 接口签名契约

### 1. 回复提交服务 (ReplySubmitter)

```python
class ReplySubmitter:
    """回复提交服务"""

    def __init__(self, harness_client: HarnessClient, task_repository: TaskRepository):
        """初始化回复提交服务

        Args:
            harness_client: DeepSeek Harness 客户端
            task_repository: 任务仓库
        """

    def submit_reply(self, task_id: str, reply_text: str, user_id: str) -> ReplySubmitResult:
        """提交回复到 DeepSeek Harness

        Args:
            task_id: 任务ID
            reply_text: 回复文本
            user_id: 用户ID

        Returns:
            ReplySubmitResult: 提交结果
        """

    def submit_pending_replies(self) -> List[ReplySubmitResult]:
        """提交所有待处理的回复

        Returns:
            List[ReplySubmitResult]: 提交结果列表
        """

    def retry_failed_submissions(self, max_retries: int = 3) -> List[ReplySubmitResult]:
        """重试失败的提交

        Args:
            max_retries: 最大重试次数

        Returns:
            List[ReplySubmitResult]: 重试结果列表
        """
```

### 2. 提交结果对象 (ReplySubmitResult)

```python
class ReplySubmitResult:
    """回复提交结果"""

    def __init__(self, task_id: str, success: bool, message: str,
                 harness_response: Optional[dict] = None):
        """初始化提交结果"""
        self.task_id = task_id
        self.success = success
        self.message = message
        self.harness_response = harness_response
```

### 3. HarnessClient 增强

```python
class HarnessClient:
    # 现有方法...

    def submit_reply(self, task_id: str, reply_text: str, user_id: str) -> bool:
        """提交回复到 DeepSeek Harness

        Args:
            task_id: Harness任务ID
            reply_text: 回复文本
            user_id: 用户ID

        Returns:
            bool: 提交是否成功

        Raises:
            HarnessConnectionError: 连接失败
            HarnessAPIError: API调用失败
        """
```

## 测试方案

### 单元测试

1. **ReplySubmitter 测试**
   - test_submit_reply_success: 测试提交回复成功
   - test_submit_reply_task_not_found: 测试任务不存在
   - test_submit_reply_harness_error: 测试Harness API错误
   - test_submit_pending_replies: 测试提交待处理回复
   - test_retry_failed_submissions: 测试重试失败提交

2. **HarnessClient.submit_reply 测试**
   - test_submit_reply_success: 测试API调用成功
   - test_submit_reply_connection_error: 测试连接错误
   - test_submit_reply_api_error: 测试API错误

## 依赖关系

- 依赖迭代1的 `TaskRepository` 和 `Task` 模型
- 依赖迭代2的 `HarnessClient`
- 依赖迭代4的回调处理结果（REPLIED状态的任务）
