# Contributing / 貢獻指南

Thank you for your interest in improving this dataset!

感謝你有興趣改善這份資料！

## Reporting Data Errors / 回報資料錯誤

This is the most valuable contribution. If you find an item that doesn't match the official PDF:

1. Open a **Data Correction** issue
2. Include: the item code (e.g. `N-5-3`), the current (incorrect) value, the expected value, and the PDF page number if possible

這是最有價值的貢獻方式。如果你發現資料與官方 PDF 不符：

1. 使用 **Data Correction** issue 模板
2. 提供：指標編碼（如 `N-5-3`）、目前的錯誤值、正確值、以及 PDF 頁碼（如果方便的話）

## Regenerating Data / 重新產生資料

```bash
# Install dependencies
pip install pdfplumber

# Run extraction (from project root)
python scripts/extract.py
```

The script reads `source.pdf` and outputs to `docs/data/`.

## Contributing to the Website / 貢獻網站

The website is plain HTML/CSS/JS in `docs/`. No build step required. Open `docs/index.html` in a browser to preview.

## Pull Requests

- Keep changes focused and small
- For data corrections, reference the issue number
- For website changes, test on both desktop and mobile
