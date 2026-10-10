"""Generate the project workflow figure using only the Python standard library."""

from html import escape
from pathlib import Path


OUT = Path(__file__).resolve().parent
W, H = 2240, 1040
INK, MUTED, LINE = "#192938", "#586777", "#6b7885"
BLUE, TEAL, PURPLE, GOLD = "#436c9b", "#277e79", "#76609d", "#9b7431"
parts = []


def rect(x, y, w, h, fill="white", stroke="#d6dde5", radius=10, dash=False):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="1.7"'
                 + (' stroke-dasharray="7 5"' if dash else '') + '/>')


def text(x, y, value, size=22, fill=INK, weight=400, anchor="start", mono=False):
    family = "'SFMono-Regular',Consolas,monospace" if mono else "'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',Arial,sans-serif"
    parts.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
                 f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(value)}</text>')


def lines(x, y, values, size=21, fill=MUTED, gap=34, **kwargs):
    for i, value in enumerate(values):
        text(x, y + gap * i, value, size, fill, **kwargs)


def path(d, stroke=LINE, dash=False, arrow=False, width=2):
    parts.append(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}" '
                 'stroke-linecap="round" stroke-linejoin="round"'
                 + (' stroke-dasharray="7 5"' if dash else '')
                 + (' marker-end="url(#arrow)"' if arrow else '') + '/>')


def flow(x1, y1, x2, y2, dash=False):
    path(f'M{x1} {y1} L{x2} {y2}', dash=dash, arrow=True, width=2.4)


def chip(x, y, w, label, color, fill="white", size=18):
    rect(x, y, w, 32, fill, color, 6)
    text(x + w / 2, y + 23, label, size, color, 500, "middle")


def panel(x, w, letter, title, subtitle, color, fill):
    rect(x, 140, w, 828, fill, "#dce2e8", 14)
    rect(x + 20, 163, 38, 38, color, color, 8)
    text(x + 39, 190, letter, 23, "white", 600, "middle")
    text(x + 72, 190, title, 27, INK, 600)
    text(x + 22, 227, subtitle, 19, color, 500)


def card(x, y, w, h, title, color):
    rect(x, y, w, h, "white", color)
    text(x + w / 2, y + 40, title, 25, INK, 600, "middle")
    path(f'M{x + 16} {y + 58} H{x + w - 16}', "#e3e7ed", width=1.3)


def build_svg():
    parts.clear()
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">')
    parts.append('<title id="title">CS Baoyan Chat Daily：从群聊到证据约束的结构化日报</title>')
    parts.append('<desc id="desc">ChatLab JSON 经校验、脱敏和重叠分块后，由模型分块提取带证据编号的候选信息，再按四个板块分别编辑；合并校验后由程序渲染 Markdown。完整流水线默认执行发布检查，可选上传 R2、供 Pages 读取并发送 Telegram 概览。证据编号仅供内部校验。</desc>')
    parts.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#6b7885"/></marker></defs>')
    rect(0, 0, W, H, "white", "none", 0)
    text(40, 59, "从群聊到结构化日报", 37, INK, 600)
    text(40, 99, "CS Baoyan Chat Daily  /  Evidence-constrained report generation", 23, MUTED)
    text(2200, 57, "SYSTEM WORKFLOW", 20, MUTED, 500, "end")
    text(2200, 93, "输入 → 隐私预处理 → 两阶段生成 → 输出与分发", 21, MUTED, 400, "end")

    panel(40, 270, "a", "数据接入", "DATA INGESTION", BLUE, "#f5f8fc")
    panel(335, 390, "b", "隐私预处理", "PRIVACY & CHUNKING", TEAL, "#f3f9f8")
    panel(750, 1020, "c", "证据约束的两阶段生成", "CHUNK EXTRACTION → SECTION SYNTHESIS", PURPLE, "#f8f6fb")
    panel(1795, 405, "d", "输出与分发", "RENDERING & OPTIONAL DELIVERY", GOLD, "#fcf9f2")

    card(65, 280, 220, 290, "ChatLab JSON", BLUE)
    lines(87, 377, ["chatlab.version", "meta / members", "messages"], 19, BLUE, 39, mono=True)
    path('M87 490 H263', "#dce3ec", width=1.3)
    lines(87, 525, ["统一公开输入格式"], 20)
    rect(65, 650, 220, 105, "white", "#c9d7e6", 8)
    lines(83, 685, ["已有 JSON 文件", "或外部 QQ 导出器"], 20, MUTED, 37)
    flow(175, 650, 175, 576)
    lines(65, 809, ["按目标日期选择文件", "校验输入结构", "提取消息列表"], 21, MUTED, 37)
    text(65, 931, "无可用消息：结束流程", 19, BLUE)

    card(360, 280, 170, 290, "清洗与脱敏", TEAL)
    lines(379, 378, ["过滤系统消息", "清理纯噪声", "发送者匿名化", "联系方式脱敏", "链接与引用脱敏"], 19, MUTED, 37)
    flow(285, 425, 354, 425)
    flow(530, 425, 552, 425)
    for dy in (20, 10, 0):
        rect(561 + dy / 2, 315 + dy, 130, 220, "white", TEAL, 8)
    text(626, 352, "重叠分块", 22, TEAL, 600, "middle")
    for i in range(3):
        chip(575, 375 + i * 47, 103, f"Chunk {i + 1}", TEAL, "#f3f9f8", 17)
    path('M581 415 H672 M581 462 H672', TEAL, dash=True, width=1.5)
    rect(360, 650, 340, 105, "white", "#bdd9d5", 8)
    text(378, 684, "内部消息标识", 21, TEAL, 600)
    text(378, 724, "M00001  ·  User_1", 20, INK, mono=True)
    lines(360, 809, ["默认分块：400 条 / 20,000 字符", "相邻块重叠 20 条消息", "保留时间与脱敏后的回复上下文"], 20, MUTED, 37)
    text(360, 931, "脱敏在模型调用前完成", 19, TEAL, 500)

    card(775, 280, 200, 290, "① 分块提取", PURPLE)
    for i, label in enumerate(["Chunk 1 → LLM", "Chunk 2 → LLM", "Chunk n → LLM"]):
        chip(793, 367 + i * 47, 164, label, PURPLE, "#f8f6fb", 18)
    text(875, 548, "并发提取候选信息", 18, MUTED, 400, "middle")
    flow(701, 425, 769, 425)
    card(1005, 280, 200, 290, "候选信息 JSON", PURPLE)
    lines(1022, 372, ["内容摘要", "类别 / 置信度", "时间线 / 不确定性"], 19, MUTED, 37)
    rect(1020, 483, 170, 57, "#f3eef9", "none", 7)
    text(1032, 507, "evidence:", 17, PURPLE, mono=True)
    text(1032, 530, '["M00001", …]', 17, PURPLE, mono=True)
    flow(975, 425, 999, 425)
    card(1235, 260, 250, 330, "② 分板块编辑", PURPLE)
    for i, (title, field) in enumerate([
        ("今日值得关注", "high_value"),
        ("今日讨论脉络", "timeline_topics"),
        ("传闻与待核实", "uncertain"),
        ("轻松一刻", "light_moments"),
    ]):
        rect(1251, 335 + 58 * i, 218, 49, "#f8f6fb", "#d8cce6", 6)
        text(1264, 357 + 58 * i, title, 19, INK, 500)
        text(1264, 376 + 58 * i, field, 14, PURPLE, mono=True)
    text(1360, 581, "各板块独立请求 · 最多 2 路并发", 15, MUTED, 400, "middle")
    flow(1205, 425, 1229, 425)
    card(1515, 280, 230, 290, "合并与校验", PURPLE)
    lines(1535, 375, ["JSON 结构与数量", "证据编号有效性", "板块引用范围", "活跃时段覆盖"], 20, MUTED, 39)
    chip(1533, 527, 194, "校验通过", PURPLE, "#f3eef9", 18)
    flow(1485, 425, 1509, 425)

    # Request-local validation feedback; final merged validation can abort.
    path('M935 570 V613 H815 V576', PURPLE, dash=True, arrow=True)
    text(875, 643, "失败反馈 / 重试", 18, PURPLE, 400, "middle")
    path('M1450 590 V613 H1270 V596', PURPLE, dash=True, arrow=True)
    text(1360, 643, "失败反馈 / 重试", 18, PURPLE, 400, "middle")
    text(1630, 635, "最终校验失败则中止", 18, PURPLE, 400, "middle")
    rect(775, 683, 970, 72, "white", "#d8cce6", 8)
    text(796, 713, "恢复与复用", 21, PURPLE, 600)
    text(946, 713, "分块检查点  ·  失败块可二分重试  ·  终稿板块缓存", 21, MUTED)
    text(796, 741, "只复用通过校验且与当前输入匹配的结果", 18, MUTED)
    lines(775, 809, ["提取阶段：为候选信息保留真实消息编号；没有明确回答的提问不作为事实。", "编辑阶段：合并重复内容，按板块约束可引用证据，保留时间线与不确定性。"], 21, MUTED, 37)
    text(775, 931, "证据编号供内部校验使用，不代表自动核实信息真实性", 19, PURPLE)

    card(1820, 280, 355, 290, "Markdown 日报", GOLD)
    text(1840, 376, "程序确定性渲染", 23, GOLD, 600)
    lines(1840, 420, ["固定四板块与顺序", "不公开内部证据编号", "写入本地私有报告目录"], 22, MUTED, 42)
    flow(1745, 425, 1814, 425)
    rect(1820, 626, 355, 72, "white", GOLD, 8)
    text(1997, 655, "发布检查", 22, INK, 600, "middle")
    text(1997, 683, "结构 / 联系方式 / 高风险标签", 19, MUTED, 400, "middle")
    flow(1997, 570, 1997, 620)
    text(2011, 605, "完整流水线", 16, MUTED)
    rect(1820, 756, 355, 63, "white", GOLD, 8, dash=True)
    text(1997, 795, "Cloudflare R2  ·  可选发布", 22, GOLD, 500, "middle")
    flow(1997, 698, 1997, 750, dash=True)
    text(2011, 735, "检查通过", 16, MUTED)
    rect(1820, 875, 164, 57, "white", GOLD, 8, dash=True)
    rect(2005, 875, 170, 57, "white", GOLD, 8, dash=True)
    text(1902, 910, "Pages 阅读", 20, GOLD, 500, "middle")
    text(2090, 910, "Telegram 概览", 19, GOLD, 500, "middle")
    path('M1997 819 V844 H1902 V869', dash=True, arrow=True)
    path('M1997 844 H2090 V869', dash=True, arrow=True)

    path('M40 990 H2200', "#d9e0e6", width=1.3)
    flow(43, 1017, 92, 1017)
    text(106, 1024, "主流程", 18, MUTED)
    flow(232, 1017, 282, 1017, dash=True)
    text(296, 1024, "可选分发", 18, MUTED)
    path('M449 1017 H499', PURPLE, dash=True, arrow=True)
    text(514, 1024, "模型请求校验 / 重试", 18, MUTED)
    text(2200, 1024, "图示描述代码能力；公开日报已停止每日更新，Pages 为历史预览。", 19, MUTED, 400, "end")
    parts.append('</svg>')
    return "\n".join(parts)


def build_html(svg):
    return '''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>项目流程图 · CS Baoyan Chat Daily</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#edf0f4;color:#192938;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}header{max-width:1680px;margin:0 auto;padding:28px 32px;display:flex;justify-content:space-between;align-items:center;gap:20px}h1{font-size:22px;margin:0 0 8px}p{font-size:14px;color:#586777;margin:0;line-height:1.7}nav{display:flex;gap:12px;flex-shrink:0}a,button{background:white;border:1px solid #ccd5df;border-radius:6px;padding:10px 15px;text-decoration:none;color:#294f78;font:inherit;font-size:14px;cursor:pointer}.canvas{margin:0 24px 24px;background:white;border:1px solid #d9e0e8;border-radius:8px;overflow:auto}.canvas svg{display:block;width:100%;height:auto;min-width:1000px}.canvas.actual svg{width:2240px}.caption{max-width:1680px;margin:0 auto 30px;padding:0 32px;font-size:14px;line-height:1.9;color:#586777}.caption strong{color:#192938}@media print{header{display:none}.caption{display:none}body{background:white}.canvas{border:0;margin:0}.canvas svg{min-width:0;width:100%}@page{size:landscape;margin:8mm}}
</style>
<header><div><h1>项目流程图</h1><p>按当前代码绘制 · 中文论文风格 · SVG 矢量格式可继续编辑</p></div><nav><button onclick="document.querySelector('.canvas').classList.toggle('actual')">原尺寸 / 适应宽度</button><a href="workflow.svg" download>下载 SVG</a><a href="workflow.png" download>下载 PNG</a></nav></header>
<main class="canvas">''' + svg + '''</main>
<div class="caption"><strong>图 1. 从群聊到结构化日报的系统流程。</strong>系统以 ChatLab JSON 为输入，在模型调用前进行消息清洗、身份匿名化、敏感信息脱敏与重叠分块。第一阶段逐块提取附带内部证据编号的结构化候选信息；第二阶段对四个板块分别编辑，并校验引用范围和时间线覆盖。结果由程序确定性渲染为 Markdown。完整流水线默认执行发布检查，之后可发布至 R2，由 Pages 读取，并发送 Telegram 概览。公开日报已停止每日更新。<br>说明：默认分块限制按字符数与消息数双重控制，单条超长消息可单独成块；模型输出失败在请求内重试，最终合并校验失败则中止。检查仅降低风险，发布前仍建议人工复核。</div></html>'''


if __name__ == "__main__":
    svg = build_svg()
    (OUT / "workflow.svg").write_text(svg, encoding="utf-8")
    (OUT / "workflow.html").write_text(build_html(svg), encoding="utf-8")
    print(f"Generated {OUT / 'workflow.svg'} and workflow.html")
