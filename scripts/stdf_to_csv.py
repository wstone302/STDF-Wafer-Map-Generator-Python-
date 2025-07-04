import struct

def read_stdf_binary(filepath):
    with open(filepath, "rb") as f:
        return f.read()

def dump_all_records_to_txt(binary_data, output_txt):
    offset = 0
    with open(output_txt, "w", encoding="utf-8") as f:
        while offset < len(binary_data):
            if offset + 4 > len(binary_data):
                break
            reclen, rectype, recsub = struct.unpack(">HBB", binary_data[offset:offset+4])
            offset += 4
            record_data = binary_data[offset:offset+reclen]

            hex_data = ' '.join(f"{b:02X}" for b in record_data)
            ascii_data = ''.join(chr(b) if 32 <= b < 127 else '.' for b in record_data)
            f.write(f"RECTYPE={rectype:02d}, RECSUB={recsub:02d}, LEN={reclen:03d}\n")
            f.write(f"HEX:   {hex_data}\n")
            f.write(f"ASCII: {ascii_data}\n")
            f.write("=====\n")

            offset += reclen

def parse_prr_from_txt(input_txt, output_csv):
    with open(input_txt, "r", encoding="utf-8") as f:
        lines = f.readlines()

    results = []
    i = 0
    while i < len(lines):
        if "RECTYPE=05, RECSUB=20" in lines[i]:
            hex_line = lines[i+1].replace("HEX:", "").strip()
            bytes_list = bytes.fromhex(hex_line)
            try:
                head_num, site_num, part_flg = struct.unpack("BBB", bytes_list[0:3])
                num_test = struct.unpack(">H", bytes_list[3:5])[0]
                x_coord = struct.unpack(">h", bytes_list[5:7])[0]
                y_coord = struct.unpack(">h", bytes_list[7:9])[0]
                test_t = struct.unpack(">I", bytes_list[9:13])[0]

                part_id_len = bytes_list[13]
                part_id = bytes_list[14:14+part_id_len].decode(errors='ignore')

                txt_start = 14 + part_id_len
                part_txt_len = bytes_list[txt_start]
                txt_end = txt_start + 1 + part_txt_len

                soft_bin = struct.unpack(">H", bytes_list[txt_end:txt_end+2])[0]

                results.append([part_id, x_coord, y_coord, soft_bin])
            except Exception as e:
                print(f"⚠️ Error decoding PRR: {e}")
        i += 1

    with open(output_csv, "w", encoding="utf-8") as f:
        f.write("PART_ID,X_COORD,Y_COORD,SOFT_BIN\n")
        for row in results:
            f.write(f"{row[0]},{row[1]},{row[2]},{row[3]}\n")

if __name__ == "__main__":
    stdf_file = "sample.stdf"  # 改成你的 STDF 檔案
    txt_output = "output.txt"
    csv_output = "prr_output.csv"

    binary = read_stdf_binary(stdf_file)
    dump_all_records_to_txt(binary, txt_output)
    parse_prr_from_txt(txt_output, csv_output)

    print(f"完成：TXT ➝ {txt_output}，PRR ➝ {csv_output}")
