# 迭代2：DeepSeek Harness 集成技术设计

**创建日期**：2026-09-03
**版本**：v1.0
**状态**：设计阶段

## 功能目标

实现从 DeepSeek Harness 获取待确认任务的功能，包括：
1. DeepSeek Harness 客户端实现
2. 任务发现模块实现
3. 轮询机制实现

## 接口签名契约

### 1. DeepSeek Harness 客户端 (HarnessClient)

```python
class HarnessClient:
    """DeepSeek Harness 客户端"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """初始化客户端
        
        Args:
            base_url: DeepSeek Harness 基础URL
            api_key: API密钥（可选）
        """
    
    def get_pending_tasks(self) -> List[dict]:
        """获取待确认任务列表
        
        Returns:
            List[dict]: 任务列表，每个任务包含 id, content, context 等字段
            
        Raises:
            HarnessConnectionError: 连接失败
            HarnessAPIError: API调用失败
        """
    
    def submit_reply(self, task_id: str, reply_text: str, user_id: str) -> bool:
        """提交用户回复到 DeepSeek Harness
        
        Args:
            task_id: 任务ID
            reply_text: 回复文本
            user_id: 用户ID
            
        Returns:
            bool: 提交是否成功
            
        Raises:
            HarnessConnectionError: 连接失败
            HarnessAPIError: API调用失败
        """
    
    def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 服务是否健康
        """
```

### 2. 任务发现模块 (TaskDiscovery)

```python
class TaskDiscovery:
    """任务发现模块"""
    
    def __init__(self, harness_client: HarnessClient, task_repository: TaskRepository):
        """初始化任务发现模块
        
        Args:
            harness_client: DeepSeek Harness 客户端
            task_repository: 任务仓库
        """
    
    def discover_pending_tasks(self) -> List[Task]:
        """发现待确认任务
        
        从 DeepSeek Harness 获取待确认任务，过滤已处理任务，创建新任务记录
        
        Returns:
            List[Task]: 新发现的任务列表
            
        Raises:
            HarnessConnectionError: 连接失败
            HarnessAPIError: API调用失败
        """
    
    def filter_processed_tasks(self, harness_tasks: List[dict]) -> List[dict]:
        """过滤已处理任务
        
        Args:
            harness_tasks: 从 Harness 获取的任务列表
            
        Returns:
            List[dict]: 未处理的任务列表
        """
```

### 3. 轮询调度器 (PollingScheduler)

```python
class PollingScheduler:
    """轮询调度器"""
    
    def __init__(self, task_discovery: TaskDiscovery, interval_seconds: int = 5):
        """初始化轮询调度器
        
        Args:
            task_discovery: 任务发现模块
            interval_seconds: 轮询间隔（秒）
        """
    
    def start(self):
        """启动轮询"""
    
    def stop(self):
        """停止轮询"""
    
    def poll_once(self) -> List[Task]:
        """执行一次轮询
        
        Returns:
            List[Task]: 新发现的任务列表
        """
```

### 4. 自定义异常

```python
class HarnessConnectionError(Exception):
    """Harness 连接错误"""
    pass

class HarnessAPIError(Exception):
    """Harness API 错误"""
    pass
```

## 数据模型

### 任务状态流转

```
PENDING → SENT → REPLIED → COMPLETED
   ↓        ↓        ↓
   ↓        ↓    TIMEOUT → FAILED
   ↓        ↓
   ↓    FAILED
   ↓
  (新增任务)
```

## 测试方案

### 单元测试

1. **HarnessClient 测试**
   - test_get_pending_tasks_success: 测试获取待确认任务成功
   - test_get_pending_tasks_connection_error: 测试连接失败
   - test_get_pending_tasks_api_error: 测试 API 错误
   - test_submit_reply_success: 测试提交回复成功
   - test_submit_reply_failure: 测试提交回复失败
   - test_health_check_success: 测试健康检查成功
   - test_health_check_failure: 测试健康检查失败

2. **TaskDiscovery 测试**
   - test_discover_pending_tasks_success: 测试发现待确认任务成功
   - test_discover_pending_tasks_no_new: 测试没有新任务
   - test_discover_pending_tasks_connection_error: 测试连接失败
   - test_filter_processed_tasks: 测试过滤已处理任务
   - test_filter_processed_tasks_all_processed: 测试所有任务已处理

3. **PollingScheduler 测试**
   - test_start_stop: 测试启动和停止
   - test_poll_once_success: 测试单次轮询成功
   - test_poll_once_no_tasks: 测试单次轮询无任务

## 依赖关系

- 依赖 `requests` 库进行 HTTP 调用
- 依赖 `APScheduler` 库实现定时任务
- 依赖迭代1的 `TaskRepository` 和 `Config`
