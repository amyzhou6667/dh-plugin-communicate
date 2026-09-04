按 TDD 优先流程执行 Bug 修复。

**Bug 描述**：$ARGUMENTS

## 通道选择（开始前先判断，标注在第一行）

| 通道 | 满足条件（任一即可） | 跳过 | 预期耗时 |
|------|-------------------|------|---------|
| **🚀 快速修复** | 根因已明确 + 改动 ≤5 行；纯配置/文案修复 | 跳过步骤① | ~3 min |
| **⚡ 标准修复** | 根因已明确 + 改动 >5 行；局部逻辑修复 | 跳过步骤① | ~10 min |
| **🔍 调试修复** | 根因不明；需要先定位问题 | 先走 `/systematic-debugging` | ~20 min |

**快速/标准修复**直接从步骤②开始。**调试修复**先调用 systematic-debugging Agent 定位根因，再进入步骤②。

**快速/标准修复的精简契约**：跳过需求拆分意味着没有 requirement-design 产出的接口签名契约。如果修复涉及接口变更（如修改方法签名、返回值、数据模型、SQL schema），code-dev Agent 在步骤③前须先产出一份**精简契约**（仅包含：方法签名 + 参数类型 + 返回类型），写入迭代计划或直接在对话中输出，作为 TDD Agent 和 Code-dev Agent 的共同输入。纯配置/文案修复无需精简契约。

---

## 编排流程

### 步骤 ①：系统化调试（仅调试修复通道）

1. 读取 `.claude/agents/systematic-debugging.md`
2. 调用调试 Agent：复现 → 假设生成 → 假设验证 → 定位根因
3. 确认根因后进入步骤②

### 步骤 ②：TDD Agent 确认复现

1. 读取 `.claude/agents/tdd.md`
2. 调用 TDD Agent：执行相关测试（`mvn test -Dtest=...`）或根据 Bug 描述设计复现测试
3. 确认 Bug 可复现（测试失败）

### 步骤 ③：Code-dev Agent 修复

1. 读取 `.claude/agents/code-dev.md`
2. 调用代码开发 Agent：基于 Bug 描述和验收标准修复实现
3. **禁止传递测试实现代码**，仅传递 Bug 描述、相关 PRD/TAD 摘要
4. 如修复涉及接口变更，需更新迭代计划中的接口签名契约

### 步骤 ④：TDD Agent 确认修复

1. 再次调用 TDD Agent 执行测试
2. 确认 Bug 已修复（测试通过）
3. 如仍失败，回到步骤 ③ 继续修复

### 步骤 ⑤：Review + 反馈处理

1. 读取 `.claude/agents/review.md`
2. 调用 Review Agent 对修复代码做审查
3. 读取 `.claude/agents/review-feedback.md`
4. 调用 Review-feedback Agent 分类处理审查报告（必须修改/建议修改/可以保留）
5. 对需要修改的项：code-dev Agent 落实修改 → TDD 复测 → 重新 review

### 完成

修复通过后，**文档同步与代码提交合并为同一步骤**：

1. 调用 verify Agent 执行完成前验证（代码/文档/Git 三维检查）
2. 执行文档同步（见 CLAUDE.md 检查表）
3. `git add` 代码文件 + 文档文件（一起）
4. `git commit`（代码和文档在同一个 commit 中）

---

## 上下文隔离

- code-dev Agent 禁读测试实现
- review Agent 不修改代码
