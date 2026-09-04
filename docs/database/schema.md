# 数据库表结构文档

## 概述
本文档描述 DeepSeek Harness 飞书桥接插件的数据库表结构设计。

## 数据库选型

### 开发环境
- **数据库**：SQLite
- **特点**：轻量级、无需安装、文件存储
- **适用场景**：本地开发、单元测试

### 生产环境
- **数据库**：MySQL 8.0+
- **特点**：高性能、高可用、支持事务
- **适用场景**：生产部署、高并发场景

## 表结构设计

### 1. 任务表 (tasks)

#### 表描述
存储待确认任务信息，跟踪任务状态和超时，记录用户回复。

#### 字段定义

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | VARCHAR(50) | PRIMARY KEY | - | 任务ID，主键 |
| harness_task_id | VARCHAR(100) | NOT NULL | - | DeepSeek Harness 任务ID |
| content | TEXT | NOT NULL | - | 任务内容 |
| context | JSON | - | NULL | 上下文信息 |
| status | ENUM | NOT NULL | 'pending' | 任务状态 |
| feishu_message_id | VARCHAR(100) | - | NULL | 飞书消息ID |
| user_reply | TEXT | - | NULL | 用户回复内容 |
| user_id | VARCHAR(100) | - | NULL | 用户ID |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |
| timeout_at | TIMESTAMP | - | NULL | 超时时间 |
| retry_count | INT | NOT NULL | 0 | 重试次数 |

#### 状态枚举值
- `pending` - 待确认
- `sent` - 已发送飞书
- `replied` - 已回复
- `completed` - 已完成
- `timeout` - 超时
- `failed` - 失败

#### 索引定义

| 索引名 | 字段 | 类型 | 说明 |
|--------|------|------|------|
| PRIMARY | id | 主键 | 主键索引 |
| idx_status | status | 普通索引 | 按状态查询 |
| idx_timeout_at | timeout_at | 普通索引 | 超时任务查询 |
| idx_harness_task_id | harness_task_id | 普通索引 | 按Harness任务ID查询 |
| idx_created_at | created_at | 普通索引 | 按创建时间查询 |

#### 建表语句

```sql
-- MySQL 版本
CREATE TABLE tasks (
    id VARCHAR(50) PRIMARY KEY,
    harness_task_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    context JSON,
    status ENUM('pending', 'sent', 'replied', 'completed', 'timeout', 'failed') NOT NULL DEFAULT 'pending',
    feishu_message_id VARCHAR(100),
    user_reply TEXT,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    timeout_at TIMESTAMP,
    retry_count INT DEFAULT 0,
    INDEX idx_status (status),
    INDEX idx_timeout_at (timeout_at),
    INDEX idx_harness_task_id (harness_task_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- SQLite 版本
CREATE TABLE tasks (
    id VARCHAR(50) PRIMARY KEY,
    harness_task_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    context TEXT,  -- SQLite 使用 TEXT 存储 JSON
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    feishu_message_id VARCHAR(100),
    user_reply TEXT,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    timeout_at TIMESTAMP,
    retry_count INT DEFAULT 0
);

CREATE INDEX idx_status ON tasks(status);
CREATE INDEX idx_timeout_at ON tasks(timeout_at);
CREATE INDEX idx_harness_task_id ON tasks(harness_task_id);
CREATE INDEX idx_created_at ON tasks(created_at);
```

#### 数据示例

```json
{
    "id": "task_123",
    "harness_task_id": "harness_456",
    "content": "请确认以下操作：删除用户数据",
    "context": {
        "user_id": "user_789",
        "action": "delete_user_data"
    },
    "status": "pending",
    "feishu_message_id": null,
    "user_reply": null,
    "user_id": null,
    "created_at": "2026-09-03T10:00:00Z",
    "updated_at": "2026-09-03T10:00:00Z",
    "timeout_at": "2026-09-03T10:05:00Z",
    "retry_count": 0
}
```

### 2. 配置表 (configs)

#### 表描述
存储系统配置信息，支持动态配置更新。

#### 字段定义

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| key | VARCHAR(100) | PRIMARY KEY | - | 配置键，主键 |
| value | TEXT | NOT NULL | - | 配置值 |
| description | VARCHAR(500) | - | NULL | 配置说明 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

#### 索引定义

| 索引名 | 字段 | 类型 | 说明 |
|--------|------|------|------|
| PRIMARY | key | 主键 | 主键索引 |

#### 建表语句

```sql
-- MySQL 版本
CREATE TABLE configs (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description VARCHAR(500),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- SQLite 版本
CREATE TABLE configs (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description VARCHAR(500),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 配置项示例

| key | value | description |
|-----|-------|-------------|
| poll_interval_seconds | 5 | 轮询间隔（秒） |
| default_timeout_seconds | 300 | 默认超时时间（秒） |
| max_retry_count | 3 | 最大重试次数 |
| feishu_app_id | cli_xxx | 飞书应用ID |
| feishu_app_secret | xxx | 飞书应用密钥 |
| harness_base_url | http://127.0.0.1:3080 | DeepSeek Harness 基础URL |

## 数据关系

### 任务状态流转
```
待确认 (pending)
    ↓
已发送飞书 (sent)
    ↓
已回复 (replied)
    ↓
已完成 (completed)

已发送飞书 (sent)
    ↓
超时 (timeout)
    ↓
重新发送 / 标记失败 (failed)
```

### 表关系
- 任务表 (tasks) 是核心表，存储所有任务信息
- 配置表 (configs) 存储系统配置，与任务表无直接关系
- 任务表通过 harness_task_id 与 DeepSeek Harness 关联
- 任务表通过 feishu_message_id 与飞书消息关联

## 数据完整性

### 约束定义
1. **主键约束**：每个表都有主键
2. **非空约束**：关键字段不允许为空
3. **唯一约束**：配置键唯一
4. **外键约束**：暂不使用外键，通过应用层保证数据一致性

### 数据校验
1. **状态校验**：任务状态必须是预定义的枚举值
2. **时间校验**：超时时间必须大于创建时间
3. **重试次数校验**：重试次数不能超过最大重试次数

## 数据迁移

### 迁移策略
1. **版本控制**：使用 Flyway 或类似工具管理数据库版本
2. **向前兼容**：新版本必须兼容旧版本数据
3. **回滚支持**：每个迁移都有对应的回滚脚本

### 迁移脚本示例

```sql
-- V1__create_tasks_table.sql
CREATE TABLE tasks (
    id VARCHAR(50) PRIMARY KEY,
    harness_task_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    context JSON,
    status ENUM('pending', 'sent', 'replied', 'completed', 'timeout', 'failed') NOT NULL DEFAULT 'pending',
    feishu_message_id VARCHAR(100),
    user_reply TEXT,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    timeout_at TIMESTAMP,
    retry_count INT DEFAULT 0,
    INDEX idx_status (status),
    INDEX idx_timeout_at (timeout_at),
    INDEX idx_harness_task_id (harness_task_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- V2__create_configs_table.sql
CREATE TABLE configs (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description VARCHAR(500),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## 性能优化

### 索引优化
1. **查询优化**：为常用查询字段创建索引
2. **复合索引**：为多字段查询创建复合索引
3. **索引维护**：定期分析索引使用情况，删除无用索引

### 查询优化
1. **分页查询**：使用 LIMIT 和 OFFSET 进行分页
2. **批量操作**：使用批量插入和更新
3. **连接池**：使用数据库连接池

### 存储优化
1. **数据归档**：定期归档历史数据
2. **表分区**：按时间对大表进行分区
3. **压缩存储**：对大文本字段进行压缩

## 备份与恢复

### 备份策略
1. **全量备份**：每日进行全量备份
2. **增量备份**：每小时进行增量备份
3. **日志备份**：实时备份数据库日志

### 恢复策略
1. **时间点恢复**：支持恢复到任意时间点
2. **测试恢复**：定期进行恢复测试
3. **文档记录**：记录恢复步骤和注意事项

## 监控与告警

### 监控指标
1. **连接数**：监控数据库连接数
2. **查询性能**：监控慢查询
3. **存储空间**：监控数据库存储空间
4. **锁等待**：监控锁等待情况

### 告警规则
1. **连接数过高**：连接数超过阈值时告警
2. **慢查询过多**：慢查询数量超过阈值时告警
3. **存储空间不足**：存储空间低于阈值时告警
4. **主从延迟**：主从延迟超过阈值时告警

## 安全考虑

### 访问控制
1. **用户权限**：最小权限原则
2. **网络访问**：限制数据库访问IP
3. **认证机制**：使用强密码和认证

### 数据安全
1. **加密存储**：敏感数据加密存储
2. **传输加密**：使用SSL/TLS加密传输
3. **审计日志**：记录数据库操作日志

## 相关文档
- [技术架构文档](../TAD/README.md)
- [产品需求文档](../PRD/README.md)
- [迭代计划](../superpowers/plans/2026-09-03-deepseek-harness-bridge.md)