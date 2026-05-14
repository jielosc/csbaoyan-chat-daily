import unittest
from unittest.mock import patch

from chat_processing import anonymize_messages
from report_generation import (
    EXTRACTION_SYSTEM_PROMPT,
    FINAL_REPORT_SYSTEM_PROMPT,
    summarize_chunk,
)


class ChatProcessingBotRemovalTests(unittest.TestCase):
    def test_anonymize_messages_does_not_preserve_removed_bot_alias(self) -> None:
        messages = [
            {
                "id": "msg-1",
                "time": "2026-05-14 10:00:00",
                "sender": {
                    "uid": "u_I7GbXJlBNyKvJIKuoZ4dXw",
                    "uin": "3352037245",
                    "name": "夕颜",
                },
                "content": {
                    "text": "大家好，我已经不在群里了",
                    "mentions": [],
                    "elements": [],
                },
            }
        ]

        anonymized = anonymize_messages(messages)

        self.assertEqual(anonymized[0].speaker, "User_1")
        self.assertNotIn("夕颜", anonymized[0].speaker)


class ReportGenerationBotRemovalTests(unittest.TestCase):
    def test_system_prompts_do_not_hardcode_removed_bot_identity(self) -> None:
        self.assertNotIn("夕颜", EXTRACTION_SYSTEM_PROMPT)
        self.assertNotIn("AI bot", EXTRACTION_SYSTEM_PROMPT)
        self.assertNotIn("夕颜", FINAL_REPORT_SYSTEM_PROMPT)
        self.assertNotIn("AI bot", FINAL_REPORT_SYSTEM_PROMPT)

    def test_summarize_chunk_prompt_does_not_mention_removed_bot(self) -> None:
        chunk = type(
            "ChunkStub",
            (),
            {
                "index": 1,
                "start_time": "2026-05-14 00:00:00",
                "end_time": "2026-05-14 00:05:00",
                "text": "[00:00] User_1: test",
            },
        )()

        with patch("report_generation.call_llm_with_retry", return_value="ok") as mocked_call:
            summarize_chunk(
                chunk=chunk,
                client=object(),
                model="test-model",
                retries=1,
                temperature=0.0,
            )

        user_prompt = mocked_call.call_args.kwargs["user_prompt"]
        self.assertNotIn("夕颜", user_prompt)
        self.assertNotIn("AI bot", user_prompt)


if __name__ == "__main__":
    unittest.main()
