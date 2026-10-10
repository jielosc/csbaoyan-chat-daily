# 项目流程图

`workflow.svg` 是可编辑的矢量图；`workflow.png` 为 4480 × 2080 像素的高清版本；`workflow.html` 提供本地预览、原尺寸切换、下载入口与中文图注。

图按当前代码的默认生成路径绘制：

- `app/generate.py`：输入选择、ChatLab 校验、预处理与生成编排。
- `domain/chat_processing.py`：清洗、身份与联系方式脱敏、证据编号、重叠分块。
- `domain/report_generation.py`：分块提取、请求内校验重试、检查点、板块编辑与缓存。
- `domain/report_schema.py`：结构、证据引用与时间线覆盖校验，以及 Markdown 渲染。
- `app/pipeline.py`、`app/verify.py`：发布检查、R2 上传与 Telegram 播报编排。

图中的证据编号校验检查引用是否存在及是否属于对应板块，并不自动确认群聊内容的真实性。R2、Pages、Telegram 展示的是可选集成能力；公开日报已停止每日更新。

## 修改与生成

修改 `generate_workflow.py` 中的文字、颜色和坐标后，在仓库根目录运行：

```bash
python3 docs/figures/generate_workflow.py
```

生成器仅使用 Python 标准库，重新生成 SVG 与 HTML。PNG 需使用支持中文字体的 SVG 渲染器另行导出，按原图 2 倍尺寸导出即可得到当前分辨率。图中文字优先使用 PingFang SC，其次为 Noto Sans CJK SC 和 Microsoft YaHei；编辑 SVG 或导出时应确保有对应中文字体。

## 图注

**图 1. 从群聊到结构化日报的系统流程。** 系统以 ChatLab JSON 为输入，在模型调用前进行消息清洗、身份匿名化、敏感信息脱敏与重叠分块。第一阶段逐块提取附带内部证据编号的结构化候选信息；第二阶段对四个板块分别编辑，并校验引用范围和时间线覆盖。结果由程序确定性渲染为 Markdown。完整流水线默认执行发布检查，之后可发布至 R2，由 Pages 读取，并发送 Telegram 概览。
