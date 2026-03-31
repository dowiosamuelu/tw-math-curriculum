/**
 * Main application: DOM rendering, events, and state management.
 */

(async function () {
  // --- State ---
  let currentType = "content"; // "content", "performance", or "competency"
  let activeDomains = []; // for content/performance
  let activeAspects = []; // for competency (A, B, C)

  // --- DOM refs ---
  const $tabs = document.getElementById("tabs");
  const $stageSelect = document.getElementById("stage-select");
  const $gradeSelect = document.getElementById("grade-select");
  const $gradeGroup = document.getElementById("grade-filter-group");
  const $searchInput = document.getElementById("search-input");
  const $domainChips = document.getElementById("domain-chips");
  const $results = document.getElementById("results");
  const $resultsCount = document.getElementById("results-count");
  const $btnClear = document.getElementById("btn-clear");
  const $version = document.getElementById("data-version");

  // --- Init ---
  await CurriculumData.load();
  $version.textContent = "v" + CurriculumData.getVersion();

  // Restore state from hash or use defaults
  const hashFilters = CurriculumSearch.fromHash(location.hash);
  if (hashFilters.type) {
    currentType = hashFilters.type;
  }
  if (hashFilters.stage) $stageSelect.value = String(hashFilters.stage);
  if (hashFilters.query) $searchInput.value = hashFilters.query;
  if (hashFilters.domains) activeDomains = hashFilters.domains;

  updateTabs();
  renderChips();
  renderGradeOptions();
  if (hashFilters.grade) $gradeSelect.value = String(hashFilters.grade);
  renderResults();

  // --- Events ---
  $tabs.addEventListener("click", (e) => {
    const btn = e.target.closest(".tab");
    if (!btn) return;
    currentType = btn.dataset.type;
    activeDomains = [];
    activeAspects = [];
    updateTabs();
    renderChips();
    renderGradeOptions();
    renderResults();
  });

  $stageSelect.addEventListener("change", () => {
    renderGradeOptions();
    renderResults();
  });
  $gradeSelect.addEventListener("change", () => renderResults());

  let searchTimeout;
  $searchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(renderResults, 150);
  });

  $btnClear.addEventListener("click", () => {
    $stageSelect.value = "";
    $gradeSelect.value = "";
    $searchInput.value = "";
    activeDomains = [];
    activeAspects = [];
    renderChips();
    renderGradeOptions();
    renderResults();
  });

  $domainChips.addEventListener("click", (e) => {
    const chip = e.target.closest(".domain-chip");
    if (!chip) return;
    const val = chip.dataset.domain || chip.dataset.aspect;
    if (currentType === "competency") {
      const idx = activeAspects.indexOf(val);
      if (idx >= 0) activeAspects.splice(idx, 1);
      else activeAspects.push(val);
    } else {
      const idx = activeDomains.indexOf(val);
      if (idx >= 0) activeDomains.splice(idx, 1);
      else activeDomains.push(val);
    }
    chip.classList.toggle("active");
    renderResults();
  });

  window.addEventListener("hashchange", () => {
    const f = CurriculumSearch.fromHash(location.hash);
    if (f.type && f.type !== currentType) {
      currentType = f.type;
      updateTabs();
      renderChips();
    }
    if (f.stage) $stageSelect.value = String(f.stage);
    if (f.grade) $gradeSelect.value = String(f.grade);
    if (f.query) $searchInput.value = f.query;
    if (f.domains) {
      activeDomains = f.domains;
      renderChips();
    }
    renderResults();
  });

  // --- Render functions ---
  function updateTabs() {
    for (const tab of $tabs.querySelectorAll(".tab")) {
      tab.classList.toggle("active", tab.dataset.type === currentType);
    }
    // Show/hide grade filter
    $gradeGroup.style.display = currentType === "content" ? "" : "none";
    // Show/hide stage filter (not applicable to competency which uses education level)
    $stageSelect.closest(".filter-group").style.display = currentType === "competency" ? "none" : "";
  }

  function renderChips() {
    if (currentType === "competency") {
      const aspects = [
        { code: "A", name: "自主行動" },
        { code: "B", name: "溝通互動" },
        { code: "C", name: "社會參與" },
      ];
      $domainChips.innerHTML = aspects.map(a => {
        const isActive = activeAspects.includes(a.code) ? " active" : "";
        return `<button class="domain-chip aspect-chip${isActive}" data-aspect="${a.code}">${a.code} ${a.name}</button>`;
      }).join("");
    } else {
      const domains = CurriculumData.getDomains(currentType);
      $domainChips.innerHTML = domains.map(d => {
        const isActive = activeDomains.includes(d.code) ? " active" : "";
        return `<button class="domain-chip${isActive}" data-domain="${d.code}">${d.code} ${d.name}</button>`;
      }).join("");
    }
  }

  function renderGradeOptions() {
    if (currentType !== "content") return;

    const stage = $stageSelect.value ? parseInt($stageSelect.value, 10) : null;
    const stageGradeMap = { 1: [1, 2], 2: [3, 4], 3: [5, 6], 4: [7, 8, 9], 5: [10, 11, 12] };
    const grades = stage ? stageGradeMap[stage] : CurriculumData.getGrades();

    const current = $gradeSelect.value;
    $gradeSelect.innerHTML = '<option value="">全部</option>' +
      grades.map(g => `<option value="${g}">${g} 年級</option>`).join("");

    if (grades.includes(parseInt(current, 10))) {
      $gradeSelect.value = current;
    }
  }

  function getFilters() {
    const filters = { type: currentType };
    if (currentType !== "competency" && $stageSelect.value) {
      filters.stage = parseInt($stageSelect.value, 10);
    }
    if ($gradeSelect.value && currentType === "content") {
      filters.grade = parseInt($gradeSelect.value, 10);
    }
    if (activeDomains.length > 0 && currentType !== "competency") {
      filters.domains = activeDomains;
    }
    if (activeAspects.length > 0 && currentType === "competency") {
      filters.aspects = activeAspects;
    }
    if ($searchInput.value.trim()) filters.query = $searchInput.value.trim();
    return filters;
  }

  function renderResults() {
    const filters = getFilters();
    let items;
    if (currentType === "content") {
      items = CurriculumData.getContentItems();
    } else if (currentType === "performance") {
      items = CurriculumData.getPerformanceItems();
    } else {
      items = CurriculumData.getCompetencyItems();
    }

    const filtered = CurriculumSearch.filter(items, filters);

    // Update hash
    const newHash = CurriculumSearch.toHash(filters);
    if (newHash !== location.hash && newHash !== "#") {
      history.replaceState(null, "", newHash || location.pathname);
    }

    // Count
    $resultsCount.textContent = `${filtered.length} / ${items.length} items`;

    // Render cards
    if (filtered.length === 0) {
      $results.innerHTML = '<p style="text-align:center;color:var(--color-text-secondary);padding:40px 0;">No results / 查無結果</p>';
      return;
    }

    let html;
    if (currentType === "content") {
      html = filtered.map(renderContentCard).join("");
    } else if (currentType === "performance") {
      html = filtered.map(renderPerformanceCard).join("");
    } else {
      html = filtered.map(renderCompetencyCard).join("");
    }
    $results.innerHTML = html;

    // Attach ref-link click events
    $results.addEventListener("click", handleRefClick);
  }

  function renderContentCard(item) {
    const classLabel = item.class_type
      ? `<span class="badge badge-class">${item.class_type === "A" ? "甲" : "乙"}</span>`
      : "";

    const remarksHtml = item.remarks
      ? `<details class="card-meta"><summary>備註 Remarks</summary><div class="card-meta-content">${esc(item.remarks)}</div></details>`
      : "";

    const aidsHtml = item.teaching_aids
      ? `<details class="card-meta"><summary>教具 Teaching Aids</summary><div class="card-meta-content">${esc(item.teaching_aids)}</div></details>`
      : "";

    const refsHtml = (item.related_performance && item.related_performance.length > 0)
      ? `<div class="card-refs">
          <span class="card-refs-label">學習表現:</span>
          ${item.related_performance.map(code =>
            `<span class="ref-link" data-ref="${code}" data-ref-type="performance">${code}</span>`
          ).join("")}
        </div>`
      : "";

    const issueUrl = `https://github.com/SammyLu/tw-math-curriculum/issues/new?template=data_correction.md&title=${encodeURIComponent("[Data] " + item.code)}`;

    return `
      <div class="card" data-domain="${item.domain}">
        <div class="card-header">
          <span class="card-code">${esc(item.code)}</span>
          <span class="card-title">${esc(item.title)}</span>
          <span class="badge badge-domain" data-domain="${item.domain}">${item.domain} ${esc(item.domain_name)}</span>
          <span class="badge badge-stage">${item.grade}年級</span>
          ${classLabel}
        </div>
        <div class="card-body">
          ${item.description ? `<p class="card-description">${esc(item.description)}</p>` : ""}
          ${remarksHtml}
          ${aidsHtml}
          ${refsHtml}
        </div>
        <div class="card-report"><a href="${issueUrl}" target="_blank" rel="noopener">回報錯誤</a></div>
      </div>`;
  }

  function renderPerformanceCard(item) {
    const relatedContent = CurriculumData.getRelatedContent(item.code);
    const refsHtml = relatedContent.length > 0
      ? `<div class="card-refs">
          <span class="card-refs-label">相關學習內容:</span>
          ${relatedContent.map(c =>
            `<span class="ref-link" data-ref="${c.code}" data-ref-type="content">${c.code}</span>`
          ).join("")}
        </div>`
      : "";

    const stageLabels = { 1: "I", 2: "II", 3: "III", 4: "IV", 5: "V" };
    const issueUrl = `https://github.com/SammyLu/tw-math-curriculum/issues/new?template=data_correction.md&title=${encodeURIComponent("[Data] " + item.code)}`;

    return `
      <div class="card" data-domain="${item.domain}">
        <div class="card-header">
          <span class="card-code">${esc(item.code)}</span>
          <span class="badge badge-domain" data-domain="${item.domain}">${item.domain} ${esc(item.domain_name)}</span>
          <span class="badge badge-stage">Stage ${stageLabels[item.stage] || item.stage}</span>
        </div>
        <div class="card-body">
          <p class="card-description">${esc(item.description)}</p>
          ${refsHtml}
        </div>
        <div class="card-report"><a href="${issueUrl}" target="_blank" rel="noopener">回報錯誤</a></div>
      </div>`;
  }

  function renderCompetencyCard(item) {
    const aspectColors = { A: "var(--domain-N)", B: "var(--domain-S)", C: "var(--domain-A)" };
    const levelLabels = { E: "國小", J: "國中", "S-U": "高中" };
    const issueUrl = `https://github.com/SammyLu/tw-math-curriculum/issues/new?template=data_correction.md&title=${encodeURIComponent("[Data] " + item.code)}`;

    return `
      <div class="card" style="border-left-color: ${aspectColors[item.aspect] || "var(--color-border)"}">
        <div class="card-header">
          <span class="card-code">${esc(item.code)}</span>
          <span class="badge" style="background:${aspectColors[item.aspect]};color:#fff">${item.aspect} ${esc(item.aspect_name)}</span>
          <span class="badge badge-stage">${esc(item.item)} ${esc(item.item_name)}</span>
          <span class="badge badge-class">${levelLabels[item.level] || item.level}</span>
        </div>
        <div class="card-body">
          <p class="card-description">${esc(item.description)}</p>
        </div>
        <div class="card-report"><a href="${issueUrl}" target="_blank" rel="noopener">回報錯誤</a></div>
      </div>`;
  }

  function handleRefClick(e) {
    const link = e.target.closest(".ref-link");
    if (!link) return;
    e.preventDefault();

    const refCode = link.dataset.ref;
    const refType = link.dataset.refType;

    // Switch tab and search for the code
    currentType = refType;
    activeDomains = [];
    activeAspects = [];
    $stageSelect.value = "";
    $gradeSelect.value = "";
    $searchInput.value = refCode;

    updateTabs();
    renderChips();
    renderGradeOptions();
    renderResults();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function esc(str) {
    if (!str) return "";
    const el = document.createElement("span");
    el.textContent = str;
    return el.innerHTML;
  }
})();
