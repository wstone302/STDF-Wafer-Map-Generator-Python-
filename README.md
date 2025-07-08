# STDF Parser 工具套件

這個專案包含兩支 Python 腳本，用於解析 STDF (Standard Test Data Format) 測試資料，並將結果匯出成 CSV：

* `scripts/unpack_and_prepare.py`：將 .tar.gz 解壓縮至指定檔案(.stdf) 。
* `scripts/stdf_parser.py`：完整解析所有 STDF 記*錄，輸出所有欄位的 CSV。
* `scripts/extract_prr.py`：專門抓取 PRR (Part Results Record) 記錄中的 X、Y 座標與 PART\_ID，輸出簡易 CSV。
* `scripts/format_prr_with_list.py`：將 extract_prr.py 生成出來的 CSV 畫成指定之 wafer map。

---

## 目錄

1. [環境與相依套件](#環境與相依套件)
2. [程式結構](#程式結構)
3. [`stdf_parser.py` 使用說明](#stdf_parserpy-使用說明)
4. [`extract_prr.py` 使用說明](#extract_prrpy-使用說明)
5. [範例](#範例)

---

## 環境與相依套件

* Python 3.8+
* pandas

建立虛擬環境並安裝相應 Python 版本：

```bash
conda create -n <your_env_name> python=3.11 -y
conda activate your_env_name 
pip install pandas 
```

---

## 程式結構

```
project_root/
├── scripts/
│   ├── unpack_and_prepare.py     # 解壓縮 
│   ├── stdf_parser.py            # 二進位轉換
│   ├── extract_prr.py            # PRR 轉換
│   └── format_prr_with_list.py   # 生成 wafer map
└── README.md                     # 使用說明文件
```

---

## `stdf_parser.py` 使用說明

此腳本可對整支 STDF 檔案做全面解析，將所有記錄、所有欄位寫入 CSV。

```bash
python scripts/stdf_parser.py <輸入.STDF> <輸出.csv>
```

### 參數說明

* `<輸入.STDF>`：要解析的 STDF 二進位檔案路徑。
* `<輸出.csv>`：解析結果要寫入的 CSV 檔案路徑。

執行後會顯示端序偵測與每筆記錄解析日誌，最後輸出完整 CSV。

---

## `extract_prr.py` 使用說明

此腳本專門掃描 STDF 中所有 PRR (Type=5, SubType=20) 記錄，僅提取：

* `X_COORD`: 測試點 X 座標
* `Y_COORD`: 測試點 Y 座標
* `PART_ID`: 測試點 ID

```bash
python scripts/extract_prr.py <輸入.STDF> <輸出_prr.csv>
```

### 參數說明

* `<輸入.STDF>`：要掃描的 STDF 檔案。
* `<輸出_prr.csv>`：PRR 結果的 CSV 檔案路徑。

執行後會輸出 CSV，欄位僅含 `X_COORD, Y_COORD, PART_ID`，方便後續製作 wafer map。

---

## 範例

```bash
# 解壓縮 .tar.gz
python scripts/unpack_and_prepare.py

# 二進位轉換
python scripts/stdf_parser.py unpacked/main_Lot_1_Wafer_1_Oct_13_09h33m41s_STDF output/full.csv

# 單獨抽 PRR
python scripts/extract_prr.py unpacked/main_Lot_1_Wafer_1_Oct_13_09h33m41s_STDF output/prr.csv

# 生成 wafer map
python scripts/format_prr_with_list.py
```

---

