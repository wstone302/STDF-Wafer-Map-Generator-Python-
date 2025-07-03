import struct
import csv

# === Record Type/SubType 對照表 ===
record_map = {
    (0, 10): "FAR",   # File Attributes Record
    (1, 10): "MIR",   # Master Information Record
    (1, 20): "MRR",   # Master Results Record
    (1, 30): "PCR",   # Part Count Record
    (1, 40): "HBR",   # Hard Bin Record
    (1, 50): "SBR",   # Soft Bin Record
    (1, 60): "PMR",   # Pin Map Record
    (1, 62): "PGR",   # Pin Group Record
    (1, 70): "PLR",   # Pin Limits Record
    (5, 10): "PTR",   # Parametric Test Record
    (5, 20): "PRR",   # Part Results Record
}

def parse_cn(data, offset):
    length = data[offset]
    val = data[offset+1:offset+1+length].decode(errors="ignore")
    return val, offset + 1 + length

def parse_record(record_type, sub_type, data):
    parsed = {"TYPE": record_map.get((record_type, sub_type), f"{record_type}:{sub_type}")}
    try:
        if (record_type, sub_type) == (0, 10):  # FAR
            parsed.update({"CPU_TYPE": data[0], "STDF_VER": data[1]})

        elif (record_type, sub_type) == (1, 10):  # MIR
            tstamp = struct.unpack(">I", data[0:4])[0]
            lot_id, _ = parse_cn(data, 28)
            parsed.update({"TIME_STAMP": tstamp, "LOT_ID": lot_id})

        elif (record_type, sub_type) == (1, 30):  # PCR
            head_num, site_num = data[0], data[1]
            retest_cnt = struct.unpack(">H", data[2:4])[0]
            parsed.update({"HEAD_NUM": head_num, "SITE_NUM": site_num, "RETEST_CNT": retest_cnt})

        elif (record_type, sub_type) == (1, 40):  # HBR
            bin_num = struct.unpack(">H", data[0:2])[0]
            bin_cnt = struct.unpack(">I", data[2:6])[0]
            parsed.update({"BIN_NUM": bin_num, "BIN_CNT": bin_cnt})

        elif (record_type, sub_type) == (5, 10):  # PTR
            test_num = struct.unpack(">I", data[0:4])[0]
            result = struct.unpack(">f", data[10:14])[0]
            parsed.update({"TEST_NUM": test_num, "RESULT": result})

        elif (record_type, sub_type) == (5, 20):  # PRR
            x_coord = struct.unpack(">h", data[5:7])[0]
            y_coord = struct.unpack(">h", data[7:9])[0]
            part_id, offset = parse_cn(data, 13)
            part_txt_len = data[offset]
            offset += 1 + part_txt_len
            soft_bin = struct.unpack(">H", data[offset:offset+2])[0]
            parsed.update({"X_COORD": x_coord, "Y_COORD": y_coord, "PART_ID": part_id, "SOFT_BIN": soft_bin})
    except Exception as e:
        parsed["ERROR"] = str(e)
    return parsed

def parse_stdf(filepath, output_csv):
    with open(filepath, "rb") as f:
        binary = f.read()

    offset = 0
    parsed_rows = []
    all_fields = set()

    while offset + 4 <= len(binary):
        try:
            reclen, rectype, recsub = struct.unpack(">HBB", binary[offset:offset+4])
            offset += 4
            data = binary[offset:offset+reclen]
            offset += reclen

            parsed = parse_record(rectype, recsub, data)
            parsed_rows.append(parsed)
            all_fields.update(parsed.keys())
        except Exception as e:
            print(f"⚠️ Error at offset {offset}: {e}")
            break

    all_fields = sorted(all_fields)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        writer.writeheader()
        for row in parsed_rows:
            writer.writerow(row)

    print(f"✅ 解析完成，共 {len(parsed_rows)} 筆記錄，輸出為 {output_csv}")

