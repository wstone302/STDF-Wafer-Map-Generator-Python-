import struct

def detect_endian(binary):
    """從前 4 byte 嘗試判斷檔案端序（Big 或 Little）。"""
    try:
        reclen_be, rectype_be, recsub_be = struct.unpack(">HBB", binary[0:4])
        if rectype_be == 0 and recsub_be == 10 and reclen_be <= 0xFF:
            return ">"
    except struct.error:
        pass

    try:
        reclen_le, rectype_le, recsub_le = struct.unpack("<HBB", binary[0:4])
        if rectype_le == 0 and recsub_le == 10 and reclen_le <= 0xFF:
            return "<"
    except struct.error:
        pass

    # 預設小端
    return "<"

def parse_prr_fields(data, endian):
    """只解析 PRR 固定欄位：X_COORD, Y_COORD, PART_ID"""
    off = 0
    # 跳過 HEAD_NUM(1), SITE_NUM(1), PART_FLG(1)
    off += 3
    # 跳過 NUM_TEST (2), HARD_BIN(2), SOFT_BIN(2)
    off += 2 + 2 + 2
    # X/Y_COORD 各 2 bytes
    x_coord = struct.unpack(endian + "h", data[off:off+2])[0]
    off += 2
    y_coord = struct.unpack(endian + "h", data[off:off+2])[0]
    off += 2
    # 跳過 TEST_T (4)
    off += 4

    # PART_ID (Cn)
    length = struct.unpack(endian + "B", data[off:off+1])[0]
    off += 1
    part_id = data[off:off+length].decode(errors="ignore")

    return {"X_COORD": x_coord, "Y_COORD": y_coord, "PART_ID": part_id}

def extract_prr_records(stdf_path):
    """掃描整個 STDF，把所有 PRR 記錄抽出來。"""
    with open(stdf_path, "rb") as f:
        binary = f.read()

    endian = detect_endian(binary)
    print(f"使用端序: {endian}")

    offset = 0
    prr_list = []

    # 跳過 FAR
    reclen, rectype, recsub = struct.unpack(endian + "HBB", binary[0:4])
    if (rectype, recsub) == (0, 10):
        offset = 4 + reclen

    # 主迴圈
    while offset + 4 <= len(binary):
        reclen, rectype, recsub = struct.unpack(endian + "HBB",
                                                binary[offset:offset+4])
        offset += 4
        data = binary[offset:offset+reclen]

        if (rectype, recsub) == (5, 20):
            prr_list.append(parse_prr_fields(data, endian))

        offset += reclen

    return prr_list

if __name__ == "__main__":
    import sys, csv
    if len(sys.argv) != 3:
        print("用法: python extract_prr.py input.stdf output_prr.csv")
        sys.exit(1)

    stdf_file = sys.argv[1]
    csv_file  = sys.argv[2]

    records = extract_prr_records(stdf_file)
    print(f"\n共抽出 {len(records)} 筆 PRR 記錄\n")

    # —— 1) 文字列表輸出，格式如範例 —— #
    # Ex: x=1 y=1 and part ID=1
    for rec in records:
        print(f"x={rec['X_COORD']} y={rec['Y_COORD']} and part ID={rec['PART_ID']}")

    # —— 2) 同時寫入 CSV（如不需要可整個拿掉下面區塊） —— #
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["X_COORD","Y_COORD","PART_ID"])
        writer.writeheader()
        writer.writerows(records)

    print(f"\n已寫入 {csv_file}")
