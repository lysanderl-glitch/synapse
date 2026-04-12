<!-- Synapse Harness Fragment: 09-footer.md -->
<!-- Purpose: Upgrade protocol, credential management -->
<!-- Variables: {{CEO_NAME}}, {{PRESIDENT_NAME}}, {{UPGRADE_URL}} -->
<!-- Required: true -->

---

## 体系升级指令（Synapse Upgrade Protocol）

当用户说以下任意指令时，自动启动升级流程：
- `"升级 Synapse"` / `"更新体系"` / `"同步最新版本"` / `"/upgrade"`

**升级流程**（由 `harness_engineer` 执行，`{{CEO_NAME}}` 审查）：

```
Step 1：读取本地版本
        cat VERSION → 获取当前版本号

Step 2：获取最新版本信息
        访问 {{UPGRADE_URL}}
        → 返回 { version, release_date, changelog, download_url }

Step 3：版本对比 + Changelog 展示
        如 本地版本 == 最新版本 → 提示"已是最新版本"，结束
        如 本地版本 < 最新版本 → 向总裁展示 Changelog，请求确认

Step 4：总裁确认后执行升级
        → 下载最新 harness fragments
        → 重新组装 CLAUDE.md
        → 保留用户配置区的个人化设置（CEO名/总裁名/公司名）
        → 更新 VERSION 文件

Step 5：QA 验证
        integration_qa 验证新配置完整性（关键约束项是否存在）

Step 6：提示重启
        "升级完成，请关闭并重新打开 Claude Code 会话，新配置即刻生效。"
```

**注意**：升级只替换 Core Harness 区域，用户个人化配置区（CEO名/总裁名）不受影响。

## 凭证管理

敏感凭证（API Key、Token、密码）存储在 `obs/credentials.md`，使用 Meld Encrypt 加密。

### AI 调用方式

```bash
# 获取单个凭证（需要用户提供密码）
PYTHONUTF8=1 python creds.py get GITHUB_TOKEN -p "密码"

# 导出全部凭证（供批量使用）
PYTHONUTF8=1 python creds.py export -p "密码"

# 查看所有 Key 名（无需密码）
PYTHONUTF8=1 python creds.py list
```

### 使用规则

1. **需要凭证时**：先用 `list` 确认 Key 名，再向用户请求密码，用 `get` 获取值
2. **密码处理**：用户提供的密码只在当次命令中使用，不存储、不记录
3. **凭证文件**：`obs/credentials.md` 已加入 `.gitignore`，不上传 GitHub
