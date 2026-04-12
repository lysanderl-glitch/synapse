# Synapse Changelog

## v1.0.0 — First Public Release (2026-04-12)

Synapse AI Team Operating System 正式发行版。
44 Agents × 14 Skills × 4-level decision system × CEO Guard enforcement。

### Core System
- **Harness Engineering 方法论**：5原则框架（Guides+Sensors双保险、执行链、角色分离、四级决策、能力审计）
- **CLAUDE.md Harness Configuration**：完整 CEO 约束 + 执行禁区 + 派单规范
- **四级决策体系**：L1 自动 → L4 总裁，95% 决策不上报
- **执行链 v2.0**：目标→方案→派单→执行→QA→交付 强制六步流程

### CEO Guard（对话控制机制）
- `.claude/settings.json`：PreToolUse/PostToolUse hooks 技术强制
- `scripts/ceo-guard-pre.js`：审计日志 + 上下文提醒注入
- `scripts/ceo-guard-post.js`：异步执行完成记录
- CLAUDE.md 违规模式识别表 + 工具白/黑名单

### 44 Agents × 7 Teams
- **Graphify**（6人）：战略分析、情报、进化引擎（evolution_engine）
- **Harness Ops**（4人）：Harness 配置、AI 系统开发、QA
- **RD**（5人）：研发、架构、数据
- **Content Ops**（6人）：内容生产、视觉设计
- **Growth**（4人）：增长、品牌
- **OBS**（4人）：知识库、文档
- **Butler**（7人）：PMO、交付、个人助理

### 14 Skills
`/dispatch` `/qa-gate` `/retro` `/knowledge` `/intel` `/graphify`
`/dev-plan` `/dev-qa` `/dev-review` `/dev-secure` `/dev-ship` `/daily-blog`
`/synapse` `/hr-audit`

### HR 管理系统
- Agent 入职审批流程（能力评分 ≥ 90 合格）
- 能力描述质量标准（A/B/C 三级，B 级以上合格）
- 定期自动审计 `audit_all_agents()`
- evolution_engine：自进化闭环协调 + GAP 分析

### 每日自动化管线
- 情报日报（搜索→分析→HTML→推送）
- 情报行动管线（建议评估→执行→报告）
- 任务恢复 Agent（active_tasks.yaml 跨会话续接）

### Distribution
- `build-distribution.py`：7类去个人化规则，0 残留验证
- `scripts/templates/`：个性化配置模板
- `synapse.config.yaml`：用户配置入口
- 升级机制：`升级 Synapse` 一句话完成，API：`https://lysander.bond/synapse/version.json`

---

*Built with Claude Code · Harness Engineering by {{COMPANY_NAME}}*
