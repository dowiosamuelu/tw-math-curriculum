# tw-math-curriculum

Taiwan's 12-Year Basic Education Math Curriculum (108 課綱) as structured, machine-readable JSON.

台灣十二年國民基本教育數學領域課程綱要，結構化 JSON 格式。

**[Live Browser / 線上瀏覽 →](https://dowiosamuelu.github.io/tw-math-curriculum)** *(coming soon)*

## Why / 為什麼做這個

The official curriculum is published only as an 83-page PDF. This project extracts it into structured data for:

- AI applications (RAG, tutoring systems, curriculum analysis)
- Education technology development
- Community-driven verification and discussion

官方課綱只有 PDF 格式。本專案將其轉為結構化資料，方便 AI 應用、教育科技開發、以及社群校對討論。

## Data Overview / 資料概覽

| Category                        | Count     |
| ------------------------------- | --------- |
| Learning Content (學習內容)     | 288 items |
| Learning Performance (學習表現) | 262 items |
| Grades (年級)                   | 1-12      |
| Domains (主題)                  | 7         |

**Domains**: N 數與量 / S 空間與形狀 / G 坐標幾何 / R 關係 / A 代數 / F 函數 / D 資料與不確定性

## Schema / 資料格式

Each JSON file is wrapped in a versioned envelope:

```json
{
  "version": "1.0.0",
  "source": "十二年國民基本教育課程綱要—數學領域",
  "extracted_at": "2026-03-31",
  "count": 288,
  "items": [...]
}
```

### Learning Content Item (學習內容)

```json
{
  "code": "N-5-3",
  "title": "公因數和公倍數",
  "description": "因數、倍數、公因數、公倍數、最大公因數、最小公倍數的意義。",
  "remarks": "以概念認識為主，不用短除法（N-6-1、N-6-2）。",
  "teaching_aids": "",
  "related_performance": ["n-III-3"],
  "domain": "N",
  "domain_name": "數與量",
  "grade": 5,
  "stage": 3,
  "stage_name": "第三學習階段（國小高年級）",
  "sequence": 3
}
```

Grades 11-12 items include an additional `"class_type": "A"` or `"B"` field (corresponding to 選修甲/乙).

### Learning Performance Item (學習表現)

```json
{
  "code": "n-III-3",
  "description": "認識因數、倍數、質數、最大公因數、最小公倍數的意義、計算與應用。",
  "domain": "n",
  "domain_name": "數與量",
  "stage": 3,
  "stage_name": "第三學習階段（國小高年級）",
  "sequence": 3
}
```

## Quick Start / 快速開始

### Use the data directly

```python
import json

with open("docs/data/learning_content.json", encoding="utf-8") as f:
    data = json.load(f)

for item in data["items"]:
    if item["grade"] == 5 and item["domain"] == "N":
        print(f'{item["code"]} {item["title"]}')
```

### Regenerate from source PDF

```bash
pip install pdfplumber
python scripts/extract.py
```

## Data Source & Copyright / 資料來源與版權

- **Source**: [十二年國民基本教育課程綱要—數學領域 (PDF)](https://www.k12ea.gov.tw), Ministry of Education, Taiwan
- **Copyright**: The official curriculum is exempt from copyright protection under [Taiwan Copyright Act Article 9](https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=J0070017&flno=9) (government orders and official documents).
- **License**: The code and website in this repository are released under the [MIT License](LICENSE).

## Contributing / 貢獻

See [CONTRIBUTING.md](CONTRIBUTING.md). Data corrections are especially welcome — use the [Data Correction](../../issues/new?template=data_correction.md) issue template.

## Versioning / 版本

Data follows semantic versioning. See [CHANGELOG.md](CHANGELOG.md).

Current version: see [`VERSION`](VERSION)
