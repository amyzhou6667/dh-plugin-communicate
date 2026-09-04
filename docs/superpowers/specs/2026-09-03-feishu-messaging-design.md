# 迭代3：飞书消息发送技术设计

**创建日期**：2026-09-03
**版本**：v1.0
**状态**：设计阶段

## 功能目标

实现将确认消息发送到飞书的功能，包括：
1. 飞书开放平台 API 集成
2. 获取访问令牌（tenant_access_token）
3. 发送文本消息
4. 发送卡片消息（交互式消息）

## 飞书开放平台 API

### 1. 获取访问令牌

**请求**：
```
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
Content-Type: application/json

{
  "app_id": "cli_xxx",
  "app_secret": "xxx"
}
```

**响应**：
```json
{
  "code": 0,
  "msg": "ok",
  "tenant_access_token": "t-xxx",
  "expire": 7200
}
```

### 2. 发送消息

**请求**：
```
POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id
Authorization: Bearer t-xxx
Content-Type: application/json

{
  "receive_id": "ou_xxx",
  "msg_type": "text",
  "content": "{\"text\":\"请确认操作\"}"
}
```

**响应**：
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "message_id": "om_xxx",
    "msg_type": "text"
  }
}
```

### 3. 发送卡片消息

**请求**：
```
POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id
Authorization: Bearer t-xxx
Content-Type: application/json

{
  "receive_id": "ou_xxx",
  "msg_type": "interactive",
  "content": "{\"config\":{\"wide_screen_mode\":true},\"header\":{\"title\":{\"tag\":\"plain_text\",\"content\":\"确认请求\"}},\"elements\":[{\"tag\":\"div\",\"text\":{\"tag\":\"lark_md\",\"content\":\"请确认以下操作\"}},{\"tag\":\"action\",\"actions\":[{\"tag\":\"button\",\"text\":{\"tag\":\"plain_text\",\"content\":\"确认\"},\"type\":\"primary\",\"value\":{\"action\":\"confirm\"}},{\"tag\":\"button\",\"text\":{\"tag\":\"plain_text\",\"content\":\"取消\"},\"type\":\"danger\",\"value\":{\"action\":\"cancel\"}}]}]}"
}
```

## 接口签名契约

### 1. 飞书客户端 (FeishuClient)

```python
class FeishuClient:
    """飞书开放平台客户端"""

    def __init__(self, app_id: str, app_secret: str):
        """初始化飞书客户端

        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
        """

    def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token

        Returns:
            str: 访问令牌

        Raises:
            FeishuAuthError: 认证失败
        """

    def send_text_message(self, open_id: str, text: str) -> str:
        """发送文本消息

        Args:
            open_id: 接收者的 open_id
            text: 消息文本

        Returns:
            str: 消息ID

        Raises:
            FeishuAuthError: 认证失败
            FeishuAPIError: API调用失败
        """

    def send_card_message(self, open_id: str, card: dict) -> str:
        """发送卡片消息

        Args:
            open_id: 接收者的 open_id
            card: 卡片内容

        Returns:
            str: 消息ID

        Raises:
            FeishuAuthError: 认证失败
            FeishuAPIError: API调用失败
        """
```

### 2. 飞书消息格式化器 (FeishuMessageFormatter)

```python
class FeishuMessageFormatter:
    """飞书消息格式化器"""

    @staticmethod
    def format_confirmation_card(task_id: str, content: str, context: dict = None) -> dict:
        """格式化确认卡片

        Args:
            task_id: 任务ID
            content: 任务内容
            context: 上下文信息

        Returns:
            dict: 卡片内容
        """

    @staticmethod
    def format_text_message(content: str) -> str:
        """格式化文本消息

        Args:
            content: 消息内容

        Returns:
            str: 格式化后的文本
        """
```

### 3. 自定义异常

```python
class FeishuAuthError(Exception):
    """飞书认证错误"""
    pass

class FeishuAPIError(Exception):
    """飞书 API 错误"""
    pass
```

## 测试方案

### 单元测试

1. **FeishuClient 测试**
   - test_get_tenant_access_token_success: 测试获取令牌成功
   - test_get_tenant_access_token_failure: 测试获取令牌失败
   - test_send_text_message_success: 测试发送文本消息成功
   - test_send_text_message_failure: 测试发送文本消息失败
   - test_send_card_message_success: 测试发送卡片消息成功
   - test_send_card_message_failure: 测试发送卡片消息失败

2. **FeishuMessageFormatter 测试**
   - test_format_confirmation_card: 测试格式化确认卡片
   - test_format_text_message: 测试格式化文本消息

## 依赖关系

- 依赖 `requests` 库进行 HTTP 调用
- 依赖迭代1的 `Config` 获取飞书配置
