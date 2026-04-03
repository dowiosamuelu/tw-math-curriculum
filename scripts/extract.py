"""
Extract Taiwan 12-Year Math Curriculum (108課綱) from official PDF into structured JSON.

Source: Ministry of Education official PDF
Output: docs/data/learning_performance.json, docs/data/learning_content.json

Usage:
    python scripts/extract.py
    (run from the project root directory)
"""

import json
import os
import re
from datetime import date

import pdfplumber

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PDF_PATH = os.path.join(PROJECT_ROOT, "source.pdf")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "docs", "data")
VERSION_FILE = os.path.join(PROJECT_ROOT, "VERSION")

# Domain mapping
DOMAIN_MAP = {
    "N": "數與量", "n": "數與量",
    "S": "空間與形狀", "s": "空間與形狀",
    "G": "坐標幾何", "g": "坐標幾何",
    "R": "關係", "r": "關係",
    "A": "代數", "a": "代數",
    "F": "函數", "f": "函數",
    "D": "資料與不確定性", "d": "資料與不確定性",
}

# Stage mapping by grade
def get_stage(grade):
    if grade <= 2: return 1
    if grade <= 4: return 2
    if grade <= 6: return 3
    if grade <= 9: return 4
    return 5

# Stage name mapping
STAGE_NAMES = {
    1: "第一學習階段（國小低年級）",
    2: "第二學習階段（國小中年級）",
    3: "第三學習階段（國小高年級）",
    4: "第四學習階段（國中）",
    5: "第五學習階段（高中）",
}

def clean_text(text):
    """Clean extracted text: normalize whitespace, remove line breaks within content."""
    if not text:
        return ""
    text = text.replace("\n", "")
    text = re.sub(r"\s+", "", text)
    return text.strip()

def clean_text_keep_spaces(text):
    """Clean but keep meaningful spacing for readability."""
    if not text:
        return ""
    # Replace newlines with nothing (PDF wrapping)
    text = text.replace("\n", "")
    return text.strip()


def parse_content_code(code):
    """Parse code like N-5-3, N-11A-1, F-12甲-3 into components."""
    # Standard: N-5-3
    m = re.match(r"^([A-Z])-(\d+)-(\d+)$", code)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3)), ""

    # With class suffix: N-11A-1, G-11B-2
    m = re.match(r"^([A-Z])-(\d+)([AB])-(\d+)$", code)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(4)), m.group(3)

    # With Chinese class: F-12甲-3, F-12乙-2
    m = re.match(r"^([A-Z])-(\d+)([甲乙])-(\d+)$", code)
    if m:
        class_map = {"甲": "A", "乙": "B"}
        return m.group(1), int(m.group(2)), int(m.group(4)), class_map.get(m.group(3), m.group(3))

    return None, None, None, None


def parse_performance_code(code):
    """Parse performance code like n-III-3 into components."""
    roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
    m = re.match(r"^([a-z])-([IVX]+)-(\d+)$", code)
    if m:
        domain_letter = m.group(1)
        stage = roman_map.get(m.group(2))
        seq = int(m.group(3))
        return domain_letter, stage, seq
    return None, None, None


def split_title_description(text):
    """Split '標題：說明內容' into (title, description)."""
    # Try splitting on first colon (full-width or half-width)
    for sep in ["：", ":"]:
        idx = text.find(sep)
        if idx > 0 and idx < 30:  # title should be short
            return text[:idx].strip(), text[idx+1:].strip()
    # No colon found, entire text is the title
    return text, ""


# Codes whose title lacks specificity — the first sentence of description
# (before the first 。) is actually part of the bold title in the original PDF,
# but pdfplumber cannot detect bold in this document (single font, uniform
# stroke width).  We merge description's first sentence back into the title.
TITLE_MERGE_CODES = {
    "N-1-4", "N-2-3", "N-2-4", "N-2-5", "N-2-6", "N-2-8", "N-2-9",
    "N-2-11", "N-2-14",
    "N-3-6", "N-3-7", "N-3-8", "N-3-12", "N-3-14", "N-3-15", "N-3-16",
    "N-3-17",
    "N-4-3", "N-4-4", "N-4-9", "N-4-10", "N-4-11", "N-4-13",
    "S-4-1", "S-4-2",
    "N-5-2", "N-5-10", "N-5-11", "N-5-12", "N-5-13", "N-5-14", "N-5-15",
    "N-5-16",
    "N-6-5", "N-6-7", "N-6-8", "N-6-9", "S-6-2", "R-6-4", "D-6-2",
}


def fix_title_specificity(items):
    """Merge first sentence of description into title for items that need it."""
    for item in items:
        if item["code"] not in TITLE_MERGE_CODES:
            continue
        desc = item.get("description", "")
        if not desc:
            continue
        # Split on first 。
        idx = desc.find("。")
        if idx >= 0:
            first_sentence = desc[:idx]
            rest = desc[idx + 1:].strip()
        else:
            first_sentence = desc
            rest = ""
        item["title"] = item["title"] + "：" + first_sentence
        item["description"] = rest


def extract_learning_performance(pdf):
    """Extract learning performance (學習表現) from pages 12-20."""
    results = []
    # Performance code pattern
    perf_pattern = re.compile(r"^[a-z]-[IVX]+-\d+$")

    for page_num in range(11, 21):  # pages 12-21 (0-indexed: 11-20)
        page = pdf.pages[page_num]
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                if not row or not row[0]:
                    continue
                code = clean_text(row[0])
                if perf_pattern.match(code):
                    description = clean_text_keep_spaces(row[1]) if len(row) > 1 and row[1] else ""
                    domain_letter, stage, seq = parse_performance_code(code)
                    if domain_letter:
                        results.append({
                            "code": code,
                            "description": description,
                            "domain": domain_letter,
                            "domain_name": DOMAIN_MAP.get(domain_letter, ""),
                            "stage": stage,
                            "stage_name": STAGE_NAMES.get(stage, ""),
                            "sequence": seq,
                        })
    return results


def extract_learning_content(pdf):
    """Extract learning content (學習內容) from pages 22-56."""
    results = []
    # Content code patterns: N-5-3, N-11A-1, F-12甲-3
    content_pattern = re.compile(r"^[A-Z]-\d+[AB甲乙]?-\d+$")
    # Grade header pattern: "1年級", "11年級（A類）", "12年級（加深加廣選修數學甲）"
    grade_pattern = re.compile(r"^(\d+)年級")

    current_grade = None

    for page_num in range(21, 57):  # pages 22-57 (0-indexed: 21-56)
        page = pdf.pages[page_num]
        tables = page.extract_tables()
        for table in tables:
            # Check header to confirm it's a learning content table
            if not table or not table[0]:
                continue
            header = [clean_text(c) for c in table[0] if c]
            if "學習內容條目及說明" not in "".join(header):
                continue

            for row in table[1:]:  # skip header
                if not row or not row[0]:
                    continue
                first_cell = clean_text(row[0])

                # Check if it's a grade header
                gm = grade_pattern.match(first_cell)
                if gm:
                    current_grade = int(gm.group(1))
                    continue

                # Check if it's a content code
                if content_pattern.match(first_cell):
                    code = first_cell
                    raw_content = clean_text_keep_spaces(row[1]) if len(row) > 1 and row[1] else ""
                    remarks = clean_text_keep_spaces(row[2]) if len(row) > 2 and row[2] else ""
                    teaching_aids = clean_text_keep_spaces(row[3]) if len(row) > 3 and row[3] else ""
                    related_perf_raw = clean_text_keep_spaces(row[4]) if len(row) > 4 and row[4] else ""

                    domain_letter, grade, seq, class_type = parse_content_code(code)

                    # Split title and description
                    title, description = split_title_description(raw_content)

                    # Parse related performance codes
                    related_performance = re.findall(r"[a-z]-[IVX]+-\d+", related_perf_raw)

                    if domain_letter:
                        entry = {
                            "code": code,
                            "title": title,
                            "description": description,
                            "remarks": remarks,
                            "teaching_aids": teaching_aids,
                            "related_performance": related_performance,
                            "domain": domain_letter,
                            "domain_name": DOMAIN_MAP.get(domain_letter, ""),
                            "grade": grade,
                            "stage": get_stage(grade),
                            "stage_name": STAGE_NAMES.get(get_stage(grade), ""),
                            "sequence": seq,
                        }
                        if class_type:
                            entry["class_type"] = class_type  # A or B (選修甲/乙)
                        results.append(entry)

    return results


def extract_core_competencies(pdf):
    """Extract core competencies (核心素養) from pages 7-8.

    Uses table extraction + supplements items lost to merged cells in PDF.
    """
    ASPECT_MAP = {
        "A": "自主行動",
        "B": "溝通互動",
        "C": "社會參與",
    }
    ITEM_MAP = {
        "A1": "身心素質與自我精進",
        "A2": "系統思考與解決問題",
        "A3": "規劃執行與創新應變",
        "B1": "符號運用與溝通表達",
        "B2": "科技資訊與媒體素養",
        "B3": "藝術涵養與美感素養",
        "C1": "道德實踐與公民意識",
        "C2": "人際關係與團隊合作",
        "C3": "多元文化與國際理解",
    }
    LEVEL_MAP = {
        "E": {"name": "國民小學教育", "stage": "elementary"},
        "J": {"name": "國民中學教育", "stage": "junior_high"},
        "S-U": {"name": "普通型高級中等學校教育", "stage": "senior_high"},
    }

    # Code pattern: 數-E-A3, 數-J-B1, 數S-U-C3 (S-U variant has no dash after 數)
    code_re = re.compile(r"(數[-–—]?(?:[EJ]|S-U)[-–—]([ABC]\d))\s*(.*)", re.DOTALL)

    results = []
    seen_codes = set()

    for page_num in [6, 7]:  # pages 7-8
        page = pdf.pages[page_num]
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                if not row:
                    continue
                for cell in row:
                    if not cell or "數" not in cell:
                        continue
                    m = code_re.search(cell)
                    if not m:
                        continue
                    raw_code = m.group(1)
                    item_key = m.group(2)
                    desc_raw = m.group(3)

                    # Normalize code: ensure dash after 數
                    code = raw_code.replace("–", "-").replace("—", "-")
                    if not code.startswith("數-"):
                        code = "數-" + code[1:]

                    if code in seen_codes:
                        continue
                    seen_codes.add(code)

                    description = desc_raw.replace("\n", "").strip()

                    # Parse level from code: 數-E-A3 or 數-S-U-A3
                    parts = code.split("-")
                    if len(parts) == 3:
                        level_key = parts[1]
                    elif len(parts) == 4:
                        level_key = parts[1] + "-" + parts[2]
                    else:
                        continue

                    aspect_key = item_key[0]
                    level_info = LEVEL_MAP.get(level_key, {})
                    results.append({
                        "code": code,
                        "description": description,
                        "aspect": aspect_key,
                        "aspect_name": ASPECT_MAP.get(aspect_key, ""),
                        "item": item_key,
                        "item_name": ITEM_MAP.get(item_key, ""),
                        "level": level_key,
                        "level_name": level_info.get("name", ""),
                        "education_stage": level_info.get("stage", ""),
                    })

    # Items lost to PDF merged cells (A1, A2) — transcribed from official document
    manual_items = [
        ("數-E-A1", "A1", "E",
         "具備個人生活所需的基本數學概念，對數學的學習有正向的情感與態度。"),
        ("數-J-A1", "A1", "J",
         "對於學習數學有更多元的想法，嘗試探索更廣泛的數學知識，積極正向地探究數學的內涵。"),
        ("數-S-U-A1", "A1", "S-U",
         "具備對數學領域的學習動力及自主管理，將所學與生活連結，並能從不同的角度反思學習歷程與結果。"),
        ("數-E-A2", "A2", "E",
         "具備基本的算術操作能力、並能指認基本的形體與相對關係，在日常生活情境中，用數學表述與解決問題。"),
        ("數-J-A2", "A2", "J",
         "具備有理數、根式、坐標系之運作能力，並能以符號代表數或幾何物件，執行運算與推論，在生活情境或可理解的想像情境中，分析本質以解決問題。"),
        ("數-S-U-A2", "A2", "S-U",
         "具備數學模型的基本工具，以數學模型解決典型的現實問題。了解數學在觀察歸納之後還須演繹證明的思維特徵及其價值。"),
    ]

    for code, item_key, level_key, description in manual_items:
        if code in seen_codes:
            continue
        aspect_key = item_key[0]
        level_info = LEVEL_MAP.get(level_key, {})
        results.append({
            "code": code,
            "description": description,
            "aspect": aspect_key,
            "aspect_name": ASPECT_MAP.get(aspect_key, ""),
            "item": item_key,
            "item_name": ITEM_MAP.get(item_key, ""),
            "level": level_key,
            "level_name": level_info.get("name", ""),
            "education_stage": level_info.get("stage", ""),
        })

    results.sort(key=lambda x: x["code"])
    return results


def read_version():
    """Read version from VERSION file."""
    try:
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"


def wrap_data(items, version, data_type):
    """Wrap items in a versioned envelope."""
    return {
        "version": version,
        "source": "十二年國民基本教育課程綱要—數學領域",
        "source_url": "https://www.k12ea.gov.tw",
        "data_type": data_type,
        "extracted_at": date.today().isoformat(),
        "count": len(items),
        "items": items,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    version = read_version()

    pdf = pdfplumber.open(PDF_PATH)
    print(f"PDF loaded: {len(pdf.pages)} pages")
    print(f"Data version: {version}")

    # Extract learning performance
    performance = extract_learning_performance(pdf)
    print(f"Learning performance items extracted: {len(performance)}")

    perf_output = os.path.join(OUTPUT_DIR, "learning_performance.json")
    with open(perf_output, "w", encoding="utf-8") as f:
        json.dump(wrap_data(performance, version, "learning_performance"), f, ensure_ascii=False, indent=2)

    # Extract learning content
    content = extract_learning_content(pdf)
    print(f"Learning content items extracted: {len(content)}")

    # Fix titles that lack specificity (bold boundary not detectable in PDF)
    fix_title_specificity(content)
    print(f"Title specificity fixes applied: {len(TITLE_MERGE_CODES)} items")

    content_output = os.path.join(OUTPUT_DIR, "learning_content.json")
    with open(content_output, "w", encoding="utf-8") as f:
        json.dump(wrap_data(content, version, "learning_content"), f, ensure_ascii=False, indent=2)

    # Extract core competencies
    competencies = extract_core_competencies(pdf)
    print(f"Core competency items extracted: {len(competencies)}")

    comp_output = os.path.join(OUTPUT_DIR, "core_competencies.json")
    with open(comp_output, "w", encoding="utf-8") as f:
        json.dump(wrap_data(competencies, version, "core_competencies"), f, ensure_ascii=False, indent=2)

    # Print summary
    print("\n--- Summary ---")
    print("Learning Performance by stage:")
    for s in range(1, 6):
        items = [p for p in performance if p["stage"] == s]
        print(f"  Stage {s}: {len(items)} items")

    print("\nLearning Content by grade:")
    for g in range(1, 13):
        items = [c for c in content if c["grade"] == g]
        if items:
            print(f"  Grade {g}: {len(items)} items")

    print("\nLearning Content by domain:")
    for d in ["N", "S", "G", "R", "A", "F", "D"]:
        items = [c for c in content if c["domain"] == d]
        if items:
            print(f"  {d} ({DOMAIN_MAP[d]}): {len(items)} items")

    print(f"\nOutput written to {OUTPUT_DIR}/")
    pdf.close()


if __name__ == "__main__":
    main()
