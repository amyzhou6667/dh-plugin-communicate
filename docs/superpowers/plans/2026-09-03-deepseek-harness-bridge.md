# DeepSeek Harness 飞书桥接插件迭代计划

**创建日期**：2026-09-03
**版本**：v1.0
**状态**：规划阶段

## 需求与设计摘要

### 功能目标
实现 DeepSeek Harness 与飞书之间的消息桥接，支持以下核心功能：
1. **任务发现**：从 DeepSeek Harness 获取待确认任务
2. **消息转发**：将确认请求发送到用户手机飞书
3. **回复接收**：接收用户通过飞书的回复
4. **信息回传**：将用户回复传回 DeepSeek Harness
5. **超时处理**：处理用户长时间未回复的情况

### 功能边界
**做什麼**：
- 支持文本回复确认方式
- 支持轮询方式获取待确认任务
- 支持飞书开放平台API集成
- 支持基本超时处理机制
- 提供RESTful API接口

**不做什么**：
- 不修改 DeepSeek Harness 核心代码
- 不支持复杂工作流（仅支持简单确认/回复）
- 不支持文件附件（仅支持文本回复）
- 不支持多用户确认（仅支持单用户确认）
- 不支持企业微信、钉钉等其他平台

### 涉及角色与场景
**主要角色**：
1. **DeepSeek Harness 用户**：在公司内网电脑端处理任务
2. **飞书用户**：通过手机飞书接收确认请求并回复
3. **系统管理员**：部署和维护桥接插件

**核心场景**：
1. 用户在公司内网电脑端通过 DeepSeek Harness 处理任务
2. 当需要用户确认信息时，插件将确认请求转发到用户手机飞书
3. 用户通过飞书回复确认
4. 插件将回复传回公司电脑端的 DeepSeek Harness
5. 用户长时间未回复时，插件发送提醒或标记超时

### 关键接口与数据结构
**核心接口**：
1. **任务发现接口**：从 DeepSeek Harness 获取待确认任务
2. **消息发送接口**：发送确认消息到飞书
3. **回调接收接口**：接收飞书用户回复
4. **回复提交接口**：将用户回复提交给 DeepSeek Harness

**核心数据结构**：
1. **任务对象**：包含任务ID、内容、状态、超时时间等
2. **消息对象**：包含消息ID、内容、发送状态等
3. **用户回复对象**：包含回复内容、用户ID、时间戳等

### 交互/流程要点
**主要流程**：
1. **任务发现流程**：轮询 DeepSeek Harness API → 获取待确认任务 → 过滤已处理任务 → 创建新任务记录
2. **消息发送流程**：格式化任务内容 → 调用飞书API发送消息 → 记录消息ID → 更新任务状态
3. **回复处理流程**：接收飞书回调 → 解析用户回复 → 匹配对应任务 → 更新任务状态 → 调用 DeepSeek Harness API 提交回复
4. **超时处理流程**：检查超时任务 → 发送提醒消息 → 标记任务超时 → 执行超时策略

### 验收与测试范围
**验收标准**：
1. 能够从 DeepSeek Harness 获取待确认任务
2. 能够将确认消息发送到飞书
3. 能够接收飞书用户回复
4. 能够将用户回复提交给 DeepSeek Harness
5. 能够处理超时场景

**测试范围**：
1. 单元测试：各模块独立测试
2. 集成测试：端到端流程测试
3. 异常测试：网络错误、认证错误、超时等场景

## 需同步文档清单
由于是新项目，无现有文档需要同步。需创建以下文档：
1. `docs/PRD/README.md` - 产品需求文档索引
2. `docs/TAD/README.md` - 技术架构文档索引
3. `docs/TEST/README.md` - 测试用例文档索引
4. `docs/api/openapi.yaml` - API接口定义
5. `docs/database/schema.md` - 数据库表结构

## 接口签名契约

### 新增类/接口

#### 1. 任务发现模块 (TaskDiscovery)
```python
class TaskDiscovery:
    def __init__(self, harness_client: HarnessClient, config: Config):
        """初始化任务发现模块
        
        Args:
            harness_client: DeepSeek Harness 客户端
            config: 配置对象
        """
    
    def discover_pending_tasks(self) -> List[Task]:
        """发现待确认任务
        
        Returns:
            List[Task]: 待确认任务列表
        
        Raises:
            HarnessConnectionError: 连接 DeepSeek Harness 失败
            HarnessAPIError: API调用失败
        """
    
    def filter_processed_tasks(self, tasks: List[Task]) -> List[Task]:
        """过滤已处理任务
        
        Args:
            tasks: 原始任务列表
        
        Returns:
            List[Task]: 过滤后的任务列表
        """
```

#### 2. 飞书集成模块 (FeishuIntegration)
```python
class FeishuIntegration:
    def __init__(self, app_id: str, app_secret: str, config: Config):
        """初始化飞书集成模块
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            config: 配置对象
        """
    
    def send_confirmation_message(self, task: Task, user_id: str) -> str:
        """发送确认消息到飞书
        
        Args:
            task: 任务对象
            user_id: 飞书用户ID
        
        Returns:
            str: 飞书消息ID
        
        Raises:
            FeishuAuthError: 飞书认证失败
            FeishuAPIError: 飞书API调用失败
        """
    
    def parse_callback_message(self, callback_data: dict) -> Optional[UserReply]:
        """解析飞书回调消息
        
        Args:
            callback_data: 飞书回调数据
        
        Returns:
            Optional[UserReply]: 用户回复对象，如果解析失败返回None
        """
```

#### 3. 状态管理模块 (StateManager)
```python
class StateManager:
    def __init__(self, db_session: Session):
        """初始化状态管理模块
        
        Args:
            db_session: 数据库会话
        """
    
    def create_task(self, task: Task) -> Task:
        """创建任务记录
        
        Args:
            task: 任务对象
        
        Returns:
            Task: 创建的任务对象
        
        Raises:
            DatabaseError: 数据库操作失败
        """
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
        
        Returns:
            bool: 更新是否成功
        
        Raises:
            TaskNotFoundError: 任务不存在
            DatabaseError: 数据库操作失败
        """
    
    def get_timeout_tasks(self) -> List[Task]:
        """获取超时任务
        
        Returns:
            List[Task]: 超时任务列表
        """
```

#### 4. API网关模块 (APIGateway)
```python
class APIGateway:
    def __init__(self, task_discovery: TaskDiscovery, feishu_integration: FeishuIntegration, state_manager: StateManager):
        """初始化API网关
        
        Args:
            task_discovery: 任务发现模块
            feishu_integration: 飞书集成模块
            state_manager: 状态管理模块
        """
    
    def get_pending_tasks(self) -> List[Task]:
        """获取待确认任务
        
        Returns:
            List[Task]: 待确认任务列表
        """
    
    def submit_user_reply(self, task_id: str, reply_text: str, user_id: str) -> bool:
        """提交用户回复
        
        Args:
            task_id: 任务ID
            reply_text: 回复文本
            user_id: 用户ID
        
        Returns:
            bool: 提交是否成功
        
        Raises:
            TaskNotFoundError: 任务不存在
            InvalidReplyError: 无效回复
        """
    
    def handle_feishu_callback(self, callback_data: dict) -> bool:
        """处理飞书回调
        
        Args:
            callback_data: 飞书回调数据
        
        Returns:
            bool: 处理是否成功
        """
```

### 数据模型

#### 1. 任务实体 (Task)
```python
class Task:
    id: str  # 任务ID，主键
    harness_task_id: str  # DeepSeek Harness 任务ID
    content: str  # 任务内容
    context: dict  # 上下文信息
    status: TaskStatus  # 任务状态
    feishu_message_id: Optional[str]  # 飞书消息ID
    user_reply: Optional[str]  # 用户回复
    user_id: Optional[str]  # 用户ID
    created_at: datetime  # 创建时间
    updated_at: datetime  # 更新时间
    timeout_at: datetime  # 超时时间
    retry_count: int  # 重试次数
```

#### 2. 任务状态枚举 (TaskStatus)
```python
class TaskStatus(Enum):
    PENDING = "pending"  # 待确认
    SENT = "sent"  # 已发送飞书
    REPLIED = "replied"  # 已回复
    COMPLETED = "completed"  # 已完成
    TIMEOUT = "timeout"  # 超时
    FAILED = "failed"  # 失败
```

#### 3. 用户回复实体 (UserReply)
```python
class UserReply:
    task_id: str  # 任务ID
    reply_text: str  # 回复文本
    user_id: str  # 用户ID
    replied_at: datetime  # 回复时间
```

#### 4. 配置实体 (Config)
```python
class Config:
    harness_base_url: str  # DeepSeek Harness 基础URL
    harness_api_key: Optional[str]  # DeepSeek Harness API密钥
    feishu_app_id: str  # 飞书应用ID
    feishu_app_secret: str  # 飞书应用密钥
    feishu_encrypt_key: Optional[str]  # 飞书加密密钥
    feishu_verification_token: Optional[str]  # 飞书验证令牌
    bridge_port: int  # 桥接插件端口
    poll_interval_seconds: int  # 轮询间隔（秒）
    default_timeout_seconds: int  # 默认超时时间（秒）
    max_retry_count: int  # 最大重试次数
    database_url: str  # 数据库连接URL
```

### MyBatis Mapper 方法签名
由于使用 Python/Flask，不使用 MyBatis，改用 SQLAlchemy 或类似ORM。

#### 1. 任务仓库 (TaskRepository)
```python
class TaskRepository:
    def save(self, task: Task) -> Task:
        """保存任务"""
    
    def find_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID查找任务"""
    
    def find_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态查找任务"""
    
    def update_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态"""
    
    def find_timeout_tasks(self) -> List[Task]:
        """查找超时任务"""
```

### SQL 表结构变更
```sql
-- 任务表
CREATE TABLE tasks (
    id VARCHAR(50) PRIMARY KEY,
    harness_task_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    context JSON,
    status ENUM('pending', 'sent', 'replied', 'completed', 'timeout', 'failed') NOT NULL,
    feishu_message_id VARCHAR(100),
    user_reply TEXT,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    timeout_at TIMESTAMP,
    retry_count INT DEFAULT 0,
    INDEX idx_status (status),
    INDEX idx_timeout_at (timeout_at)
);

-- 配置表
CREATE TABLE configs (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description VARCHAR(500),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 迭代计划

### 迭代 1: 基础框架搭建
- **目标**：搭建 Flask 应用框架，实现基本 API 接口和数据库模型
- **涉及范围**：
  - Flask 应用初始化
  - 数据库模型定义
  - 基本 API 接口实现
  - 配置管理
- **接口契约**：
  - `APIGateway.get_pending_tasks()` - 获取待确认任务
  - `APIGateway.submit_user_reply()` - 提交用户回复
  - `TaskRepository` - 任务数据访问层
- **验收标准**：
  1. Flask 应用能够启动并监听指定端口
  2. 能够创建和查询数据库表
  3. API 接口能够返回正确的响应格式
  4. 配置能够正确加载
- **测试方案**：
  - 单元测试：测试各个模块的独立功能
  - 集成测试：测试 API 接口的完整流程
  - 手动验证：使用 curl 或 Postman 测试 API

### 迭代 2: DeepSeek Harness 集成
- **目标**：实现从 DeepSeek Harness 获取待确认任务的功能
- **涉及范围**：
  - DeepSeek Harness 客户端实现
  - 任务发现模块实现
  - 轮询机制实现
- **接口契约**：
  - `TaskDiscovery.discover_pending_tasks()` - 发现待确认任务
  - `TaskDiscovery.filter_processed_tasks()` - 过滤已处理任务
  - `HarnessClient` - DeepSeek Harness 客户端
- **验收标准**：
  1. 能够连接到 DeepSeek Harness
  2. 能够获取待确认任务列表
  3. 能够过滤已处理任务
  4. 轮询机制能够定期执行
- **测试方案**：
  - 单元测试：Mock DeepSeek Harness API，测试任务发现逻辑
  - 集成测试：测试与 DeepSeek Harness 的真实连接
  - 手动验证：查看日志确认任务发现过程

### 迭代 3: 飞书消息发送
- **目标**：实现将确认消息发送到飞书的功能
- **涉及范围**：
  - 飞书 SDK 集成
  - 消息发送功能实现
  - 消息格式化
- **接口契约**：
  - `FeishuIntegration.send_confirmation_message()` - 发送确认消息
  - `FeishuIntegration.parse_callback_message()` - 解析回调消息
- **验收标准**：
  1. 能够获取飞书访问令牌
  2. 能够发送文本消息到飞书
  3. 能够发送卡片消息到飞书
  4. 消息格式正确
- **测试方案**：
  - 单元测试：Mock 飞书 API，测试消息发送逻辑
  - 集成测试：测试与飞书 API 的真实连接
  - 手动验证：在飞书中查看收到的消息

### 迭代 4: 飞书回复接收
- **目标**：实现接收飞书用户回复的功能
- **涉及范围**：
  - 飞书回调接口实现
  - 回复解析功能实现
  - 任务状态更新
- **接口契约**：
  - `APIGateway.handle_feishu_callback()` - 处理飞书回调
  - `FeishuIntegration.parse_callback_message()` - 解析回调消息
  - `StateManager.update_task_status()` - 更新任务状态
- **验收标准**：
  1. 能够接收飞书回调消息
  2. 能够解析用户回复内容
  3. 能够匹配对应任务
  4. 能够更新任务状态
- **测试方案**：
  - 单元测试：Mock 飞书回调数据，测试回复解析逻辑
  - 集成测试：测试完整的回调处理流程
  - 手动验证：在飞书中回复消息，查看系统状态变化

### 迭代 5: DeepSeek Harness 回复提交
- **目标**：实现将用户回复提交给 DeepSeek Harness 的功能
- **涉及范围**：
  - 回复提交功能实现
  - DeepSeek Harness API 集成
  - 错误处理
- **接口契约**：
  - `APIGateway.submit_user_reply()` - 提交用户回复
  - `HarnessClient.submit_reply()` - 提交回复到 DeepSeek Harness
- **验收标准**：
  1. 能够将用户回复提交给 DeepSeek Harness
  2. 能够处理提交成功和失败的情况
  3. 能够更新任务状态为已完成
- **测试方案**：
  - 单元测试：Mock DeepSeek Harness API，测试回复提交逻辑
  - 集成测试：测试与 DeepSeek Harness 的真实连接
  - 手动验证：提交回复后查看 DeepSeek Harness 状态

### 迭代 6: 超时处理机制
- **目标**：实现超时处理机制，处理用户长时间未回复的情况
- **涉及范围**：
  - 超时检测功能实现
  - 超时提醒功能实现
  - 超时策略执行
- **接口契约**：
  - `StateManager.get_timeout_tasks()` - 获取超时任务
  - `StateManager.update_task_status()` - 更新任务状态
  - `FeishuIntegration.send_confirmation_message()` - 发送提醒消息
- **验收标准**：
  1. 能够检测超时任务
  2. 能够发送超时提醒消息
  3. 能够执行超时策略（重试/失败）
  4. 能够更新任务状态
- **测试方案**：
  - 单元测试：测试超时检测和提醒逻辑
  - 集成测试：测试完整的超时处理流程
  - 手动验证：设置短超时时间，查看超时处理效果

### 迭代 7: 错误处理与监控
- **目标**：实现完善的错误处理和监控机制
- **涉及范围**：
  - 错误分类和处理
  - 重试机制实现
  - 日志记录
  - 监控指标
- **接口契约**：
  - 错误处理类：`HarnessConnectionError`, `FeishuAuthError`, `TaskNotFoundError` 等
  - 重试机制：指数退避重试
  - 日志记录：结构化日志
- **验收标准**：
  1. 能够正确分类和处理各种错误
  2. 能够实现重试机制
  3. 能够记录详细的日志
  4. 能够提供监控指标
- **测试方案**：
  - 单元测试：测试各种错误场景的处理
  - 集成测试：测试错误恢复机制
  - 手动验证：模拟错误场景，查看日志和监控

### 迭代 8: 配置管理与部署
- **目标**：实现完善的配置管理和部署方案
- **涉及范围**：
  - 配置管理优化
  - 部署脚本
  - 运维文档
- **接口契约**：
  - 配置管理：环境变量、配置文件
  - 部署脚本：启动、停止、重启
- **验收标准**：
  1. 能够通过环境变量配置系统
  2. 能够通过配置文件配置系统
  3. 提供完整的部署脚本
  4. 提供详细的运维文档
- **测试方案**：
  - 单元测试：测试配置加载逻辑
  - 集成测试：测试部署流程
  - 手动验证：按照文档进行部署测试

## 为子 Agent 提供的清晰接口

### 给 TDD Agent 的接口

#### 迭代 1 接口契约
**目标**：搭建 Flask 应用框架，实现基本 API 接口和数据库模型

**接口签名**：
```python
# APIGateway 类
class APIGateway:
    def get_pending_tasks(self) -> List[Task]:
        """获取待确认任务
        
        Returns:
            List[Task]: 待确认任务列表
        
        Raises:
            HarnessConnectionError: 连接 DeepSeek Harness 失败
            DatabaseError: 数据库操作失败
        """
    
    def submit_user_reply(self, task_id: str, reply_text: str, user_id: str) -> bool:
        """提交用户回复
        
        Args:
            task_id: 任务ID
            reply_text: 回复文本
            user_id: 用户ID
        
        Returns:
            bool: 提交是否成功
        
        Raises:
            TaskNotFoundError: 任务不存在
            InvalidReplyError: 无效回复
            DatabaseError: 数据库操作失败
        """

# TaskRepository 类
class TaskRepository:
    def save(self, task: Task) -> Task:
        """保存任务
        
        Args:
            task: 任务对象
        
        Returns:
            Task: 保存后的任务对象
        
        Raises:
            DatabaseError: 数据库操作失败
        """
    
    def find_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID查找任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            Optional[Task]: 任务对象，如果不存在返回None
        """
```

**验收标准**：
1. Flask 应用能够启动并监听指定端口
2. 能够创建和查询数据库表
3. API 接口能够返回正确的响应格式
4. 配置能够正确加载

**测试方案**：
- 单元测试：测试各个模块的独立功能
- 集成测试：测试 API 接口的完整流程
- 手动验证：使用 curl 或 Postman 测试 API

#### 迭代 2 接口契约
**目标**：实现从 DeepSeek Harness 获取待确认任务的功能

**接口签名**：
```python
# TaskDiscovery 类
class TaskDiscovery:
    def discover_pending_tasks(self) -> List[Task]:
        """发现待确认任务
        
        Returns:
            List[Task]: 待确认任务列表
        
        Raises:
            HarnessConnectionError: 连接 DeepSeek Harness 失败
            HarnessAPIError: API调用失败
        """
    
    def filter_processed_tasks(self, tasks: List[Task]) -> List[Task]:
        """过滤已处理任务
        
        Args:
            tasks: 原始任务列表
        
        Returns:
            List[Task]: 过滤后的任务列表
        """

# HarnessClient 类
class HarnessClient:
    def get_pending_tasks(self) -> List[dict]:
        """从 DeepSeek Harness 获取待确认任务
        
        Returns:
            List[dict]: 原始任务数据列表
        
        Raises:
            HarnessConnectionError: 连接失败
            HarnessAPIError: API调用失败
        """
```

**验收标准**：
1. 能够连接到 DeepSeek Harness
2. 能够获取待确认任务列表
3. 能够过滤已处理任务
4. 轮询机制能够定期执行

**测试方案**：
- 单元测试：Mock DeepSeek Harness API，测试任务发现逻辑
- 集成测试：测试与 DeepSeek Harness 的真实连接
- 手动验证：查看日志确认任务发现过程

### 给代码开发 Agent 的接口

#### 迭代 1 开发指南
**目标**：搭建 Flask 应用框架，实现基本 API 接口和数据库模型

**涉及范围**：
- Flask 应用初始化
- 数据库模型定义
- 基本 API 接口实现
- 配置管理

**接口约束**：
1. API 接口必须遵循 RESTful 设计原则
2. 响应格式必须统一（参考 openapi.yaml）
3. 错误处理必须完善
4. 日志记录必须详细

**数据约束**：
1. 任务状态必须使用预定义的枚举值
2. 时间字段必须使用 ISO 8601 格式
3. 必须实现数据验证

**代码规范**：
1. 遵循 PEP 8 编码规范
2. 添加详细的文档字符串
3. 实现类型注解
4. 编写单元测试

#### 迭代 2 开发指南
**目标**：实现从 DeepSeek Harness 获取待确认任务的功能

**涉及范围**：
- DeepSeek Harness 客户端实现
- 任务发现模块实现
- 轮询机制实现

**接口约束**：
1. 必须实现重试机制
2. 必须处理网络异常
3. 必须记录详细日志
4. 必须支持配置化

**数据约束**：
1. 必须过滤已处理任务
2. 必须处理重复任务
3. 必须验证任务数据完整性

### 给 Review Agent 的接口

#### 模块划分审查
**审查要点**：
1. 模块职责是否单一
2. 模块间耦合度是否合理
3. 接口设计是否清晰
4. 依赖关系是否正确

**审查标准**：
1. 每个模块只负责一个功能
2. 模块间通过接口交互
3. 避免循环依赖
4. 使用依赖注入降低耦合

#### 安全审查
**审查要点**：
1. 输入验证是否完善
2. 认证授权是否正确
3. 敏感数据是否加密
4. 日志记录是否安全

**审查标准**：
1. 所有输入必须验证
2. 关键操作必须认证
3. 敏感信息必须加密
4. 日志不能记录敏感信息

#### 可维护性审查
**审查要点**：
1. 代码是否易于理解
2. 文档是否完善
3. 测试是否充分
4. 配置是否灵活

**审查标准**：
1. 代码结构清晰
2. 注释详细准确
3. 测试覆盖率 > 80%
4. 配置支持环境变量