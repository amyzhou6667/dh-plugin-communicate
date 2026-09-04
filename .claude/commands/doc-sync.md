执行文档同步，确保 PRD/TAD/TEST 与代码实现一致。

> **单一真相源**：完整的文档同步规则见 `.claude/workflows/doc-sync.md`。本命令是编排入口。

**变更描述**：$ARGUMENTS

## 执行流程

1. 读取 `.claude/workflows/doc-sync.md` 获取完整同步规则
2. 按规则执行：确定变更源 → 读取相关文档 → 差异分析 → 按依赖顺序更新 → 产出变更说明表

## 核心原则

- 文档同步不是独立步骤，是 `git commit` 的组成部分
- 禁止先 commit 代码、后补文档
- 代码和文档必须在同一个 commit 中出现
