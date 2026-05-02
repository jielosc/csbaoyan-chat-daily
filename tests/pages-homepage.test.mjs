import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const indexHtml = await readFile(new URL("../pages/index.html", import.meta.url), "utf8");
const appJs = await readFile(new URL("../pages/app.js", import.meta.url), "utf8");
const stylesCss = await readFile(new URL("../pages/styles.css", import.meta.url), "utf8");

assert.match(indexHtml, /id="home-view"/, "index.html should include a homepage view");
assert.match(indexHtml, /id="reader-view"/, "index.html should wrap the report reader in a reader view");
assert.match(indexHtml, /id="read-latest-btn"/, "homepage should expose a read-latest action");
assert.match(indexHtml, /id="recent-reports-list"/, "homepage should expose a recent reports list");
assert.match(indexHtml, /id="home-link"/, "header brand area should expose a home link");
assert.match(indexHtml, /class="contribute-section"/, "homepage should include a contribution section");
assert.match(indexHtml, /github\.com\/jielosc\/csbaoyan-chat-daily\/issues\/new/, "contribution section should link to GitHub issue creation");

assert.match(appJs, /function\s+showHomeView\s*\(/, "app.js should render the no-hash homepage state");
assert.match(appJs, /function\s+showReaderView\s*\(/, "app.js should render the report reader state");
assert.match(appJs, /function\s+renderHomeView\s*\(/, "app.js should populate homepage data from the manifest");
assert.match(appJs, /function\s+extractOverview\s*\(/, "app.js should extract overview text from report markdown");
assert.match(appJs, /function\s+loadRecentReportSummaries\s*\(/, "app.js should load recent report summaries for the homepage");
assert.match(appJs, /const\s+targetDate\s*=\s*getHashDate\(\)/, "manifest loading should not force a latest-date hash");

assert.match(stylesCss, /\.home-view\b/, "styles.css should style the homepage view");
assert.match(stylesCss, /\.recent-reports-list\b/, "styles.css should style the recent reports list");
assert.match(stylesCss, /\.recent-report-summary\b/, "styles.css should style recent report overview text");
assert.match(stylesCss, /\.contribute-section\b/, "styles.css should style the contribution section");
