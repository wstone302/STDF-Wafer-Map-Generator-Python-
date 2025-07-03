import struct
import csv

def read_stdf_file(filepath):
    with open(filepath, "rb") as f:
        return f.read()

def parse_prr_records(binary_data):
    offset = 0
    results = []

    while offset < len(binary_data):
        try:
            # 每筆 STDF 記錄的開頭是：長度（2B）+ record type（1B）+ record sub-type（1B）
            reclen, rectype, recsub = struct.unpack(">HBB", binary_data[offset:offset+4])
            offset += 4

            data = binary_data[offset:offset+reclen]

            # 處理 PRR (type=5, sub=20)
            if rectype == 5 and recsub == 20:
                # 根據 STDF spec，PRR 部分欄位格式如下（僅列出常用）
                # HEAD_NUM(1B), SITE_NUM(1B), PART_FLG(1B), NUM_TEST(U2), X_COORD(I2), Y_COORD(I2),
                # TEST_T(U4), PART_ID(Cn), PART_TXT(Cn), SOFT_BIN(U2), HARD_BIN(U2)
                
                # 我們手動一個個解析欄位
                head_num, site_num, part_flg = struct.unpack("BBB", data[0:3])
                num_test = struct.unpack(">H", data[3:5])[0]
                x_coord = struct.unpack(">h", data[5:7])[0]
                y_coord = struct.unpack(">h", data[7:9])[0]
                test_t = struct.unpack(">I", data[9:13])[0]

                # PART_ID 是 Cn 字串（第一個 byte 是長度）
                part_id_len = data[13]
                part_id = data[14:14+part_id_len].decode(errors='ignore')

                # PART_TXT 是下一個 Cn，跳過它
                txt_start = 14 + part_id_len
                part_txt_len = data[txt_start]
                txt_end = txt_start + 1 + part_txt_len

                # SOFT_BIN (U2)
                soft_bin = struct.unpack(">H", data[txt_end:txt_end+2])[0]

                results.append({
                    "PART_ID": part_id,
                    "X_COORD": x_coord,
                    "Y_COORD": y_coord,
                    "SOFT_BIN": soft_bin
                })

            offset += reclen
        except Exception as e:
            print(f"⚠️ Error parsing at offset {offset}: {e}")
            break

    return results

def write_to_csv(results, output_path):
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["PART_ID", "X_COORD", "Y_COORD", "SOFT_BIN"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

if __name__ == "__main__":
    binary = read_stdf_file("sample.stdf")
    prr_data = parse_prr_records(binary)
    write_to_csv(prr_data, "output.csv")
    print(f"✅ 轉換完成，共 {len(prr_data)} 筆 PRR 記錄，已輸出為 output.csv")
