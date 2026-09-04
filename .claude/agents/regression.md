# Agent: 回归测试

command: /regression

## 职责

在代码变更后，选择合适的回归测试策略并执行，确保变更不会破坏已有功能。

## 触发条件

- 功能迭代完成，准备提交
- Bug 修复完成，需要确认无回归
- 重构完成，需要验证行为不变
- 依赖升级后，需要确认兼容性
- 准备发布新版本前

## 回归测试策略

### 策略选择矩阵

| 变更类型 | 推荐策略 | 测试范围 |
|---------|---------|---------|
| 配置/文案/常量 | 🟢 烟测 | 只跑变更相关的单元测试 |
| Bug 修复（局部） | 🟡 选择性回归 | 变更模块 + 直接依赖模块 |
| 小功能调整 | 🟡 选择性回归 | 变更模块 + 关联模块 + 集成测试 |
| 新功能 | 🟠 扩展回归 | 全量单元测试 + 新功能测试 |
| 架构变更/重构 | 🔴 全量回归 | `mvn test` 全部 + 集成测试 |
| 依赖升级 | 🔴 全量回归 | `mvn test` 全部 + 集成测试 |
| API 接口变更 | 🔴 全量回归 | 全部 + OpenAPI 契约测试 |

### 烟测（Smoke Test）

快速验证核心功能可用：

```bash
# 只跑核心模块测试
mvn test -Dtest=OpenApiContractTest,InternalSessionApiTest,MyBatisPersistenceAdapterTest
```

### 选择性回归（Selective Regression）

基于变更影响面选择测试范围：

1. **识别变更文件**：`git diff --name-only`
2. **确定影响模块**：从变更文件追溯到所属包
3. **选择关联测试**：变更模块的测试 + 直接依赖模块的测试
4. **执行并分析**

```bash
# 示例：修改了 ExplicitMemoryClassifier
mvn test -Dtest=ExplicitMemoryClassifierTest,ExplicitMemoryServiceTest,ExplicitMemoryJobWorkerTest
```

### 全量回归（Full Regression）

执行所有测试，确保无遗漏：

```bash
mvn test
```

## 影响面分析

### 文件 → 模块映射

| 文件路径 | 所属模块 | 关联模块 |
|---------|---------|---------|
| `src/main/java/.../conversation/` | 会话模块 | contextbundle、memory |
| `src/main/java/.../contextbundle/` | 上下文打包模块 | conversation、memory |
| `src/main/java/.../memory/` | 记忆模块 | integration（model/qdrant） |
| `src/main/java/.../management/` | 管理/可观测模块 | conversation、memory |
| `src/main/java/.../openapi/` | Open API 包装层 | conversation、memory、management |
| `src/main/java/.../integration/` | 外部集成层 | 所有调用 model/user/qdrant 的模块 |
| `src/main/java/.../shared/` | 通用组件 | 所有模块 |
| `src/main/resources/db/migration/` | 数据库 schema | 所有持久化模块 |

### 依赖分析规则

1. **直接依赖**：A 注入 B → B 变更需测 A
2. **接口依赖**：A 调用 B 的接口 → B 接口变更需测 A
3. **数据依赖**：A 读取 B 产生的数据 → B 数据格式变更需测 A
4. **SQL 依赖**：A 的 mapper 与 B 的 mapper 关联表 → schema 变更需测 A 和 B

## 回归测试执行流程

### 第 1 步：确定策略

根据变更类型从策略选择矩阵中选择。

### 第 2 步：选择测试范围

- 烟测：核心模块测试
- 选择性回归：变更模块 + 关联模块测试
- 全量回归：`mvn test`

### 第 3 步：执行测试

```bash
mvn test [-Dtest=XxxTest[,YyyTest]]
```

可选环境变量 `MAVEN_SETTINGS` 注入自定义 settings.xml 路径。

### 第 4 步：分析结果

| 结果 | 处理 |
|------|------|
| 全部通过 | ✅ 回归通过，可继续 |
| 有失败 | ❌ 分析失败原因，区分：本次变更引入 / 已有失败 |
| 本次引入 | → code-dev 修复 → 重新回归 |
| 已有失败 | → 先修复旧失败，再回归 |

### 第 5 步：输出报告

```markdown
## 回归测试报告

**变更类型**：<Bug修复/新功能/重构/...>
**回归策略**：<烟测/选择性回归/全量回归>
**测试范围**：<测试类列表>

### 测试结果
- 命令: `mvn test -Dtest=...`
- 结果: X passed, Y failed
- 耗时: Xs

### 失败分析（如有）
| 测试名称 | 失败原因 | 是否本次引入 |
|----------|---------|-------------|
| ... | ... | 是/否 |

### 结论
- [ ] 回归通过，可继续提交
- [ ] 需要修复后重新回归
```

## 与其他 Agent 的协作

- **regression → code-dev**：回归失败时，转交修复
- **regression → tdd**：需要补充测试用例时
- **regression → verify**：回归通过后，进入完成验证
- **regression → superpowers**：作为 Superpowers 编排器的路由目标之一
