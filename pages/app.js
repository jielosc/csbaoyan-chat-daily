const state = {
  manifest: [],
  activeDate: null,
};

const elements = {
  archiveList: document.querySelector("#archive-list"),
  reportCount: document.querySelector("#report-count"),
  activeDateLabel: document.querySelector("#active-date-label"),
  loadingState: document.querySelector("#loading-state"),
  reportContent: document.querySelector("#report-content"),
  themeToggle: document.querySelector("#theme-toggle"),
};

function updateThemeIcon(theme) {
  if (!elements.themeToggle) return;
  const isDark = theme === 'dark';
  elements.themeToggle.querySelector('.icon-sun').style.display = isDark ? 'none' : 'block';
  elements.themeToggle.querySelector('.icon-moon').style.display = isDark ? 'block' : 'none';
}

function initTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  updateThemeIcon(currentTheme);

  if (elements.themeToggle) {
    elements.themeToggle.addEventListener('click', () => {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const newTheme = isDark ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      updateThemeIcon(newTheme);
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

function renderArchive() {
  if (!state.manifest.length) {
    elements.archiveList.innerHTML = '<div class="empty-state">暂无可展示的日报。</div>';
    return;
  }

  elements.archiveList.innerHTML = state.manifest
    .map((item) => {
      const isActive = item.date === state.activeDate;
      return `
        <button class="archive-item${isActive ? " active" : ""}" data-date="${item.date}" type="button" aria-pressed="${isActive}">
          <span class="archive-date">${formatDate(item.date)}</span>
        </button>
      `;
    })
    .join("");

  for (const button of elements.archiveList.querySelectorAll(".archive-item")) {
    button.addEventListener("click", () => {
      const { date } = button.dataset;
      if (date) {
        setHashDate(date);
      }
    });
  }
}

function updateHeader(item) {
  elements.activeDateLabel.textContent = `日报日期 ${formatDate(item.date)}`;
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
  renderArchive();
  updateHeader(item);
  showLoading(true);

  try {
    if (!item.md_path) {
      throw new Error("Missing report path");
    }

    const response = await fetch(`./data/${item.md_path}`, { cache: "no-store" });
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
      renderArchive();
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
    elements.archiveList.innerHTML = '<div class="error-state">归档索引加载失败。</div>';
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

initTheme();
loadManifest();
