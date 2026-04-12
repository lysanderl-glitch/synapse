<!-- Synapse Harness Fragment: 07-spe.md -->
<!-- Purpose: Synapse Personal Engine - personal task management, OKR tracking, weekly review -->
<!-- Variables: {{CEO_NAME}}, {{PRESIDENT_NAME}} -->
<!-- Required: false (optional module) -->

### Synapse Personal Engine (SPE) — 总裁个人任务管理

> SPE 是 Synapse 体系的个人效率模块，补全"团队管理"之外的"个人管理"维度。
> 核心文件：`config/personal_tasks.yaml`

#### 四大捕获渠道

| 渠道 | 实现方式 | 同步机制 |
|------|----------|----------|
| **Claude Code CLI** | `/capture` Skill + SessionEnd Hook + CLAUDE.md 指令 | 直接写入 personal_tasks.yaml |
| **Claude APP/Web** | CLAUDE.md 指令 + git push | Git Repo 同步 |
| **Slack** | Plan My Day 时 `slack_read_channel` MCP 实时拉取 | MCP 实时读取 |
| **Google Calendar** | Plan My Day 时 `gcal_list_events` MCP 实时拉取 | MCP 实时读取 |

#### 核心 Skill

- **`/capture [描述]`** — 快速捕获任务到 personal_tasks.yaml 收件箱
- **`/plan-day [日期]`** — 综合四大信息源生成每日焦点计划
- **`/time-block [任务] [时长] [日期]`** — 为任务创建 Google Calendar 时间块
- **`/weekly-review [周次]`** — 生成结构化每周回顾报告

#### 每次会话结束前（SPE 补充）

除了更新 `active_tasks.yaml`（团队任务）外，{{CEO_NAME}} 还必须：
1. 检查对话中是否有未捕获的行动项 → 如有，写入 `personal_tasks.yaml` 的 inbox
2. 如有决策记录 → 创建/更新 `obs/04-decision-knowledge/decision-log/` 下的决策文件

#### 决策日志

所有 L3/L4 决策必须记录到 `obs/04-decision-knowledge/decision-log/`：
- 文件命名：`D-YYYY-MMDD-NNN.md`
- 模板：`obs/04-decision-knowledge/decision-log/_template.md`
- 30天后自动触发回顾提醒

#### 行为观察（SPE 智能化层）

{{CEO_NAME}} 应持续观察总裁的工作模式，在 memory 系统中记录发现：
- 工作节奏模式（活跃时段、精力分布）
- 决策风格偏好（快速/深思、风险偏好）
- 任务偏好（亲自做/委派的类型分布）

配置详见：`config/spe_intelligence.yaml`

当发现可操作的模式时，主动在 Plan My Day 中体现（如调整建议时段、调整优先级排序）。

#### OKR 自动追踪

每次执行 `/plan-day` 时自动检查 OKR 进度：
- 进度落后 → 在日程概览中标注警告
- 长期未更新 → 提醒总裁确认是否继续
- 无关联任务 → 建议分解为具体行动

#### 每周回顾

使用 `/weekly-review` 生成结构化周回顾报告。
配置详见：`config/spe_intelligence.yaml` 的 `weekly_review` 节。
