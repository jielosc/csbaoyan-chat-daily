# CS Baoyan Chat Daily

把 QQ 保研群聊导出 JSON 转成匿名化聊天记录、结构化日报，以及可部署到 GitHub Pages 的静态网页。

## 功能

- 读取群聊 JSON 导出文件
- 对昵称、提及等做统一匿名化
- 按 Chunk 提取有效信息，再合成日报
- 同步站点索引到 `pages/`
- 可直接提交 `pages/data/` 用于 GitHub Pages 部署

## 环境

- Python 3.11+
- 一个 OpenAI-compatible API

安装依赖：

```bash
pip install -r requirements.txt
```

## 配置

项目支持从环境变量或本地 `.env` 读取配置。

1. 复制 `.env.example` 为 `.env`
2. 按你的环境填写值

关键变量：

- `CSBAOYAN_EXPORT_DIR`：原始聊天导出目录
- `CSBAOYAN_PAGES_DIR`：静态站点目录
- `OPENAI_BASE_URL`：兼容 OpenAI 的接口地址
- `OPENAI_API_KEY`：API Key
- `OPENAI_MODEL`：模型名

## 用法

生成最新一期日报：

```bash
python generate_daily_report.py
```

生成指定日期日报：

```bash
python generate_daily_report.py --date 2026-03-13
```

只同步 Pages 数据：

```bash
python sync_pages_data.py
```

发布前检查公开产物：

```bash
python release_check.py
```

本地预览网页：

```bash
cd pages
python -m http.server 8000
```

然后打开 `http://localhost:8000/`。

## GitHub Pages

静态网页资源位于 `pages/`，站点数据位于 `pages/data/`。
网页会直接加载 `pages/data/reports/*.md`，并在浏览器中渲染 Markdown。
Markdown 渲染依赖已随仓库一起放在 `pages/vendor/`，不依赖外部 CDN。

生成脚本的落盘位置如下：

- `internal/transcripts/<date>.txt`：脱敏聊天记录，仅供内部审阅
- `internal/extracted/<date>.md`：分块提取中间结果，仅供内部审阅
- `pages/data/reports/<date>.md`：最终日报

如果你希望把生成后的页面直接部署到 GitHub Pages，可以提交 `pages/` 目录内容，并通过以下两种方式之一部署：

- 使用 GitHub Actions 部署 `pages/` 目录
- 或把站点目录迁移到 GitHub Pages 默认识别的位置后部署

## 自动化运行

当前项目的 `generate_daily_report.py` 依赖你本机的聊天导出目录和本地 `.env`，所以“每天早上 06:30 自动生成日报”更适合放在你的 Windows 电脑上执行，而不是放到 GitHub 托管的定时任务里。

### 1. 本地每日 06:30 自动执行

先确保以下条件已经满足：

- 本机已安装 Python 3.11+
- 已填写 `.env`
- 已执行 `git remote add origin <你的 GitHub 仓库地址>`
- 当前分支为你要推送的分支（默认按 `main` 处理）

每日流水线脚本会依次执行：

1. `python generate_daily_report.py`
2. `python release_check.py`
3. `git add --all -- pages/data`
4. `git commit -m "chore: update pages data"`
5. `git push`

手动运行一次：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\daily_pipeline.ps1
```

注册为每天 06:30 的 Windows 计划任务：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register_daily_task.ps1
```

如果你需要指定 Python 路径，可以这样：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register_daily_task.ps1 -PythonCommand "C:\Python311\python.exe"
```

默认任务名为 `CSBaoyanDailyReport`，默认时间为本机时区下的 `06:30`。当前注册方式使用“用户登录时运行”；如果你希望在锁屏或注销后也继续执行，可以在 Windows 任务计划程序里把该任务改为“无论用户是否登录都要运行”并保存密码。

### 2. GitHub Pages 自动部署

仓库已提供 [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)，当 `main` 分支上的 `pages/` 有变更时会自动部署到 GitHub Pages。

你还需要在 GitHub 仓库页面完成一次设置：

1. 进入 `Settings > Pages`
2. 在 `Build and deployment` 里把 `Source` 设为 `GitHub Actions`
3. 确保默认分支是 `main`

完成后，本地计划任务每天推送新生成的 `pages/data`，GitHub 就会自动发布到 Pages。

## 仓库内容说明

- `pages/`：静态网页、公开日报和索引数据
- `internal/`：不建议公开的中间提取产物

当前仓库保留了匿名化后的示例产物，便于直接查看效果。是否继续公开这些内容，取决于你对匿名化充分性的判断。

## Public Release Notes

- 建议公开 `pages/data/reports/`，不要公开 `internal/`
- 日报内容来自群聊整理与公开信息交叉归纳，仅供参考，请以官方通知和公开资料为准
- 若涉及未核实信息、主观经验或争议评价，应在页面或正文中明确标注“待核实”

## 许可证

本项目默认采用 MIT License，见 `LICENSE`。
