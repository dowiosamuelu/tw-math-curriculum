/**
 * Search and filter logic for tw-math-curriculum.
 * Pure functions, no DOM access.
 */

const CurriculumSearch = (() => {

  /**
   * Filter items based on criteria.
   * @param {Array} items - data items
   * @param {Object} filters - { stage, grade, domains, query, type }
   * @returns {Array} filtered items
   */
  function filter(items, filters) {
    return items.filter(item => {
      // Stage filter
      if (filters.stage && item.stage !== undefined && item.stage !== filters.stage) {
        return false;
      }

      // Education level filter (for competency)
      if (filters.level && item.education_stage && item.education_stage !== filters.level) {
        return false;
      }

      // Grade filter (only for content)
      if (filters.grade && item.grade !== undefined && item.grade !== filters.grade) {
        return false;
      }

      // Domain filter (multiple selection, for content/performance)
      if (filters.domains && filters.domains.length > 0) {
        if (item.domain && !filters.domains.includes(item.domain)) {
          return false;
        }
      }

      // Aspect filter (for competency)
      if (filters.aspects && filters.aspects.length > 0) {
        if (item.aspect && !filters.aspects.includes(item.aspect)) {
          return false;
        }
      }

      // Text search
      if (filters.query) {
        const q = filters.query.toLowerCase();
        const searchable = [
          item.code,
          item.title || "",
          item.description || "",
          item.remarks || "",
          item.item_name || "",
          item.aspect_name || "",
        ].join(" ").toLowerCase();

        if (!searchable.includes(q)) {
          return false;
        }
      }

      return true;
    });
  }

  /**
   * Encode current filter state to URL hash.
   */
  function toHash(filters) {
    const params = new URLSearchParams();
    if (filters.type) params.set("type", filters.type);
    if (filters.stage) params.set("stage", String(filters.stage));
    if (filters.grade) params.set("grade", String(filters.grade));
    if (filters.domains && filters.domains.length > 0) {
      params.set("domains", filters.domains.join(","));
    }
    if (filters.query) params.set("q", filters.query);
    return params.toString() ? "#" + params.toString() : "";
  }

  /**
   * Decode URL hash to filter state.
   */
  function fromHash(hash) {
    const str = hash.startsWith("#") ? hash.slice(1) : hash;
    if (!str) return {};
    const params = new URLSearchParams(str);
    const filters = {};
    if (params.has("type")) filters.type = params.get("type");
    if (params.has("stage")) filters.stage = parseInt(params.get("stage"), 10);
    if (params.has("grade")) filters.grade = parseInt(params.get("grade"), 10);
    if (params.has("domains")) filters.domains = params.get("domains").split(",");
    if (params.has("q")) filters.query = params.get("q");
    return filters;
  }

  return { filter, toHash, fromHash };
})();
