# Workflow

## Overview

这个仓库的目标是把按日期导出的 CS 保研群聊天记录，整理成可以公开浏览的日报，并同步到静态站点和 Telegram 频道。

核心流程分为四步：

1. 读取聊天导出文件。
2. 清洗内容并做匿名化处理。
3. 调用 OpenAI-compatible 模型提取重点并生成最终日报。
4. 将结果写入站点目录，并在需要时推送到 Telegram。

## Main Entry Points

- `generate_daily_report.py`
  - 日报生成入口。
  - 负责加载聊天导出、提取消息、分块、调用模型和写出最终 Markdown。
- `scripts/daily_pipeline.ps1`
  - 日常运行脚本。
  - 负责串起日报生成、发布前检查、Git 提交、`git push` 和 Telegram 播报。
- `release_check.py`
  - 发布前检查脚本。
  - 用于扫描公开目录中的敏感信息和不该进入仓库的中间产物。
- `telegram_broadcast.py`
  - 从日报的“今日概览”章节提取一句摘要，并发送到 Telegram 频道。

## Inputs And Outputs

### Inputs

- 聊天导出目录默认来自 `CSBAOYAN_EXPORT_DIR`，未设置时使用 `chat_exports/`。
- 站点输出目录默认来自 `CSBAOYAN_PAGES_DIR`，未设置时使用 `pages/`。
- 模型配置来自：
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
  - `OPENAI_BASE_URL`

### Public Outputs

- `pages/data/reports/YYYY-MM-DD.md`
  - 最终公开的日报正文。
- `pages/data/reports.json`
  - 站点用于索引日报列表的清单文件。

### Private Or Intermediate Outputs

- 运行过程中还会生成脱敏聊天记录和分块提取结果。
- 这些内容用于本地处理和校验，不应作为公开数据长期保留在仓库中。
- `release_check.py` 会额外检查公开目录里是否混入了不该提交的中间文件。

## Daily Run

如果只生成某一天的日报，可以直接运行：

```bash
python generate_daily_report.py --date YYYY-MM-DD
```

如果要执行日常完整流程，使用：

```powershell
powershell -File scripts/daily_pipeline.ps1 -ReportDate YYYY-MM-DD
```

完整流水线会依次做这些事：

1. 校验 Git 远端和分支同步状态。
2. 运行 `generate_daily_report.py` 生成日报。
3. 运行 `release_check.py` 做公开内容检查。
4. 将 `pages/data` 加入暂存区并在有变更时提交。
5. 在允许推送时执行 `git push`。
6. 从最终日报提取概览并发送 Telegram 播报。

## Publishing Model

- GitHub Pages 负责展示 `pages/` 下的静态页面与日报数据。
- Telegram 频道负责分发每天的简要概览，并附上阅读全文链接。
- README 只保留项目入口和最小使用说明；更详细的处理流程集中记录在这个文档里。
