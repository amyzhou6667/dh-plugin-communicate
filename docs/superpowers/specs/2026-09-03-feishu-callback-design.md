# 迭代4：飞书回复接收技术设计

**创建日期**：2026-09-03
**版本**：v1.0
**状态**：设计阶段

## 功能目标

实现接收飞书用户回复的功能，包括：
1. 飞书回调接口实现
2. 回复解析功能实现
3. 任务状态更新
4. 回调签名验证

## 飞书回调机制

### 回调数据格式

飞书事件订阅回调数据格式：
```json
{
  "schema": "2.0",
  "header": {
    "event_id": "xxx",
    "event_type": "im.message.receive_v1",
    "create_time": "1234567890",
    "token": "xxx",
    "app_id": "cli_xxx",
    "tenant_key": "xxx"
  },
  "event": {
    "sender": {
      "sender_id": {
        "union_id": "on_xxx",
        "user_id": "xxx",
        "open_id": "ou_xxx"
      },
      "sender_type": "user",
      "tenant_key": "xxx"
    },
    "message": {
      "message_id": "om_xxx",
      "root_id": "",
      "parent_id": "",
      "create_time": "1234567890",
      "chat_id": "oc_xxx",
      "chat_type": "p2p",
      "message_type": "text",
      "content": "{\"text\":\"确认执行\"}",
      "mentions": []
    }
  }
}
```

### 签名验证

飞书回调签名验证：
```
timestamp + nonce + encrypt_key + body = sha256
```

## 接口签名契约

### 1. 飞书回调解析器 (FeishuCallbackParser)

```python
class FeishuCallbackParser:
    """飞书回调解析器"""

    def __init__(self, encrypt_key: Optional[str] = None, verification_token: Optional[str] = None):
        """初始化回调解析器

        Args:
            encrypt_key: 加密密钥（可选）
            verification_token: 验证令牌（可选）
        """

    def parse_message_event(self, callback_data: dict) -> Optional[FeishuMessageEvent]:
        """解析消息事件

        Args:
            callback_data: 飞书回调数据

        Returns:
            Optional[FeishuMessageEvent]: 消息事件对象，解析失败返回None
        """

    def verify_signature(self, timestamp: str, nonce: str, body: str, signature: str) -> bool:
        """验证回调签名

        Args:
            timestamp: 时间戳
            nonce: 随机数
            body: 请求体
            signature: 签名

        Returns:
            bool: 签名是否有效
        """

    def extract_task_id_from_message(self, message_content: str) -> Optional[str]:
        """从消息内容中提取任务ID

        Args:
            message_content: 消息内容

        Returns:
            Optional[str]: 任务ID，提取失败返回None
        """
```

### 2. 消息事件对象 (FeishuMessageEvent)

```python
class FeishuMessageEvent:
    """飞书消息事件"""

    def __init__(self, message_id: str, chat_id: str, chat_type: str,
                 message_type: str, content: str, sender_open_id: str,
                 create_time: str):
        """初始化消息事件"""
        self.message_id = message_id
        self.chat_id = chat_id
        self.chat_type = chat_type
        self.message_type = message_type
        self.content = content
        self.sender_open_id = sender_open_id
        self.create_time = create_time
```

### 3. 回调处理器 (CallbackHandler)

```python
class CallbackHandler:
    """回调处理器"""

    def __init__(self, callback_parser: FeishuCallbackParser,
                 task_repository: TaskRepository,
                 harness_client: HarnessClient):
        """初始化回调处理器"""

    def handle_message_callback(self, callback_data: dict) -> CallbackResult:
        """处理消息回调

        Args:
            callback_data: 飞书回调数据

        Returns:
            CallbackResult: 处理结果
        """

    def match_task_by_message(self, message_content: str) -> Optional[Task]:
        """根据消息匹配任务

        Args:
            message_content: 消息内容

        Returns:
            Optional[Task]: 匹配的任务，未找到返回None
        """
```

### 4. 自定义类型

```python
class CallbackResult:
    """回调处理结果"""

    def __init__(self, success: bool, message: str, task_id: Optional[str] = None):
        self.success = success
        self.message = message
        self.task_id = task_id

class CallbackParseError(Exception):
    """回调解析错误"""
    pass
```

## 测试方案

### 单元测试

1. **FeishuCallbackParser 测试**
   - test_parse_message_event_success: 测试解析消息事件成功
   - test_parse_message_event_invalid: 测试解析无效数据
   - test_verify_signature_success: 测试签名验证成功
   - test_verify_signature_failure: 测试签名验证失败
   - test_extract_task_id_from_message: 测试提取任务ID

2. **CallbackHandler 测试**
   - test_handle_message_callback_success: 测试处理消息回调成功
   - test_handle_message_callback_task_not_found: 测试任务未找到
   - test_handle_message_callback_invalid_data: 测试无效数据
   - test_match_task_by_message: 测试匹配任务

## 依赖关系

- 依赖迭代1的 `TaskRepository` 和 `Task` 模型
- 依赖迭代2的 `HarnessClient`
- 依赖 `hashlib` 进行签名验证
