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
    # 跳過前三個 U1
    off += 3
    # NUM_TEST: U2
    off += 2
    # HARD_BIN, SOFT_BIN, X/Y_COORD, TEST_T
    # X_COORD: signed U2
    off += 2 + 2  # hard+soft
    x_coord = struct.unpack(endian + "h", data[off:off+2])[0]
    off += 2
    y_coord = struct.unpack(endian + "h", data[off:off+2])[0]
    off += 2
    # 跳過 TEST_T U4
    off += 4

    # 接下來就是 Cn 欄位：PART_ID
    # Cn 前先讀長度 U1
    length = struct.unpack(endian + "B", data[off:off+1])[0]
    off += 1
    part_id = data[off:off+length].decode(errors="ignore")

    return {"X_COORD": x_coord, "Y_COORD": y_coord, "PART_ID": part_id}

def extract_prr_records(stdf_path):
    """掃描整個 STDF，把所有 PRR 記錄抽出來。"""
    with open(stdf_path, "rb") as f:
        binary = f.read()

    endian = detect_endian(binary)
    print(f"使用端序: {endian!r}")

    offset = 0
    prr_list = []

    # 如果有 FAR 標頭，可以先把它跳過
    # 假設 FAR 長度不超過 255
    _, rectype, recsub = struct.unpack(endian + "HBB", binary[0:4])
    reclen = struct.unpack(endian + "H", binary[0:2])[0]
    if (rectype, recsub) == (0, 10):
        offset = 4 + reclen

    # 主迴圈
    while offset + 4 <= len(binary):
        reclen, rectype, recsub = struct.unpack(endian + "HBB", binary[offset:offset+4])
        offset += 4
        data = binary[offset:offset+reclen]

        if (rectype, recsub) == (5, 20):
            prr = parse_prr_fields(data, endian)
            prr_list.append(prr)

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
    print(f"共抽出 {len(records)} 筆 PRR 記錄")

    # 輸出成 CSV
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["X_COORD","Y_COORD","PART_ID"])
        writer.writeheader()
        writer.writerows(records)

    print(f"已寫入 {csv_file}")
