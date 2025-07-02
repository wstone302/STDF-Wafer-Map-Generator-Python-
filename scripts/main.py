import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# === 檔案路徑設定 ===
input_path = "./input/output.txt"
excel_path = "./output/wafer_map_data.xlsx"
part_id_img_path = "./output/wafer_map_part_id.png"
bin_img_path = "./output/wafer_map_bin.png"
yield_txt_path = "./output/wafer_yield_summary.txt"

# === 確認檔案存在並讀入 ===
if not os.path.exists(input_path):
    print(f"找不到檔案：{input_path}")
    exit()

with open(input_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"讀入 {len(lines)} 行")

# === 篩出 PRR 記錄 ===
prr_lines = [line for line in lines if line.startswith("PRR|")]
print(f"找到 PRR 記錄：{len(prr_lines)} 行")

data = []
for line in prr_lines:
    parts = line.strip().split("|")
    try:
        x = int(parts[7])
        y = int(parts[8])
        part_id = int(float(parts[10]))
        soft_bin = int(float(parts[11])) if len(parts) > 11 else 0
        data.append({"X": x, "Y": y, "PART_ID": part_id, "BIN": soft_bin})
    except Exception as e:
        print(f"⚠️ 無法解析行：{line.strip()}，錯誤：{e}")
        continue

# === 建立 DataFrame ===
df = pd.DataFrame(data)
if df.empty:
    print("沒有成功擷取到 PRR 記錄。")
    exit()

df.to_excel(excel_path, index=False)
print(f"匯出 Excel：{excel_path}")

# === PART_ID 圖（含文字置中顯示） ===
pivot_map = df.pivot(index='Y', columns='X', values='PART_ID')
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(pivot_map.fillna(0).astype(int), cmap='viridis', origin='lower')

plt.title("Wafer Map (PART_ID)")
plt.colorbar(im, ax=ax, label="PART_ID")
plt.xlabel("X")
plt.ylabel("Y")

# 加上文字顯示 PART_ID 在格子中央
for y_idx in range(pivot_map.shape[0]):
    for x_idx in range(pivot_map.shape[1]):
        value = pivot_map.values[y_idx][x_idx]
        if not pd.isna(value):
            ax.text(x_idx, y_idx, str(int(value)), ha='center', va='center', fontsize=14, color='black')

plt.tight_layout()
plt.savefig(part_id_img_path)
plt.close()
print(f"匯出 PART_ID 彩圖（含文字）：{part_id_img_path}")


# # === PART_ID 圖 ===
# pivot_map = df.pivot(index='Y', columns='X', values='PART_ID')
# fig, ax = plt.subplots(figsize=(10, 8))
# im = ax.imshow(pivot_map.fillna(0).astype(int), cmap='viridis', origin='lower')
# plt.title("Wafer Map (PART_ID)")
# plt.colorbar(im, ax=ax, label="PART_ID")
# plt.xlabel("X")
# plt.ylabel("Y")
# plt.tight_layout()
# plt.savefig(part_id_img_path)
# plt.close()
# print(f"匯出 PART_ID 彩圖：{part_id_img_path}")

# === BIN 圖 ===
bin_map = df.pivot(index='Y', columns='X', values='BIN')
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(bin_map.fillna(0).astype(int), cmap='tab20', origin='lower')
plt.title("Wafer Map (BIN)")
plt.colorbar(im, ax=ax, label="BIN")
plt.xlabel("X")
plt.ylabel("Y")
plt.tight_layout()
plt.savefig(bin_img_path)
plt.close()
print(f"匯出 BIN 彩圖：{bin_img_path}")

# === 良率 ===
total = len(df)
pass_count = len(df[df["BIN"] == 1])
yield_rate = pass_count / total * 100 if total > 0 else 0

summary = f"Total Chips: {total}\nPASS (BIN=1): {pass_count}\nYield Rate: {yield_rate:.2f}%"
with open(yield_txt_path, "w", encoding="utf-8") as f:
    f.write(summary)

print(f"匯出良率報告：{yield_txt_path}")
