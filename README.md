# CS Baoyan Chat Daily Generator 📰

从 ChatLab 群聊导出生成匿名化、可校验的 Markdown 日报。项目默认面向 CS 保研群聊，但生成、检查和发布流程可以独立使用。

> [!IMPORTANT]
> 维护者已停止公开日报的每日更新。[Pages 网站](https://csbaoyan.icelon.top)仅作为历史生成效果预览，不代表当前招生信息。

## 核心能力

- 消费已有 ChatLab JSON，或调用 [`qqnt-export-macos`](https://github.com/jielosc/qqnt-export-macos) 导出指定自然日的消息；
- 在调用模型前对发送者、联系方式和链接进行匿名化；
- 使用 OpenAI 兼容 API 分块提取信息，并保留内部证据编号；
- 确定性渲染四板块 Markdown，执行结构和隐私风险检查；
- 可选发布到 Cloudflare R2，并发送 Telegram 概览；
- 可选使用 macOS LaunchAgent 或 Windows 任务计划定时运行。

![从群聊到结构化日报的系统流程](./docs/figures/workflow.svg)

[查看大图与图注](./docs/figures/workflow.html) · [高清 PNG](./docs/figures/workflow.png) · [可编辑 SVG](./docs/figures/workflow.svg)

原始消息、脱敏记录、中间结果和最终报告默认保存在被 Git 忽略的私有目录中。仓库不包含公开日报的数据源；`pages/` 只是读取历史公开数据的静态预览前端。

## 快速开始

需要 Python 3.10 或更高版本：

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
cp .env.example .env
chmod 600 .env
```

最小模型配置：

```dotenv
OPENAI_BASE_URL=https://your-provider.example/v1
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=your-model
```

将目标日期的 ChatLab 文件放到输入目录，例如 `chatlab-2026-09-06.json`，然后生成本地日报：

```bash
csbaoyan-daily generate \
  --source json \
  --export-dir /path/to/chatlab-json \
  --report-dir ./internal/reports \
  --date 2026-09-06
```

输出为 `internal/reports/2026-09-06.md`。仅本地生成不需要 QQ、R2 或 Telegram 配置。

## 输入与项目边界

公开输入边界是 ChatLab JSON：

- 文件必须包含 `chatlab.version`、`meta`、`members` 和 `messages`；
- 每条消息至少包含 `platformMessageId`、`sender`、`timestamp`、`type` 和 `content`；
- 文件名建议包含目标日期，例如 `chatlab-YYYY-MM-DD.json`。

当使用 `--source export` 时，本项目只编排 `qqnt-export-macos export-chatlab`，不读取 QQ 数据库，也不解析 QQ 私有消息格式。此模式还需要配置 `QQNT_EXPORT_COMMAND`、`QQNT_KEY_PATH` 和 `QQNT_CONVERSATION_ID`。

## 日报结构

默认模板包含四个板块：

1. **今日值得关注**：院校与项目、申请与考核、经验与选择；
2. **今日讨论脉络**：按时间顺序概括话题、观点、分歧和阶段性结论；
3. **传闻与待核实**：单一信源、矛盾或缺少原始证据的信息；
4. **轻松一刻**：少量脱离上下文仍能理解且不会伤害具体个人的片段。

分块提取结果只用于内部校验，公开 Markdown 不包含证据编号。

## 可选集成

完整流水线可以串联生成、检查、R2 发布和 Telegram 播报：

```bash
scripts/daily_pipeline.sh --date 2026-09-06
```

这些集成都不是本地生成的前置条件：

- 自动 QQ 导出需要 `QQNT_*` 配置；
- R2 发布需要完整的 `R2_*` 配置；
- Telegram 播报需要 `TELEGRAM_*` 和 `SITE_BASE_URL`；
- 定时任务、R2 和预览站部署见[可选部署指南](./docs/deploy-guide.md)。

所有可用命令可以通过以下方式查看：

```bash
csbaoyan-daily --help
```

## 历史预览

[csbaoyan.icelon.top](https://csbaoyan.icelon.top) 展示本工具过去生成的日报。预览数据现已冻结；页面中的日期、项目、导师和招生信息可能已经过期。

Pages 前端仍可随代码变更部署，但不会触发日报生成，也不会向 R2 写入新数据。

## 隐私与免责声明

日报由 AI 从群聊中整理，可能存在遗漏或错误。涉及夏令营、预推免、招生制度和导师信息时，请以官方通知及公开资料为准。

匿名化和风险检查只能降低风险，无法保证所有上下文都绝对不可识别。使用者应在发布前人工复核，并妥善保护 ChatLab 导出、`.env` 和私有生成目录。

## License

[MIT](./LICENSE)
