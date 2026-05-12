import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const pipelineScript = await readFile(new URL("../scripts/daily_pipeline.ps1", import.meta.url), "utf8");

assert.match(pipelineScript, /\[string\]\$ReportDate\b/, "daily pipeline should accept an explicit ReportDate parameter");
assert.match(pipelineScript, /generate_daily_report\.py"\s*,\s*"--date"\s*,\s*\$resolvedReportDate/, "daily pipeline should pass the resolved report date to the generator");
assert.match(pipelineScript, /Write-Step "Sending Telegram broadcast"/, "daily pipeline should log the Telegram send phase");
assert.match(pipelineScript, /Write-Step "Skipping Telegram broadcast/, "daily pipeline should log when Telegram delivery is skipped");
assert.match(pipelineScript, /telegram_broadcast\.py/, "daily pipeline should invoke the Telegram broadcast script");
