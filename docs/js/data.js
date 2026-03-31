/**
 * Data loading and indexing for tw-math-curriculum.
 * Fetches JSON files and builds reverse index for cross-referencing.
 */

const CurriculumData = (() => {
  let contentData = null;
  let performanceData = null;
  let competencyData = null;
  let reverseIndex = {}; // performance code -> [content items]
  let version = "";

  async function load() {
    const [contentRes, perfRes, compRes] = await Promise.all([
      fetch("data/learning_content.json"),
      fetch("data/learning_performance.json"),
      fetch("data/core_competencies.json"),
    ]);

    const contentJson = await contentRes.json();
    const perfJson = await perfRes.json();
    const compJson = await compRes.json();

    contentData = contentJson.items;
    performanceData = perfJson.items;
    competencyData = compJson.items;
    version = contentJson.version;

    buildReverseIndex();
    return { contentData, performanceData, competencyData, version };
  }

  function buildReverseIndex() {
    reverseIndex = {};
    for (const item of contentData) {
      for (const perfCode of item.related_performance || []) {
        if (!reverseIndex[perfCode]) {
          reverseIndex[perfCode] = [];
        }
        reverseIndex[perfCode].push(item);
      }
    }
  }

  function getContentItems() {
    return contentData || [];
  }

  function getPerformanceItems() {
    return performanceData || [];
  }

  function getCompetencyItems() {
    return competencyData || [];
  }

  function getRelatedContent(performanceCode) {
    return reverseIndex[performanceCode] || [];
  }

  function getVersion() {
    return version;
  }

  // Collect unique domains from a dataset
  function getDomains(type) {
    const items = type === "content" ? contentData : performanceData;
    if (!items) return [];
    const seen = new Map();
    for (const item of items) {
      if (!seen.has(item.domain)) {
        seen.set(item.domain, item.domain_name);
      }
    }
    return Array.from(seen.entries()).map(([code, name]) => ({ code, name }));
  }

  // Collect unique grades from content data
  function getGrades() {
    if (!contentData) return [];
    const grades = new Set();
    for (const item of contentData) {
      grades.add(item.grade);
    }
    return Array.from(grades).sort((a, b) => a - b);
  }

  return { load, getContentItems, getPerformanceItems, getCompetencyItems, getRelatedContent, getVersion, getDomains, getGrades };
})();
