const state = {
  manifest: [],
  activeDate: null,
  abortController: null,
  reportsCache: {},
  isSearching: false,
  dateSwitcherOpen: false,
};

const elements = {
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

function updateHeader(item) {
  elements.activeDateLabel.textContent = "内容覆盖 05:00 至次日 05:00，每天 06:30 自动更新";
  elements.reportCount.textContent = `${state.manifest.length} 篇日报`;
  document.title = `${item.date} | 绿群日报`;
}

async function loadReport(date) {
  const item = state.manifest.find((entry) => entry.date === date) ?? state.manifest[0];
  if (!item) {
    showLoading(false);
    showMessage("empty-state", "暂无可展示的日报。");
    return;
  }

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
      elements.reportCount.textContent = "0 篇日报";
      showLoading(false);
      renderDateSwitcher();
      showMessage("empty-state", "还没有可展示的日报，等下一次生成后这里会自动更新。");
      return;
    }

    elements.reportCount.textContent = `${state.manifest.length} 篇日报`;
    const targetDate = state.manifest.some((item) => item.date === getHashDate())
      ? getHashDate()
      : state.manifest[0].date;
    if (getHashDate() !== targetDate) {
      setHashDate(targetDate);
      return;
    }
    await loadReport(targetDate);
  } catch (error) {
    console.error(error);
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

// --- Search Functionality ---
let searchDebounceTimeout = null;

function openSearch() {
  closeDateSwitcher();
  elements.searchModal.hidden = false;
  elements.searchInput.focus();
  prefetchAllReports();
}

function closeSearch() {
  elements.searchModal.hidden = true;
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
loadManifest();
