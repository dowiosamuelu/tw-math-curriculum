# 概念圖譜：關聯機制與視覺化改版 — 背景交接文件

## 專案概述

`tw-math-curriculum` 是台灣 108 數學課綱的結構化資料專案。288 個學習內容條目已擷取為 JSON，並建構了概念圖譜（`concept_graph.json`）。

目前圖譜有 74 條邊（4 same_topic + 70 reference），全部來自課綱文字中的明確交叉引用。

## 待辦：兩件事

### 一、新增第三種關聯類型：共用學習表現

**背景**：每個學習內容條目對應 1~N 個學習表現（`related_performance` 欄位）。當兩個條目共用同一個學習表現時，代表它們對應相同的能力指標 — 這是課綱本身定義的對應關係，不是推測。

**資料分析結果**：
- 99 個學習表現被 2 個以上的學習內容共用，產生 578 對潛在關聯
- 品質有好有壞：
  - 好：`a-IV-2` 連結 A-7-2「一元一次方程式的意義」和 A-7-3「解法與應用」
  - 好：`d-I-1` 連結 D-1-1「簡單分類」→ D-2-1「分類與呈現」（跨年級）
  - 差：group size 太大的（如 n-II-6 連結十幾個「解題」條目）沒有辨別力
- group size 分布：2 items=41 groups, 3=26, 4=14, 5=8, 6+=9

**已達成共識**：
- 加入「共用學習表現」作為第三種邊類型
- 需要過濾：group size 過大的要排除（具體閾值待定，建議 ≤5）
- 可考慮只保留跨年級的配對（同年級同領域的關聯比較 obvious）
- 實作位置：`scripts/build_graph.py`

**相關資料路徑**：
- `docs/data/learning_content.json` — 每個 item 有 `related_performance` 陣列
- `docs/data/learning_performance.json` — 學習表現完整資料
- `docs/data/concept_graph.json` — 圖譜輸出（nodes + edges）

### 二、視覺化從 grid 改為聚焦式探索（方案 A）

**問題**：現有 `docs/graph/index.html` 是 grid layout（X=年級, Y=領域），一次顯示 288 個節點，密密麻麻，而且 69% 的節點（199/288）沒有任何邊。

**已達成共識的方案 A**：
- 不預設顯示 288 個點
- 起始畫面：搜尋框 + 學習階段/年級/領域篩選
- 選定一個條目後，以它為中心，只顯示它 + 所有直接關聯的節點
- 每個節點是卡片（編碼 + 標題），不只是一個點
- 卡片依年級左右排列，保留時間軸方向感
- 右側 info panel 保留，顯示完整說明/備註/關聯
- 使用者可以點擊鄰居節點繼續探索

**三種邊的視覺設計**（之前已實作的風格可參考）：
- `same_topic`：紫色實線，無箭頭（雙向）
- `reference`：灰色虛線，有箭頭
- `shared_performance`（新）：待設計，建議橘色或其他可區分的樣式

## 技術堆疊

- 資料處理：Python (`scripts/extract.py`, `scripts/build_graph.py`)
- 視覺化：原生 HTML + D3.js v7，部署於 GitHub Pages (`docs/` 目錄)
- 無 build step，無框架

## 目前的邊類型定義（concept_graph.json）

```json
{
  "same_topic": "同一主題跨領域出現（如 N-1-5 與 S-1-1 皆為「長度」）",
  "reference": "課綱文字中的交叉引用（附原文，語意待人工標註）"
}
```

每條邊的結構：
```json
{
  "source": "N-5-3",
  "target": "N-6-1",
  "type": "reference",
  "field": "remarks",
  "evidence": "…不用短除法（N-6-1、N-6-2）…",
  "directed": true  // same_topic 為 false
}
```

## 重要的設計原則（使用者多次強調）

1. **只用有證據的關係** — 不做推測或推論。sequential edges（年級遞進）被否決過，因為「不一定」。
2. **same_topic 判定嚴格** — 只有 title 或 description 中出現「同XXX」才算，備註中的「同X備註」不算。
3. **保留原文證據** — reference 邊附上原文 snippet，讓使用者自行判讀語意。
4. **使用者是數學教育專家** — 重視資料準確度，不需要過度簡化。

## 剛完成的工作（本次對話）

- 修正了 40 個條目的標題切分問題（`extract.py` 中的 `TITLE_MERGE_CODES` + `fix_title_specificity()`）
- 標題如「解題」「長度」「面積」等缺乏獨特性的，已將 description 第一句併入 title（如「解題：速度」「長度：公里」）
- 已重新生成 `learning_content.json` 和 `concept_graph.json`
