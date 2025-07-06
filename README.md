# STDF Wafer Map Analysis Tool

本工具用於解析 STDF 測試檔案，支援二進位 `.std` 格式與純文字 `.txt` 格式。可擷取所有晶粒的座標與編號資訊，並繪製 Wafer Map、自動計算良率、匯出圖表與 Excel 結果。

---

### 資料夾結構

```
HW/
├── README.md                      # 使用說明文件（Markdown）
├── README.pdf                     # 使用說明文件（PDF）
├── scripts/                       # 主程式與輔助腳本
│   ├── unpack_and_prepare.py      # 解壓 .tar.gz 檔案
│   ├── main.py                    # 主程式：Wafer Map 與良率統計
│   └── stdf_parser.py             # STDF 二進位解析模組（含 PRR、FAR、MIR 等）
├── input/                         # 經轉換後之 STDF 純文字或 JSON 格式資料
├── output/                        # Wafer Map 圖片與良率統計資料
├── unpacked/                      # 原始 STDF 檔案解壓後資料
├── reference/                     # 參考資料
└── pystdf-master/                 # 第三方 STDF 解析套件（文字格式）
```

---

### 程式檔案與用途

| 檔案名稱                | 位置                        | 功能說明                                                        |
|-------------------------|-----------------------------|-----------------------------------------------------------------|
| `unpack_and_prepare.py` | `./scripts/`                | 解壓 `.tar.gz` 檔案並輸出至 `./unpacked/`                       |
| `stdf2text.py`          | `./pystdf-master/.../`      | 將 `.std` 轉為文字格式 `.txt`，輸出至 `./input/output.txt`     |
| `main.py`               | `./scripts/`                | 主程式：產出 Wafer Map 與良率統計檔案                           |
| `stdf_parser.py`        | `./scripts/`                | **新功能：直接解析 STDF Binary 檔，產出結構化 CSV**            |

---

### 執行流程（支援兩種來源格式）

#### 方式一：以 `.std` ➝ `.txt`（需使用 pystdf）

```bash
# Step 1: 解壓 STDF 壓縮檔
python scripts/unpack_and_prepare.py

# Step 2: 將 .std 轉為純文字格式
python pystdf-master/pystdf/scripts/stdf2text.py ./unpacked/xxx.std > ./input/output.txt

# Step 3: 執行主程式分析與繪圖
python scripts/main.py
```

#### 方式二：以 Binary `.std` 直接解析（新功能）

```bash
# 解析 Binary STDF 為 CSV
python scripts/stdf_parser.py ./unpacked/xxx.std ./input/parsed_output.csv
```

---

## 功能說明

### 1 STDF Binary 解碼（stdf_parser.py）

- 自行撰寫之 Binary 解碼器，解析以下記錄類型：
  - 基礎資訊：FAR、MIR、MRR、PCR、WIR、WRR、WCR
  - 晶粒測試資訊：PIR、PTR、PRR、FTR、MPR
  - 分群資訊：SDR、RDR、TSR
- 可輸出完整欄位對應的 CSV 檔案

### 2️ 主程式分析與繪圖（main.py）

- 解析 PRR 記錄，擷取晶粒之：
  - `X_COORD`、`Y_COORD`、`PART_ID`、`HARD_BIN`
- 畫出 Wafer Map：
  - `wafer_map_part_id.png`：依據編號顯示晶粒位置
  - `wafer_map_bin.png`：依據 BIN 顏色標示晶粒分類
- 自動統計良率並輸出 `.txt` 與 `.xlsx` 結果

---

## 輸出檔案

| 檔案名稱                   | 說明                                                  |
|----------------------------|-------------------------------------------------------|
| `wafer_map_data.xlsx`      | 含 X, Y, PART_ID, BIN 的詳細表格                      |
| `wafer_map_part_id.png`    | Wafer Map（以晶粒編號顯示）                          |
| `wafer_map_bin.png`        | Wafer Map（以測試分類 BIN 顏色區分）                |
| `wafer_yield_summary.txt`  | 良率統計摘要（總晶粒數、通過數、良率百分比）        |
| `parsed_output.csv`        | STDF Binary 解析後的完整結構欄位                    |

---

## 良率計算方式

```text
總晶粒數 = PRR 記錄數
通過數量 = BIN == 1
良率 (%) = (PASS Count / Total Chips) × 100%
```

---

## 依賴套件

```bash
pip install pandas matplotlib numpy
```

若使用 `pystdf`（文字格式解析）：

```bash
pip install pystdf
```

---

## 題目對應需求整理

| 題目需求                  | 對應功能                                  |
|---------------------------|--------------------------------------------|
| 解壓 `.tar.gz`            | `unpack_and_prepare.py` 處理雙層壓縮       |
| 解析 STDF 二進位資料      | `stdf_parser.py` 全自製 Binary 解析器     |
| 擷取晶粒資訊              | PRR 欄位分析與 Wafer Map 圖片標註         |
| 畫出 PART_ID / BIN 圖     | `main.py` 輸出 PNG                        |
| 統計良率並產出 Excel      | `wafer_map_data.xlsx` / `wafer_yield_summary.txt` |