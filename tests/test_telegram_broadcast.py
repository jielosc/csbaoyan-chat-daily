import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csbaoyan_daily.infra.telegram import build_report_url, compose_message, extract_overview



class ExtractOverviewTests(unittest.TestCase):
    def test_extract_overview_returns_first_non_quote_paragraph(self) -> None:
        markdown = """# CS保研信息日报

## 今日概览

> 引言

今日讨论聚焦夏令营结果与导师联系策略。

第二段不应被选中。

## 重要信息
"""

        overview = extract_overview(markdown)

        self.assertEqual(overview, "今日讨论聚焦夏令营结果与导师联系策略。")

    def test_extract_overview_raises_when_section_missing(self) -> None:
        markdown = """# CS保研信息日报

## 重要信息

- 没有概览
"""

        with self.assertRaisesRegex(ValueError, "今日概览"):
            extract_overview(markdown)


class ComposeMessageTests(unittest.TestCase):
    def test_build_report_url_normalizes_trailing_slash(self) -> None:
        self.assertEqual(
            build_report_url("https://csbaoyan.icelon.top/", "2026-05-11"),
            "https://csbaoyan.icelon.top/#2026-05-11",
        )
        self.assertEqual(
            build_report_url("https://csbaoyan.icelon.top", "2026-05-11"),
            "https://csbaoyan.icelon.top/#2026-05-11",
        )

    def test_compose_message_escapes_html_sensitive_text(self) -> None:
        message = compose_message(
            report_date="2026-05-11",
            overview='今日关注 <创智> & "套磁" 变化',
            site_base_url="https://csbaoyan.icelon.top/",
        )

        self.assertNotIn("绿群日报 2026-05-11", message)
        self.assertTrue(message.startswith("今日关注"))
        self.assertIn("&lt;创智&gt;", message)
        self.assertIn("&amp;", message)
        self.assertIn("&quot;套磁&quot;", message)
        self.assertIn('href="https://csbaoyan.icelon.top/#2026-05-11"', message)
        self.assertNotIn("内容由 AI 总结生成，仅供参考，请以官方通知和公开资料为准。", message)


if __name__ == "__main__":
    unittest.main()
