# 技术架构文档 (TAD)

## 概述
本目录包含 DeepSeek Harness 飞书桥接插件的技术架构文档。

## 文档结构

### 架构设计
- [系统架构概览](./2026-09-03-system-architecture.md) - 整体架构设计和组件关系
- [模块设计](./2026-09-03-module-design.md) - 各模块详细设计
- [数据流设计](./2026-09-03-data-flow.md) - 数据流转和处理流程

### 接口设计
- [API接口设计](./2026-09-03-api-design.md) - RESTful API 接口定义
- [飞书集成设计](./2026-09-03-feishu-integration.md) - 飞书开放平台API集成
- [DeepSeek Harness集成](./2026-09-03-harness-integration.md) - DeepSeek Harness API集成

### 数据设计
- [数据库设计](./2026-09-03-database-design.md) - 数据库表结构和索引
- [数据模型设计](./2026-09-03-data-model.md) - 实体类和数据模型

### 部署架构
- [部署架构](./2026-09-03-deployment-architecture.md) - 部署拓扑和配置
- [网络架构](./2026-09-03-network-architecture.md) - 网络拓扑和安全

## 技术栈

### 后端技术
- **编程语言**：Python 3.9+
- **Web框架**：Flask 2.0+
- **数据库**：SQLite (开发) / MySQL (生产)
- **ORM**：SQLAlchemy
- **任务调度**：APScheduler

### 飞书集成
- **SDK**：飞书开放平台SDK
- **认证**：OAuth 2.0
- **消息格式**：JSON

### DeepSeek Harness 集成
- **通信协议**：HTTP/HTTPS
- **数据格式**：JSON
- **认证方式**：API Key (可选)

## 架构原则

### 1. 松耦合设计
- 模块间通过接口交互
- 适配器模式支持多种实现
- 依赖注入降低耦合度

### 2. 可扩展性
- 支持多种任务发现机制
- 支持多种消息平台
- 支持多种确认方式

### 3. 可靠性
- 完善的错误处理机制
- 重试和降级策略
- 持久化存储保证数据不丢失

### 4. 安全性
- 本地监听，不暴露到外网
- 认证和授权机制
- 敏感信息加密存储

## 模块划分

### 1. 任务发现模块 (TaskDiscovery)
**职责**：从 DeepSeek Harness 获取待确认任务
**组件**：
- 轮询适配器 (默认)
- Webhook适配器 (备选)
- 文件监听适配器 (备选)

### 2. 飞书集成模块 (FeishuIntegration)
**职责**：与飞书平台的消息收发
**组件**：
- 消息发送器
- 回调接收器
- 消息格式化器

### 3. 状态管理模块 (StateManager)
**职责**：管理任务状态和超时处理
**组件**：
- 任务状态跟踪
- 超时处理器
- 持久化存储

### 4. API网关模块 (APIGateway)
**职责**：提供内部和外部API接口
**组件**：
- 内部API (供DeepSeek Harness调用)
- 外部API (供飞书回调)

## 数据流设计

### 1. 任务发现流程
```
DeepSeek Harness → 轮询适配器 → 任务发现模块 → 状态管理模块 → 数据库
```

### 2. 消息发送流程
```
状态管理模块 → 飞书集成模块 → 飞书API → 用户手机
```

### 3. 回复接收流程
```
用户手机 → 飞书API → 飞书集成模块 → 状态管理模块 → DeepSeek Harness
```

### 4. 超时处理流程
```
定时器 → 状态管理模块 → 飞书集成模块 → 飞书API → 用户手机
```

## 接口设计

### 1. 内部API (供DeepSeek Harness调用)
- `GET /api/tasks/pending` - 获取待确认任务
- `POST /api/tasks/{task_id}/reply` - 提交用户回复

### 2. 外部API (供飞书回调)
- `POST /webhook/feishu` - 飞书消息回调

### 3. 飞书开放平台API
- `POST /open-apis/im/v1/messages` - 发送消息
- `GET /open-apis/auth/v3/tenant_access_token/internal` - 获取访问令牌

## 数据库设计

### 1. 任务表 (tasks)
- 存储待确认任务信息
- 跟踪任务状态和超时
- 记录用户回复

### 2. 配置表 (configs)
- 存储系统配置
- 支持动态配置更新

## 安全设计

### 1. 网络安全
- 仅监听本地端口 (127.0.0.1)
- 飞书回调使用HTTPS
- API接口添加认证

### 2. 数据安全
- 敏感信息加密存储
- 定期清理过期数据
- 访问日志记录

### 3. 访问控制
- 飞书应用权限最小化
- 用户身份验证
- 操作权限控制

## 部署架构

### 1. 开发环境
- 本地开发机器
- SQLite数据库
- Mock外部服务

### 2. 测试环境
- 测试服务器
- MySQL数据库
- 真实外部服务

### 3. 生产环境
- 生产服务器
- MySQL数据库
- 真实外部服务
- 监控和告警

## 相关文档
- [产品需求文档](../PRD/README.md)
- [测试用例文档](../TEST/README.md)
- [迭代计划](../superpowers/plans/2026-09-03-deepseek-harness-bridge.md)
- [技术设计文档](../superpowers/specs/2026-09-03-deepseek-harness-bridge-design.md)