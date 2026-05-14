const state = {
  manifest: [],
  activeDate: null,
  abortController: null,
  reportsCache: {},
  isSearching: false,
  dateSwitcherOpen: false,
};

const elements = {
  homeLink: document.querySelector("#home-link"),
  homeView: document.querySelector("#home-view"),
  readerView: document.querySelector("#reader-view"),
  readLatestBtn: document.querySelector("#read-latest-btn"),
  homeSearchBtn: document.querySelector("#home-search-btn"),
  latestReportDate: document.querySelector("#latest-report-date"),
  homeReportCount: document.querySelector("#home-report-count"),
  recentReportsList: document.querySelector("#recent-reports-list"),
  dateSwitcher: document.querySelector("#date-switcher"),
  prevDateBtn: document.querySelector("#prev-date-btn"),
  nextDateBtn: document.querySelector("#next-date-btn"),
  currentDateBtn: document.querySelector("#current-date-btn"),
  dateSwitcherCurrent: document.querySelector("#date-switcher-current"),
  dateSwitcherPopover: document.querySelector("#date-switcher-popover"),
  dateSwitcherList: document.querySelector("#date-switcher-list"),
  reportCount: document.querySelector("#report-count"),
  activeDateLabel: document.querySelector("#active-date-label"),
  loadingState: document.querySelector("#loading-state"),
  reportContent: document.querySelector("#report-content"),
  themeToggle: document.querySelector("#theme-toggle"),
  searchBtn: document.querySelector("#search-btn"),
  searchModal: document.querySelector("#search-modal"),
  searchBackdrop: document.querySelector("#search-backdrop"),
  searchInput: document.querySelector("#search-input"),
  closeSearchBtn: document.querySelector("#close-search-btn"),
  searchResults: document.querySelector("#search-results"),
};

function updateThemeIcon(themeSetting) {
  if (!elements.themeToggle) return;
  elements.themeToggle.querySelector('.icon-sun').style.display = themeSetting === 'light' ? 'block' : 'none';
  elements.themeToggle.querySelector('.icon-moon').style.display = themeSetting === 'dark' ? 'block' : 'none';
  const iconSystem = elements.themeToggle.querySelector('.icon-system');
  if (iconSystem) {
    iconSystem.style.display = themeSetting === 'system' ? 'block' : 'none';
  }
}

function applyTheme(themeSetting) {
  const isDark = themeSetting === 'dark' || (themeSetting === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
}

function initTheme() {
  let currentSetting = localStorage.getItem('theme') || 'system';
  applyTheme(currentSetting);
  updateThemeIcon(currentSetting);

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if ((localStorage.getItem('theme') || 'system') === 'system') {
      applyTheme('system');
    }
  });

  if (elements.themeToggle) {
    elements.themeToggle.addEventListener('click', () => {
      let current = localStorage.getItem('theme') || 'system';
      let nextSetting = 'system';
      if (current === 'system') nextSetting = 'light';
      else if (current === 'light') nextSetting = 'dark';
      else nextSetting = 'system';

      localStorage.setItem('theme', nextSetting);
      applyTheme(nextSetting);
      updateThemeIcon(nextSetting);
    });
  }
}

function getHashDate() {
  return window.location.hash.replace(/^#/, "").trim();
}

function setHashDate(date) {
  const nextHash = `#${date}`;
  if (window.location.hash !== nextHash) {
    window.location.hash = nextHash;
  }
}

function formatDate(date) {
  const [year, month, day] = date.split("-");
  return `${year}.${month}.${day}`;
}

function goHome() {
  if (window.location.hash) {
    history.pushState("", "", window.location.pathname + window.location.search);
  }
  showHomeView();
}

function formatHomeDate(date) {
  const [, month, day] = date.split("-");
  return `${Number(month)}月${Number(day)}日`;
}

function extractOverview(markdownText) {
  const match = markdownText.match(/##\s*今日概览\s*\n+([\s\S]*?)(?=\n##\s|$)/);
  if (!match) {
    return "本期概览暂不可用，点击查看日报正文。";
  }

  const overview = match[1]
    .split(/\n+/)
    .map((line) => line.trim())
    .find((line) => line && !line.startsWith(">"));

  if (!overview) {
    return "本期概览暂不可用，点击查看日报正文。";
  }

  return overview
    .replace(/^([-+*]|\d+[.)])\s+/, "")
    .replace(/[#*`_>]/g, "")
    .trim();
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function showLoading(isLoading) {
  elements.loadingState.classList.toggle("hidden", !isLoading);
  if (isLoading) {
    elements.reportContent.classList.remove("ready");
  }
}

function showMessage(className, message) {
  elements.reportContent.innerHTML = `<div class="${className}">${escapeHtml(message)}</div>`;
  elements.reportContent.classList.add("ready");
}

function showHomeView() {
  closeDateSwitcher();
  if (elements.homeView) elements.homeView.hidden = false;
  if (elements.readerView) elements.readerView.hidden = true;
  document.title = "绿群日报";
}

function showReaderView() {
  if (elements.homeView) elements.homeView.hidden = true;
  if (elements.readerView) elements.readerView.hidden = false;
}

function renderMarkdown(markdownText) {
  if (!window.marked || !window.DOMPurify) {
    throw new Error("Markdown renderer is unavailable");
  }

  const rawHtml = window.marked.parse(markdownText, {
    breaks: false,
    gfm: true,
  });
  return window.DOMPurify.sanitize(rawHtml);
}

function getActiveIndex() {
  return state.manifest.findIndex((item) => item.date === state.activeDate);
}

function setDateSwitcherOpen(isOpen) {
  state.dateSwitcherOpen = isOpen;

  if (elements.dateSwitcherPopover) {
    elements.dateSwitcherPopover.hidden = !isOpen;
  }

  if (elements.dateSwitcher) {
    elements.dateSwitcher.classList.toggle("open", isOpen);
  }

  for (const button of [elements.currentDateBtn]) {
    if (button) {
      button.setAttribute("aria-expanded", String(isOpen));
    }
  }
}

function closeDateSwitcher() {
  if (!state.dateSwitcherOpen) {
    return;
  }
  setDateSwitcherOpen(false);
}

function toggleDateSwitcher() {
  if (!elements.dateSwitcherPopover) {
    return;
  }
  setDateSwitcherOpen(!state.dateSwitcherOpen);
}

function navigateDate(offset) {
  const activeIndex = getActiveIndex();
  if (activeIndex === -1) return;

  const nextItem = state.manifest[activeIndex + offset];
  if (nextItem) {
    setHashDate(nextItem.date);
  }
}

function renderDateSwitcher() {
  if (!elements.dateSwitcherList || !elements.dateSwitcherCurrent) {
    return;
  }

  if (!state.manifest.length) {
    elements.dateSwitcherCurrent.textContent = "暂无日报";
    elements.dateSwitcherList.innerHTML = '<div class="date-switcher-empty">暂无可展示的日报。</div>';
    for (const button of [elements.prevDateBtn, elements.nextDateBtn, elements.currentDateBtn]) {
      if (button) {
        button.disabled = true;
      }
    }
    elements.currentDateBtn?.setAttribute("aria-label", "当前日报日期，暂无可展示的日报");
    closeDateSwitcher();
    return;
  }

  const activeIndex = getActiveIndex();
  const activeItem = state.manifest[activeIndex] ?? state.manifest[0];
  const resolvedIndex = activeIndex === -1 ? 0 : activeIndex;

  elements.dateSwitcherCurrent.textContent = formatDate(activeItem.date);
  elements.currentDateBtn?.setAttribute("aria-label", `当前日报 ${formatDate(activeItem.date)}，打开日期列表`);

  if (elements.prevDateBtn) {
    elements.prevDateBtn.disabled = resolvedIndex >= state.manifest.length - 1;
  }
  if (elements.nextDateBtn) {
    elements.nextDateBtn.disabled = resolvedIndex <= 0;
  }
  for (const button of [elements.currentDateBtn]) {
    if (button) {
      button.disabled = false;
    }
  }

  elements.dateSwitcherList.innerHTML = state.manifest
    .map((item) => {
      const isActive = item.date === activeItem.date;
      return `
        <button class="date-switcher-item${isActive ? " active" : ""}" data-date="${item.date}" type="button" aria-pressed="${isActive}">
          <span class="date-switcher-item-date">${formatDate(item.date)}</span>
        </button>
      `;
    })
    .join("");
}

function renderHomeView() {
  if (!elements.latestReportDate || !elements.homeReportCount || !elements.recentReportsList) {
    return;
  }

  elements.homeReportCount.textContent = `${state.manifest.length} 篇`;

  if (!state.manifest.length) {
    elements.latestReportDate.textContent = "暂无日报";
    elements.recentReportsList.innerHTML = '<div class="date-switcher-empty">暂无可展示的日报。</div>';
    return;
  }

  const [latestReport] = state.manifest;
  elements.latestReportDate.textContent = formatHomeDate(latestReport.date);
  elements.recentReportsList.innerHTML = state.manifest
    .slice(0, 7)
    .map((item, index) => {
      const label = index === 0 ? '<span class="recent-report-label">最新</span>' : "";
      return `
        <a class="recent-report-item" href="#${item.date}" data-date="${item.date}">
          <span class="recent-report-meta">
            <span class="recent-report-date">${formatHomeDate(item.date)}</span>
            ${label}
          </span>
          <span class="recent-report-summary">正在读取概览...</span>
        </a>
      `;
    })
    .join("");
  loadRecentReportSummaries();
}

async function loadRecentReportSummaries() {
  if (!elements.recentReportsList || !state.manifest.length) {
    return;
  }

  const recentItems = state.manifest.slice(0, 7);
  await Promise.all(recentItems.map(async (item) => {
    const link = elements.recentReportsList.querySelector(`[data-date="${item.date}"]`);
    const summary = link?.querySelector(".recent-report-summary");
    if (!summary) {
      return;
    }

    try {
      if (!item.md_path) {
        throw new Error("Missing report path");
      }
      const response = await fetch(`./data/${item.md_path}`, { cache: "force-cache" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const markdown = await response.text();
      summary.textContent = extractOverview(markdown);
    } catch (error) {
      console.error(error);
      summary.textContent = "概览加载失败，点击查看日报正文。";
    }
  }));
}

function updateHeader(item) {
  if (elements.activeDateLabel) {
    elements.activeDateLabel.textContent = "";
  }
  elements.reportCount.textContent = `${state.manifest.length} 篇日报`;
  document.title = `${item.date} | 绿群日报`;
}

async function loadReport(date) {
  const item = state.manifest.find((entry) => entry.date === date) ?? state.manifest[0];
  if (!item) {
    showReaderView();
    showLoading(false);
    showMessage("empty-state", "暂无可展示的日报。");
    return;
  }

  showReaderView();
  state.activeDate = item.date;
  updateHeader(item);
  renderDateSwitcher();
  closeDateSwitcher();
  showLoading(true);

  if (state.abortController) {
    state.abortController.abort();
  }
  state.abortController = new AbortController();
  const signal = state.abortController.signal;

  try {
    if (!item.md_path) {
      throw new Error("Missing report path");
    }

    const response = await fetch(`./data/${item.md_path}`, { cache: "no-store", signal });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const markdown = await response.text();
    elements.reportContent.innerHTML = renderMarkdown(markdown);
    showLoading(false);
    requestAnimationFrame(() => {
      elements.reportContent.classList.add("ready");
    });
  } catch (error) {
    if (error.name === 'AbortError') return;
    console.error(error);
    showLoading(false);
    showMessage("error-state", "日报内容加载失败，请稍后刷新重试。");
  }
}

async function loadManifest() {
  showLoading(true);

  try {
    const response = await fetch("./data/reports.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    state.manifest = await response.json();
    if (!Array.isArray(state.manifest) || !state.manifest.length) {
      state.manifest = [];
      renderHomeView();
      elements.reportCount.textContent = "0 篇日报";
      showLoading(false);
      renderDateSwitcher();
      showMessage("empty-state", "还没有可展示的日报，等下一次生成后这里会自动更新。");
      showHomeView();
      return;
    }

    renderHomeView();
    elements.reportCount.textContent = `${state.manifest.length} 篇日报`;
    const targetDate = getHashDate();
    if (!targetDate) {
      showLoading(false);
      renderDateSwitcher();
      showHomeView();
      return;
    }
    if (!state.manifest.some((item) => item.date === targetDate)) {
      setHashDate(state.manifest[0].date);
      return;
    }
    await loadReport(targetDate);
  } catch (error) {
    console.error(error);
    showReaderView();
    elements.reportCount.textContent = "读取失败";
    showLoading(false);
    renderDateSwitcher();
    showMessage("error-state", "日报索引加载失败，请确认 pages/data 已成功生成。");
  }
}

window.addEventListener("hashchange", () => {
  if (!state.manifest.length) {
    return;
  }
  if (!getHashDate()) {
    showHomeView();
    return;
  }
  const isKnownDate = state.manifest.some((item) => item.date === getHashDate());
  const targetDate = isKnownDate ? getHashDate() : state.manifest[0].date;
  if (!isKnownDate) {
    setHashDate(targetDate);
    return;
  }
  loadReport(targetDate);
});

function initDateSwitcher() {
  renderDateSwitcher();
  elements.prevDateBtn?.addEventListener("click", () => navigateDate(1));
  elements.nextDateBtn?.addEventListener("click", () => navigateDate(-1));
  elements.currentDateBtn?.addEventListener("click", toggleDateSwitcher);

  elements.dateSwitcherList?.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const button = target?.closest(".date-switcher-item");
    if (!(button instanceof HTMLElement)) {
      return;
    }
    const { date } = button.dataset;
    if (!date) {
      return;
    }
    setHashDate(date);
    closeDateSwitcher();
  });

  document.addEventListener("click", (event) => {
    if (!state.dateSwitcherOpen || !elements.dateSwitcher) {
      return;
    }
    if (!(event.target instanceof Node) || !elements.dateSwitcher.contains(event.target)) {
      closeDateSwitcher();
    }
  });
}

function initHome() {
  elements.homeLink?.addEventListener("click", (event) => {
    event.preventDefault();
    goHome();
  });

  elements.readLatestBtn?.addEventListener("click", () => {
    const latestReport = state.manifest[0];
    if (latestReport) {
      setHashDate(latestReport.date);
    }
  });

  elements.homeSearchBtn?.addEventListener("click", openSearch);
}

// --- Search Functionality ---
let searchDebounceTimeout = null;

function openSearch() {
  closeDateSwitcher();
  elements.searchModal.hidden = false;
  elements.searchModal.setAttribute('aria-hidden', 'false');
  elements.searchInput.focus();
  prefetchAllReports();
}

function closeSearch() {
  elements.searchModal.hidden = true;
  elements.searchModal.setAttribute('aria-hidden', 'true');
  elements.searchInput.value = '';
  elements.searchResults.innerHTML = '<div class="search-placeholder">输入关键词开始搜索...</div>';
}

async function prefetchAllReports() {
  if (state.isSearching || Object.keys(state.reportsCache).length === state.manifest.length) return;
  state.isSearching = true;
  try {
    const promises = state.manifest.map(async (item) => {
      if (state.reportsCache[item.date]) return;
      const res = await fetch(`./data/${item.md_path}`, { cache: "force-cache" });
      if (res.ok) {
        state.reportsCache[item.date] = await res.text();
      }
    });
    await Promise.all(promises);
    // If user already typed something while fetching, perform search
    if (elements.searchInput.value.trim()) {
      performSearch(elements.searchInput.value);
    }
  } catch (err) {
    console.error("Failed to prefetch reports for search:", err);
  } finally {
    state.isSearching = false;
  }
}

function performSearch(query) {
  if (!query.trim()) {
    elements.searchResults.innerHTML = '<div class="search-placeholder">输入关键词开始搜索...</div>';
    return;
  }

  const keywords = query.trim().toLowerCase().split(/\s+/);
  const results = [];

  for (const item of state.manifest) {
    const text = state.reportsCache[item.date];
    if (!text) continue;

    const lowerText = text.toLowerCase();
    const isMatch = keywords.every(kw => lowerText.includes(kw));

    if (isMatch) {
      const firstKwIndex = lowerText.indexOf(keywords[0]);
      const start = Math.max(0, firstKwIndex - 40);
      const end = Math.min(text.length, firstKwIndex + 120);
      let snippet = text.substring(start, end);
      
      snippet = snippet.replace(/[\r\n]+/g, ' ').replace(/[#*`_>]/g, '');
      snippet = escapeHtml(snippet);
      
      if (start > 0) snippet = '...' + snippet;
      if (end < text.length) snippet += '...';

      keywords.forEach(kw => {
        const escapedKw = escapeHtml(kw);
        const regex = new RegExp(`(${escapedKw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        snippet = snippet.replace(regex, '<mark>$1</mark>');
      });

      results.push({ date: item.date, snippet });
    }
  }

  if (results.length === 0) {
    elements.searchResults.innerHTML = '<div class="search-placeholder">没有找到相关结果</div>';
    return;
  }

  elements.searchResults.innerHTML = results.map(res => `
    <a href="#${res.date}" class="search-result-item" data-date="${res.date}">
      <h3 class="search-result-title">${formatDate(res.date)}</h3>
      <div class="search-result-snippet">${res.snippet}</div>
    </a>
  `).join('');

  elements.searchResults.querySelectorAll('.search-result-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const date = item.dataset.date;
      setHashDate(date);
      closeSearch();
    });
  });
}

function initSearch() {
  if (!elements.searchBtn) return;
  
  elements.searchBtn.addEventListener('click', openSearch);
  elements.closeSearchBtn.addEventListener('click', closeSearch);
  elements.searchBackdrop.addEventListener('click', closeSearch);
  
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && state.dateSwitcherOpen) {
      closeDateSwitcher();
    }
    if (e.key === 'Escape' && !elements.searchModal.hidden) {
      closeSearch();
    }
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      openSearch();
    }
  });

  elements.searchInput.addEventListener('input', (e) => {
    clearTimeout(searchDebounceTimeout);
    searchDebounceTimeout = setTimeout(() => {
      performSearch(e.target.value);
    }, 250);
  });
}

initTheme();
initDateSwitcher();
initSearch();
initHome();
loadManifest();
