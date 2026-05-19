import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csbaoyan_daily.app.pipeline import PipelineOptions, run_pipeline
from csbaoyan_daily.infra.git_publish import PublishResult


class PipelineTests(unittest.TestCase):
    def test_skip_commit_avoids_publish_and_broadcast(self) -> None:
        options = PipelineOptions(
            repo_root=Path.cwd(),
            date="2026-05-18",
            skip_generate=True,
            skip_release_check=True,
            skip_commit=True,
        )

        with patch("csbaoyan_daily.app.pipeline.run_publish") as mocked_publish, patch(
            "csbaoyan_daily.app.pipeline.broadcast_report"
        ) as mocked_broadcast:
            resolved_date = run_pipeline(options)

        self.assertEqual(resolved_date, "2026-05-18")
        mocked_publish.assert_not_called()
        mocked_broadcast.assert_not_called()

    def test_no_changes_skips_broadcast(self) -> None:
        options = PipelineOptions(
            repo_root=Path.cwd(),
            date="2026-05-18",
            skip_generate=True,
            skip_release_check=True,
            skip_push=False,
        )

        with patch(
            "csbaoyan_daily.app.pipeline.run_publish",
            return_value=PublishResult(changes_detected=False, committed=False, pushed=False),
        ) as mocked_publish, patch("csbaoyan_daily.app.pipeline.broadcast_report") as mocked_broadcast, patch(
            "csbaoyan_daily.app.pipeline.run_publish_preflight",
            return_value="main",
        ):
            resolved_date = run_pipeline(options)

        self.assertEqual(resolved_date, "2026-05-18")
        mocked_publish.assert_called_once()
        mocked_broadcast.assert_not_called()

    def test_successful_publish_triggers_broadcast(self) -> None:
        options = PipelineOptions(
            repo_root=Path.cwd(),
            date="2026-05-18",
            skip_generate=True,
            skip_release_check=True,
        )

        with patch(
            "csbaoyan_daily.app.pipeline.run_publish",
            return_value=PublishResult(changes_detected=True, committed=True, pushed=True, branch="main"),
        ) as mocked_publish, patch(
            "csbaoyan_daily.app.pipeline.broadcast_report",
            return_value=True,
        ) as mocked_broadcast, patch(
            "csbaoyan_daily.app.pipeline.run_publish_preflight",
            return_value="main",
        ):
            resolved_date = run_pipeline(options)

        self.assertEqual(resolved_date, "2026-05-18")
        mocked_publish.assert_called_once()
        mocked_broadcast.assert_called_once()


if __name__ == "__main__":
    unittest.main()
