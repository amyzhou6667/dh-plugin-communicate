# 迭代6：超时处理机制技术设计

**创建日期**：2026-09-03
**版本**：v1.0
**状态**：设计阶段

## 功能目标

实现超时处理机制，处理用户长时间未回复的情况，包括：
1. 超时检测功能实现
2. 超时提醒功能实现
3. 超时策略执行
4. 任务状态同步

## 超时处理流程

```
任务状态流转：
PENDING → SENT → [等待回复]
                  ↓ (超时)
              TIMEOUT (提醒) → SENT (重新发送) → ...
                  ↓ (超过最大重试)
              FAILED
```

## 接口签名契约

### 1. 超时处理器 (TimeoutHandler)

```python
class TimeoutHandler:
    """超时处理器"""

    def __init__(self, task_repository: TaskRepository,
                 feishu_client: FeishuClient,
                 harness_client: HarnessClient,
                 config: Config):
        """初始化超时处理器

        Args:
            task_repository: 任务仓库
            feishu_client: 飞书客户端
            harness_client: Harness客户端
            config: 配置对象
        """

    def check_timeout_tasks(self) -> List[TimeoutResult]:
        """检查超时任务

        Returns:
            List[TimeoutResult]: 超时处理结果列表
        """

    def handle_timeout_task(self, task: Task) -> TimeoutResult:
        """处理单个超时任务

        Args:
            task: 超时任务

        Returns:
            TimeoutResult: 处理结果
        """

    def send_timeout_reminder(self, task: Task) -> bool:
        """发送超时提醒

        Args:
            task: 超时任务

        Returns:
            bool: 发送是否成功
        """

    def mark_task_timeout(self, task: Task) -> bool:
        """标记任务超时

        Args:
            task: 超时任务

        Returns:
            bool: 标记是否成功
        """

    def mark_task_failed(self, task: Task) -> bool:
        """标记任务失败

        Args:
            task: 超时任务

        Returns:
            bool: 标记是否成功
        """
```

### 2. 超时结果对象 (TimeoutResult)

```python
class TimeoutResult:
    """超时处理结果"""

    def __init__(self, task_id: str, action: str, success: bool, message: str):
        """初始化超时结果"""
        self.task_id = task_id
        self.action = action  # 'reminder', 'timeout', 'failed'
        self.success = success
        self.message = message
```

### 3. 超时调度器 (TimeoutScheduler)

```python
class TimeoutScheduler:
    """超时调度器"""

    def __init__(self, timeout_handler: TimeoutHandler, check_interval_seconds: int = 60):
        """初始化超时调度器

        Args:
            timeout_handler: 超时处理器
            check_interval_seconds: 检查间隔（秒）
        """

    def start(self):
        """启动调度器"""

    def stop(self):
        """停止调度器"""

    def check_once(self) -> List[TimeoutResult]:
        """执行一次检查"""
```

## 测试方案

### 单元测试

1. **TimeoutHandler 测试**
   - test_check_timeout_tasks: 测试检查超时任务
   - test_handle_timeout_task_reminder: 测试发送提醒
   - test_handle_timeout_task_timeout: 测试标记超时
   - test_handle_timeout_task_failed: 测试标记失败
   - test_send_timeout_reminder: 测试发送超时提醒

2. **TimeoutScheduler 测试**
   - test_start_stop: 测试启动和停止
   - test_check_once: 测试执行一次检查

## 依赖关系

- 依赖迭代1的 `TaskRepository` 和 `Task` 模型
- 依赖迭代3的 `FeishuClient` 发送提醒消息
- 依赖迭代2的 `HarnessClient` 通知超时
