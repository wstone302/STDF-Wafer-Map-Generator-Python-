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
