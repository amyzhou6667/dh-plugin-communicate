# DeepSeek Harness 飞书桥接插件技术设计文档

**创建日期**：2026-09-03
**版本**：v1.0
**状态**：设计阶段

## 1. 概述

### 1.1 项目背景
用户在公司内网电脑端通过 DeepSeek Harness (http://127.0.0.1:3080/) 处理任务，当需要用户确认信息时，需要将确认请求转发到用户手机飞书，用户通过飞书回复后，信息能传回公司电脑端继续任务。

### 1.2 核心目标
- 实现 DeepSeek Harness 与飞书之间的消息桥接
- 支持文本回复确认方式
- 支持超时处理机制
- 部署在公司内网，与 DeepSeek Harness 同机器

### 1.3 技术栈
- **后端**：Python/Flask
- **飞书集成**：飞书开放平台API
- **部署**：本地部署 (127.0.0.1:5000)

## 2. 架构设计

### 2.1 系统架构图
```
公司内网电脑 (127.0.0.1)
├── DeepSeek Harness (端口3080)
│   └── 任务处理引擎
└── 桥接插件 (端口5000)
    ├── 任务发现模块
    │   ├── 轮询适配器 (默认)
    │   ├── Webhook适配器 (备选)
    │   └── 文件监听适配器 (备选)
    ├── 飞书集成模块
    │   ├── 消息发送器
    │   ├── 回调接收器
    │   └── 消息格式化器
    ├── 状态管理模块
    │   ├── 任务状态跟踪
    │   ├── 超时处理器
    │   └── 持久化存储
    └── API网关
        ├── 内部API (供DeepSeek Harness调用)
        └── 外部API (供飞书回调)
```

### 2.2 组件说明

#### 2.2.1 任务发现模块
负责从 DeepSeek Harness 获取待确认任务。

**适配器模式设计**：
- **轮询适配器**：定期查询 DeepSeek Harness API（默认方案）
- **Webhook适配器**：接收 DeepSeek Harness 的回调通知
- **文件监听适配器**：监听本地文件变化（备用方案）

#### 2.2.2 飞书集成模块
负责与飞书平台的消息收发。

**核心功能**：
- 发送确认消息到飞书（支持文本、卡片消息）
- 接收飞书用户回复（通过回调）
- 消息格式转换

#### 2.2.3 状态管理模块
管理任务状态和超时处理。

**状态流转**：
```
待确认 → 已发送飞书 → 已回复 → 已回传
                 ↓
              超时处理 → 重新发送/标记失败
```

#### 2.2.4 API网关
提供内部和外部API接口。

## 3. 接口设计

### 3.1 内部API (供DeepSeek Harness调用)

#### 3.1.1 获取待确认任务
```http
GET /api/tasks/pending
Response: {
  "tasks": [
    {
      "id": "task_123",
      "content": "请确认以下操作：...",
      "context": {...},
      "created_at": "2026-09-03T10:00:00Z",
      "timeout_seconds": 300
    }
  ]
}
```

#### 3.1.2 提交用户回复
```http
POST /api/tasks/{task_id}/reply
Request: {
  "reply_text": "确认执行",
  "user_id": "user_456"
}
Response: {
  "success": true,
  "message": "回复已接收"
}
```

### 3.2 外部API (供飞书回调)

#### 3.2.1 飞书消息回调
```http
POST /webhook/feishu
Request: {
  "event": {
    "message": {
      "content": "确认执行",
      "message_type": "text",
      "open_id": "ou_xxx"
    }
  }
}
Response: {
  "success": true
}
```

### 3.3 飞书开放平台API调用

#### 3.3.1 发送确认消息
```http
POST https://open.feishu.cn/open-apis/im/v1/messages
Headers: {
  "Authorization": "Bearer {tenant_access_token}",
  "Content-Type": "application/json"
}
Request: {
  "receive_id": "ou_xxx",
  "msg_type": "interactive",
  "content": {
    "type": "template",
    "data": {
      "template_id": "template_123",
      "template_variable": {
        "task_content": "请确认以下操作：...",
        "task_id": "task_123"
      }
    }
  }
}
```

## 4. 数据模型

### 4.1 任务表 (tasks)
```sql
CREATE TABLE tasks (
  id VARCHAR(50) PRIMARY KEY,
  harness_task_id VARCHAR(100) NOT NULL,
  content TEXT NOT NULL,
  context JSON,
  status ENUM('pending', 'sent', 'replied', 'completed', 'timeout', 'failed'),
  feishu_message_id VARCHAR(100),
  user_reply TEXT,
  user_id VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  timeout_at TIMESTAMP,
  retry_count INT DEFAULT 0
);
```

### 4.2 配置表 (configs)
```sql
CREATE TABLE configs (
  key VARCHAR(100) PRIMARY KEY,
  value TEXT NOT NULL,
  description VARCHAR(500),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 5. 核心流程

### 5.1 任务发现流程
1. 轮询适配器定期查询 DeepSeek Harness API
2. 获取待确认任务列表
3. 过滤已处理任务
4. 创建新任务记录

### 5.2 消息发送流程
1. 格式化任务内容为飞书消息
2. 调用飞书API发送消息
3. 记录飞书消息ID
4. 更新任务状态为"已发送"

### 5.3 回复处理流程
1. 接收飞书回调消息
2. 解析用户回复内容
3. 匹配对应任务
4. 更新任务状态和用户回复
5. 调用 DeepSeek Harness API 提交回复

### 5.4 超时处理流程
1. 检查超时任务
2. 发送提醒消息（可选）
3. 标记任务超时
4. 执行超时策略（重试/失败）

## 6. 配置管理

### 6.1 环境变量配置
```python
# DeepSeek Harness 配置
HARNESS_BASE_URL = "http://127.0.0.1:3080"
HARNESS_API_KEY = ""  # 如果需要认证

# 飞书配置
FEISHU_APP_ID = "cli_xxx"
FEISHU_APP_SECRET = "xxx"
FEISHU_ENCRYPT_KEY = "xxx"
FEISHU_VERIFICATION_TOKEN = "xxx"

# 插件配置
BRIDGE_PORT = 5000
POLL_INTERVAL_SECONDS = 5
DEFAULT_TIMEOUT_SECONDS = 300
MAX_RETRY_COUNT = 3
```

### 6.2 数据库配置
```python
DATABASE_URL = "sqlite:///bridge.db"  # 本地SQLite
# 或
DATABASE_URL = "mysql://user:pass@localhost/bridge_db"
```

## 7. 错误处理与监控

### 7.1 错误分类
- **网络错误**：DeepSeek Harness 或飞书API不可用
- **认证错误**：飞书token过期或无效
- **数据错误**：消息格式错误或任务状态异常
- **超时错误**：用户长时间未回复

### 7.2 重试策略
- 网络错误：指数退避重试，最多3次
- 认证错误：自动刷新token
- 超时错误：根据配置执行超时策略

### 7.3 日志与监控
- 结构化日志记录
- 关键指标监控（消息发送成功率、回复率、超时率）
- 异常告警

## 8. 安全考虑

### 8.1 网络安全
- 插件仅监听本地端口 (127.0.0.1)
- 飞书回调使用HTTPS（生产环境）
- API接口添加认证

### 8.2 数据安全
- 敏感信息加密存储
- 定期清理过期数据
- 访问日志记录

### 8.3 访问控制
- 飞书应用权限最小化
- 用户身份验证
- 操作权限控制

## 9. 部署与运维

### 9.1 部署步骤
1. 安装Python依赖
2. 配置环境变量
3. 初始化数据库
4. 启动插件服务
5. 配置飞书应用回调地址

### 9.2 运维建议
- 使用进程管理器（如systemd）
- 配置日志轮转
- 定期备份数据库
- 监控服务状态

## 10. 扩展性考虑

### 10.1 适配器扩展
- 支持多种任务发现机制
- 支持多种消息平台（企业微信、钉钉等）
- 支持多种确认方式

### 10.2 功能扩展
- 支持富文本消息
- 支持文件附件
- 支持多用户确认
- 支持确认工作流

## 11. 风险评估

### 11.1 技术风险
- DeepSeek Harness API不可用：降级为文件监听
- 飞书API限流：实现请求队列和退避策略
- 网络不稳定：增加重试机制

### 11.2 业务风险
- 用户回复延迟：设置合理超时时间
- 消息丢失：实现消息持久化和确认机制
- 误操作：添加确认步骤和撤销功能

## 12. 实现计划

### 12.1 第一阶段：基础框架
1. 搭建Flask应用框架
2. 实现基本API接口
3. 集成飞书SDK
4. 实现轮询适配器

### 12.2 第二阶段：核心功能
1. 实现消息发送和接收
2. 实现状态管理
3. 实现超时处理
4. 添加错误处理

### 12.3 第三阶段：完善优化
1. 添加配置管理
2. 实现日志和监控
3. 优化性能
4. 编写文档

## 13. 测试策略

### 13.1 单元测试
- 各模块独立测试
- Mock外部依赖

### 13.2 集成测试
- 端到端流程测试
- 异常场景测试

### 13.3 性能测试
- 并发处理能力
- 响应时间测试

## 14. 文档与培训

### 14.1 技术文档
- API接口文档
- 部署运维文档
- 故障排查指南

### 14.2 用户文档
- 使用说明
- 常见问题解答
- 操作演示

## 15. 后续优化

### 15.1 功能优化
- 支持更多消息类型
- 实现智能提醒
- 添加数据分析

### 15.2 性能优化
- 缓存机制
- 异步处理
- 连接池优化

### 15.3 运维优化
- 自动化部署
- 监控告警
- 日志分析