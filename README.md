# STDF Wafer Map Analysis Tool

本工具用於解析 STDF 測試檔案，從中擷取所有晶粒的座標與編號資訊，並繪製 Wafer Map。可自動計算良率並匯出對應圖表與 Excel 結果。

---

### 資料夾結構

```
HW/
├── README.md                      # 使用說明文件（Markdown）
├── README.pdf                     # 使用說明文件（PDF）
├── scripts/                       # 自行撰寫之主程式與工具腳本
│   ├── unpack_and_prepare.py      # 解壓 .tar.gz 檔案
│   └── main.py                    # 主程式：Wafer Map 與良率統計
├── input/                         # 經轉換後之 STDF 文字檔（output.txt）
├── output/                        # Wafer Map 圖片與良率統計資料
├── unpacked/                      # 原始 STDF 檔案解壓後資料
├── reference/                     # 參考資料
└── pystdf-master/                 # 第三方 STDF 解析套件
```


### 程式檔案用途與執行說明

| 檔案名稱                | 位置                        | 功能說明                                                      |
|-------------------------|-----------------------------|---------------------------------------------------------------|
| `unpack_and_prepare.py` | `./scripts/`                | 解壓 `.tar.gz` 檔案並展開為 `.std`，輸出至 `./unpacked/`       |
| `stdf2text.py`          | `./pystdf-master/.../`      | 將 `.std` 轉為純文字格式 `.txt`，輸出至 `./input/output.txt` |
| `main.py`               | `./scripts/`                | 主程式，產出 Wafer Map 圖與良率統計檔案                       |

### 執行順序

```bash
# Step 1: 解壓 STDF 壓縮檔
python scripts/unpack_and_prepare.py

# Step 2: 將 .std 轉為文字格式
python pystdf-master/pystdf/scripts/stdf2text.py ./unpacked/main_Lot_1_Wafer_1_Oct_13_09h33m41s_STDF > ./input/output.txt

# Step 3: 執行主程式分析與繪圖
python scripts/main.py
```

<div style="page-break-after: always;"></div>

## 資料處理流程

### Step 1 & 2：解壓 .tar.gz 並展開 .tar 檔案

> 題目提供的檔案為 main_Lot_1_Wafer_1_Oct_13_09h33m41s_STDF.tar.gz
實際為 .tar 格式，以下程式碼會自動完成兩階段解壓，並顯示展開結果。

```python
import gzip
import shutil
import tarfile
import os

# === 檔案與資料夾路徑 ===
input_gz_path = "./main_Lot_1_Wafer_1_Oct_13_09h33m41s_STDF.tar.gz"
intermediate_tar_path = "./temp_stdf.tar"
unpack_dir = "./unpacked"

# === Step 1: 解壓 .gz 成 .tar ===
if not os.path.exists(input_gz_path):
    print(f"找不到壓縮檔：{input_gz_path}")
    exit()

with gzip.open(input_gz_path, 'rb') as f_in:
    with open(intermediate_tar_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

print(f"已解壓 .gz 成 .tar：{intermediate_tar_path}")

# === Step 2: 解開 .tar 成資料夾 ===
with tarfile.open(intermediate_tar_path, "r") as tar:
    tar.extractall(unpack_dir)

print(f"完成解壓 STDF 至：{unpack_dir}")

# === Step 3: 顯示有哪些解出來的檔案 ===
print("解壓內容：")
for f in os.listdir(unpack_dir):
    print("  -", f)

```

### Step 3：轉為文字格式

使用 [`pystdf`](https://github.com/stephentu/pystdf) 工具轉換 `.std` → `.txt`

```bash
python pystdf-master/pystdf/scripts/stdf2text.py ./unpacked/main_Lot_1_Wafer_1_Oct_13_09h33m41s_STDF > ./input/output.txt
```

<div style="page-break-after: always;"></div>

## 執行主程式

```bash
python scripts/main.py
```

---

## 功能與說明

- 解析 STDF 檔案中所有 `PRR` 記錄
- 擷取晶粒之：
  - X 座標：PRR 欄位 `X_COORD`
  - Y 座標：PRR 欄位 `Y_COORD`
  - 晶粒編號：PRR 欄位 `PART_ID`
  - 測試分類：PRR 欄位 `HARD_BIN`
- 畫出 2 種 Wafer Map：
  - `wafer_map_part_id.png`：顯示各座標之 PART_ID
  - `wafer_map_bin.png`：依據 BIN 值分類之顏色圖
- 自動統計良率，顯示 PASS 數與總數

---

## 輸出檔案說明

| 檔案名稱                   | 說明                                                  |
|----------------------------|-------------------------------------------------------|
| `wafer_map_data.xlsx`      | 含 X, Y, PART_ID, BIN 的詳細表格                      |
| `wafer_map_part_id.png`    | Wafer Map（以晶粒編號顯示）                          |
| `wafer_map_bin.png`        | Wafer Map（以測試分類 BIN 顏色區分）                |
| `wafer_yield_summary.txt`  | 良率統計摘要（總晶粒數、通過數、良率百分比）        |

---

## 良率計算公式

- 總晶粒數：所有 PRR 記錄總筆數
- 通過數：BIN 值為 1 者
- 計算公式：

```text
Yield = (PASS Count / Total Chips) × 100%
```
---
<div style="page-break-after: always;"></div>

## 套件需求

- Python 3.11
- 套件安裝方式：

```bash
pip install pystdf pandas matplotlib numpy
```

---

## 題目對應說明

本專案對應題目需求如下：

| 題目要求                  | 本專案對應功能                             |
|---------------------------|---------------------------------------------|
| 解壓 `.tar.gz`            | `gzip` + `tarfile` 處理 `.std` 來源檔       |
| 擷取 PRR 資訊             | `tx.py` 內部解析每一筆 PRR 記錄            |
| 提取 X, Y, PART_ID        | 儲存於 `wafer_map_data.xlsx` 並於圖片顯示  |
| 繪製 Wafer Map            | 輸出 `wafer_map_part_id.png` 等圖          |
| 顯示 PART_ID 於 Wafer Map | 圖中座標標註 PART_ID                        |

