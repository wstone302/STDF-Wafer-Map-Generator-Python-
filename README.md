
# STDF Wafer Map Generator (Java)

本專案可將 `.out` 格式的 STDF 測試結果轉為 `.csv`，並根據 X/Y 座標繪製晶圓圖、統計良率，並輸出結果（文字報告與彩圖）。

---

### 專案結構

```
stdf_java_project/
├── lib/
│   └── StdfDump.jar         # 官方提供的 STDF 解碼工具
├── unpacked/
│   └── *.out                # 用 StdfDump 解碼後的輸出文字檔
├── src/
│   ├── StdfOutToCsv.java    # 將 out 檔轉為 csv
│   └── WaferMapGenerator.java # 輸出圖像、統計良率
├── converted.csv            # 中介 CSV 檔
└── output/
    ├── wafer_map_part_id.png
    ├── wafer_map_bin.png
    └── wafer_yield_summary.txt
```

---

### 使用步驟

#### step1  將 `.stdf` 檔轉為 `.out`
請先使用 STDF 工具列印 STDF 結構至純文字格式：

```bash
java -cp lib/StdfDump.jar ri.core.stdf.StdfDump unpacked/main_Lot_1_Wafer_1_Oct_13_09h33m41s_STDF
```

執行後會產出 `.out` 檔案，例如：

```
Output saved to: unpacked/main_Lot_1_Wafer_1_Oct_13_09h33m41s_STDF.out
```



#### step2 編譯並執行 Java 轉檔

```bash
javac -d . src/StdfOutToCsv.java
java StdfOutToCsv
```

輸出為 `converted.csv`，內容範例如下：

```
X,Y,PART_ID,BIN
-5,-4,1,1
-1,-4,2,1
4,-4,3,2
6,-4,4,1
7,-4,5,1
...
```


#### step3 產生晶圓圖與良率報告

```bash
javac -d . src/WaferMapGenerator.java
java WaferMapGenerator
```

執行結果會輸出：

```
--- 晶圓圖 (P: Pass, F: Fail) ---
原始晶圓範圍: X [-7,7], Y [-4,0]
         -7  -6  -5  -4  -3  -2  -1   0   1   2   3   4   5   6   7
   0      .   F   .   F   .   .   .   .   .   .   .   .   .   .   .
  -1      .   .   .   .   .   .   .   .   .   .   .   .   .   .   .
  -2      .   .   .   .   .   .   .   .   .   .   .   .   .   .   .
  -3      F   .   .   .   F   F   .   .   .   .   F   F   .   F   .
  -4      .   .   P   .   .   .   P   .   .   .   .   F   .   F   F

良率總結輸出完成： output/wafer_yield_summary.txt
圖片已保存到: output/wafer_map_part_id.png
圖片已保存到: output/wafer_map_bin.png
```

---

### 功能說明

- 自動解析 `X, Y, PART_ID, BIN`
- 依據座標重建晶圓格狀結構
- 以終端機顯示文字晶圓圖（P 為 Pass、F 為 Fail）
- 匯出良率報告 `.txt`
- 匯出兩張彩圖：`PART_ID` 以及 `BIN` 為基礎的晶圓圖

---

### 聯絡與貢獻
```
作者 / Author: 張婷佳 (Jessie Chang)
Email: tingchaaa@gmail.com
```


