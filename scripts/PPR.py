import struct
import csv

def read_stdf_file(filepath):
    with open(filepath, "rb") as f:
        return f.read()

def parse_stdf_records(binary_data):
    offset = 0
    results = []

    while offset < len(binary_data):
        try:
            # 每筆 STDF 記錄開頭: 長度 (2B) + Record Type (1B) + Sub Type (1B)
            reclen, rectype, recsub = struct.unpack_from("<HBB", binary_data, offset)
            offset += 4
            data = binary_data[offset:offset+reclen]

            if rectype == 0 and recsub == 10:  # FAR
                cpu_type = struct.unpack_from("B", data, 0)[0]
                results.append({"TYPE": "FAR", "CPU_TYPE": cpu_type})

            elif rectype == 1 and recsub == 10:  # MIR
                test_time = struct.unpack_from("<I", data, 20)[0]
                results.append({"TYPE": "MIR", "TEST_TIME": test_time})

            elif rectype == 1 and recsub == 30:  # PCR
                bin_count = struct.unpack_from("<H", data, 2)[0]
                results.append({"TYPE": "PCR", "BIN_COUNT": bin_count})

            elif rectype == 1 and recsub == 40:  # HBR
                hard_bin_num = struct.unpack_from("<H", data, 0)[0]
                results.append({"TYPE": "HBR", "HARD_BIN_NUM": hard_bin_num})

            elif rectype == 5 and recsub == 10:  # PTR
                test_num = struct.unpack_from("<H", data, 0)[0]
                results.append({"TYPE": "PTR", "TEST_NUM": test_num})

            elif rectype == 5 and recsub == 20:  # PRR
                head_num, site_num, part_flg = struct.unpack_from("BBB", data, 0)
                num_test = struct.unpack_from("<H", data, 3)[0]
                x_coord = struct.unpack_from("<h", data, 5)[0]
                y_coord = struct.unpack_from("<h", data, 7)[0]
                test_t = struct.unpack_from("<I", data, 9)[0]
                part_id_len = data[13]
                part_id = data[14:14+part_id_len].decode(errors='ignore')
                txt_start = 14 + part_id_len
                part_txt_len = data[txt_start]
                txt_end = txt_start + 1 + part_txt_len
                soft_bin = struct.unpack_from("<H", data, txt_end)[0]
                hard_bin = struct.unpack_from("<H", data, txt_end+2)[0]
                results.append({
                    "TYPE": "PRR",
                    "HEAD_NUM": head_num,
                    "SITE_NUM": site_num,
                    "PART_ID": part_id,
                    "X_COORD": x_coord,
                    "Y_COORD": y_coord,
                    "SOFT_BIN": soft_bin,
                    "HARD_BIN": hard_bin
                })

            offset += reclen
        except Exception as e:
            print(f"⚠️ Error at offset {offset}: {e}")
            break

    return results

def write_to_csv(results, output_path):
    keys = sorted(set().union(*[r.keys() for r in results]))
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

if __name__ == "__main__":
    binary = read_stdf_file("sample.stdf")
    parsed_data = parse_stdf_records(binary)
    write_to_csv(parsed_data, "parsed_output.csv")
    print(f"✅ 已完成解析與輸出，共 {len(parsed_data)} 筆記錄。")
