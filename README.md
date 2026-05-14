# 绿群日报 / CS Baoyan Chat Daily

>  CS 保研群 AI 日报整理项目，面向公开浏览与归档。


## Quick Links

- 在线阅读: https://csbaoyan.icelon.top
- Telegram Channel: https://t.me/csbaoyan
- Changelog: [CHANGELOG.md](./CHANGELOG.md)
- Workflow: [docs/workflow.md](./docs/workflow.md)

## Why This Project / 为什么做这个项目

- 保研相关信息常常淹没在高频聊天里，检索和回看都不方便。
- 群人数有限，不是所有人都能长期留在群里跟进消息。
- 把群聊中的有效信息沉淀成日报，可以降低获取门槛，也方便后续归档。

## What It Does / 项目做什么

- 读取按日期导出的群聊 JSON。
- 对消息做清洗、匿名化和分块处理。
- 用 OpenAI-compatible 模型提取重点并生成结构化日报。
- 将最终日报发布到 `pages/data/reports/`，供 GitHub Pages 使用。

## Quick Start / 快速开始

### 1. 安装依赖 / Install

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量 / Configure

最少需要配置模型相关变量：

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL`（如果你使用兼容 OpenAI 的第三方接口）

可选变量：

- `CSBAOYAN_EXPORT_DIR`
- `CSBAOYAN_PAGES_DIR`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHANNEL_ID`
- `SITE_BASE_URL`

### 3. 生成单日日报 / Generate One Report

```bash
python generate_daily_report.py --date YYYY-MM-DD
```

### 4. 跑完整日常流水线 / Run Daily Pipeline

```powershell
powershell -File scripts/daily_pipeline.ps1 -ReportDate YYYY-MM-DD
```

这条流水线会串起日报生成、发布前检查、`pages/data` 提交以及 Telegram 播报。

## Project Structure / 项目结构

- `generate_daily_report.py`: 日报生成入口，负责读取聊天导出、调用模型并写出结果。
- `scripts/daily_pipeline.ps1`: 日常运行脚本，串起生成、检查、提交与推送。
- `telegram_broadcast.py`: 从日报中提取概览并发送到 Telegram 频道。
- `pages/`: 静态站点资源与公开数据目录。
- `pages/data/reports/`: 最终公开的日报 Markdown 文件。
- `tests/`: 针对流水线脚本、站点页面和广播逻辑的测试。

## 隐私与免责声明

本项目本质上是借助 AI 对群聊内容进行摘要，内容可能存在遗漏或不完全准确的情况。涉及夏令营、预推免或其他正式招生信息时，请以官方通知为准。

项目会尽量对聊天内容做匿名化处理，降低身份暴露风险；但在少数语境下，仍不能完全排除基于上下文进行识别的可能。

如果你认为仓库中的公开内容可能涉及隐私泄露、身份暴露或其他不适合公开的信息，请及时联系我处理。

## Contributing

欢迎提 Issue、分享想法或直接发 PR，一起把这份日报做得更清晰、更有用。

如果这个项目对你有帮助，也欢迎点一个 Star 支持一下。

## Acknowledgments

- “绿群”来自 [CS-BAOYAN](https://github.com/CS-BAOYAN) 社区。
- 聊天记录导出使用了 [qq-chat-exporter](https://github.com/shuakami/qq-chat-exporter)。
- 感谢绿群中持续提供信息的同学，以及相关开源工具和社区维护者。
