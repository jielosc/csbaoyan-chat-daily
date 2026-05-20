# 绿群日报 — 部署与使用指南

---

## 1. 快速开始

### 环境要求

- Python 3.10+
- Git 2.x+
- [qq-chat-exporter](https://github.com/shuakami/qq-chat-exporter) 导出聊天记录
- OpenAI 兼容 API（默认 DeepSeek）

### 安装

```bash
git clone https://github.com/<your-username>/csbaoyan-chat-daily.git
cd csbaoyan-chat-daily

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
```

编辑 `.env`：

```ini
# 必填
CSBAOYAN_EXPORT_DIR=/path/to/chat-export-jsons
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_MODEL=deepseek-v4-flash

# 可选
CSBAOYAN_PAGES_DIR=pages
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@your_channel
SITE_BASE_URL=https://your-domain.example.com
```

| 变量 | 必填 | 说明 |
|------|------|------|
| `CSBAOYAN_EXPORT_DIR` | 是 | 聊天导出 JSON 所在目录 |
| `OPENAI_BASE_URL` | 是 | LLM API 端点 |
| `OPENAI_API_KEY` | 是 | LLM API 密钥 |
| `OPENAI_MODEL` | 是 | 模型名称 |
| `CSBAOYAN_PAGES_DIR` | 否 | 静态站点目录，默认 `pages` |
| `TELEGRAM_BOT_TOKEN` | 否 | Telegram Bot Token |
| `TELEGRAM_CHANNEL_ID` | 否 | Telegram 频道 ID |
| `SITE_BASE_URL` | 否 | 站点 URL，用于推送链接 |

### 运行

```bash
# macOS / Linux
chmod +x scripts/daily_pipeline.sh
scripts/daily_pipeline.sh

# Windows
.\scripts\daily_pipeline.ps1
```

日志自动写入 `logs/` 目录。

---

## 2. CLI 用法

所有命令通过 `python -m csbaoyan_daily.cli <子命令>` 调用（需设置 `PYTHONPATH=src`，脚本已自动处理）。

| 子命令 | 作用 |
|--------|------|
| `generate` | 从聊天 JSON 生成日报 |
| `verify` | 检查日报是否有隐私泄露 |
| `publish` | Git commit + push 页面数据 |
| `broadcast` | 推送摘要到 Telegram |
| `pipeline` | 按顺序执行以上全部步骤 |

**常用参数（`generate` / `pipeline`）：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--date YYYY-MM-DD` | 自动推断 | 目标日期 |
| `--model` | 环境变量 | 覆盖 LLM 模型 |
| `--max-workers N` | `4` | 并行线程数 |
| `--timeout SECS` | `120` | 单次 LLM 超时 |
| `--temperature T` | `0.2` | 采样温度 |

**`pipeline` 阶段控制：**

```bash
# 只生成，不提交推送
python -m csbaoyan_daily.cli pipeline --skip-commit

# 跳过 Telegram 推送
python -m csbaoyan_daily.cli pipeline --skip-telegram

# 只本地提交，不推远程
python -m csbaoyan_daily.cli pipeline --skip-push
```

---

## 3. 定时任务

### Linux / macOS (cron)

```bash
crontab -e
```

```cron
30 6 * * * /path/to/csbaoyan-chat-daily/scripts/daily_pipeline.sh >> /path/to/logs/cron.log 2>&1
```

### Windows（计划任务）

```powershell
.\scripts\register_daily_task.ps1                              # 默认 06:30
.\scripts\register_daily_task.ps1 -Time "07:00"               # 指定时间
.\scripts\register_daily_task.ps1 -RunWhenSignedOut -Password "xxx"  # 未登录也运行
```

### Linux (systemd)

```bash
# /etc/systemd/system/csbaoyan-daily.service
[Unit]
Description=CS Baoyan Daily Pipeline

[Service]
Type=oneshot
WorkingDirectory=/path/to/csbaoyan-chat-daily
ExecStart=/path/to/csbaoyan-chat-daily/scripts/daily_pipeline.sh

# /etc/systemd/system/csbaoyan-daily.timer
[Unit]
Description=CS Baoyan Daily Timer

[Timer]
OnCalendar=*-*-* 06:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now csbaoyan-daily.timer
```

---

## 4. 前端部署

### GitHub Pages（推荐）

项目内置 Actions 工作流，`pages/` 有变更推送到 `main` 分支时自动部署。

1. 仓库 **Settings → Pages** → Source 选择 **GitHub Actions**
2. 推送即可

### 自托管

`pages/` 是纯静态站点，任何 HTTP 服务器均可托管：

```bash
# 快速预览
cd pages && python3 -m http.server 8080
```

---

## 5. Telegram 推送

1. 在 Telegram 找 [@BotFather](https://t.me/BotFather)，`/newbot` 创建 Bot，记录 Token
2. 创建频道，将 Bot 添加为管理员（需发消息权限）
3. 在 `.env` 填入 `TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHANNEL_ID`、`SITE_BASE_URL`

---

## 6. 常见问题

**换 LLM 提供商？** 修改 `.env` 中 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`OPENAI_MODEL`，只要兼容 OpenAI 接口即可。

**生成慢？** 增大 `--max-workers`、`--chunk-max-chars`，或增大 `--timeout`。

**重新生成某天？** `python -m csbaoyan_daily.cli generate --date 2026-05-18`，会覆盖已有报告。

**匿名化可靠吗？** 项目全面脱敏用户名、UID、邮箱、URL、手机号等，`verify` 命令发布前自动扫描泄露风险。
