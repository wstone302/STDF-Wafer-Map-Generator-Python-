import struct
import csv

record_map = {
    (0, 10): "FAR",
    (0, 20): "ATR",
    (1, 10): "MIR",
    (1, 20): "MRR",
    (1, 30): "PCR",
    (1, 40): "HBR",
    (1, 50): "SBR",
    (1, 60): "PMR",
    (1, 62): "PGR",
    (1, 70): "RDR",
    (1, 80): "SDR",
    (1, 91): "GDR",
    (1, 92): "DTR",
    (2, 10): "WIR",
    (2, 20): "WRR",
    (2, 30): "WCR",
    (5, 10): "PTR",
    (5, 15): "PIR",
    (5, 20): "PRR",
    (5, 30): "BPS",
    (5, 40): "EPS",
    (10, 30): "TSR",
    (15, 10): "FTR",
    (15, 15): "MPR",
}

def parse_cn(data, offset):
    if offset >= len(data):
        return "", offset
    length = data[offset]
    end = offset + 1 + length
    val = data[offset+1:end].decode(errors="ignore") if end <= len(data) else ""
    return val, end

def parse_record(record_type, sub_type, data):
    parsed = {"TYPE": record_map.get((record_type, sub_type), f"{record_type}:{sub_type}")}
    try:
        if (record_type, sub_type) == (0, 10):  # FAR
            if len(data) >= 2:
                parsed.update({"CPU_TYPE": data[0], "STDF_VER": data[1]})
            else:
                parsed["ERROR"] = "FAR record too short"
            return parsed

        elif (record_type, sub_type) == (1, 10):  # MIR
            if len(data) >= 29:
                tstamp = struct.unpack(">I", data[0:4])[0]
                lot_id_len = data[28]
                if len(data) >= 29 + lot_id_len:
                    lot_id = data[29:29+lot_id_len].decode(errors="ignore")
                    parsed.update({"TIME_STAMP": tstamp, "LOT_ID": lot_id})
                else:
                    parsed.update({"TIME_STAMP": tstamp})
            return parsed

        elif (record_type, sub_type) == (1, 30):  # PCR
            head_num, site_num = data[0], data[1]
            retest_cnt = struct.unpack(">H", data[2:4])[0]
            parsed.update({"HEAD_NUM": head_num, "SITE_NUM": site_num, "RETEST_CNT": retest_cnt})
            return parsed

        elif (record_type, sub_type) == (1, 40):  # HBR
            bin_num = struct.unpack(">H", data[0:2])[0]
            bin_cnt = struct.unpack(">I", data[2:6])[0]
            parsed.update({"BIN_NUM": bin_num, "BIN_CNT": bin_cnt})
            return parsed

        elif (record_type, sub_type) == (5, 10):  # PTR
            test_num = struct.unpack(">I", data[0:4])[0]
            result = struct.unpack(">f", data[10:14])[0]
            parsed.update({"TEST_NUM": test_num, "RESULT": result})
            return parsed

        elif (record_type, sub_type) == (5, 20):  # PRR
            if len(data) >= 14:
                x_coord = struct.unpack(">h", data[5:7])[0]
                y_coord = struct.unpack(">h", data[7:9])[0]
                part_id_len = data[13]
                if len(data) >= 14 + part_id_len + 2:
                    part_id = data[14:14+part_id_len].decode(errors="ignore")
                    offset = 14 + part_id_len
                    soft_bin = struct.unpack(">H", data[offset:offset+2])[0]
                    parsed.update({"X_COORD": x_coord, "Y_COORD": y_coord, "PART_ID": part_id, "SOFT_BIN": soft_bin})
            return parsed

        elif (record_type, sub_type) == (0, 20):  # ATR
            mod_time = struct.unpack(">I", data[0:4])[0]
            cmd_len = data[4]
            cmd_line = data[5:5+cmd_len].decode(errors="ignore")
            parsed.update({"MOD_TIM": mod_time, "CMD_LINE": cmd_line})
            return parsed

        elif (record_type, sub_type) == (1, 70):  # RDR
            num_bins = struct.unpack(">H", data[0:2])[0]
            rtst_bin = [struct.unpack(">H", data[2+i*2:4+i*2])[0] for i in range(num_bins)]
            parsed.update({"NUM_BINS": num_bins, "RTST_BIN": rtst_bin})
            return parsed

        elif (record_type, sub_type) == (1, 80):  # SDR
            head_num, site_grp, site_cnt = struct.unpack("BBB", data[0:3])
            site_nums = list(data[3:3+site_cnt])
            parsed.update({"HEAD_NUM": head_num, "SITE_GRP": site_grp, "SITE_CNT": site_cnt, "SITE_NUM": site_nums})
            return parsed

        elif (record_type, sub_type) == (2, 10):  # WIR
            head_num, site_grp = struct.unpack("BB", data[0:2])
            start_t = struct.unpack(">I", data[2:6])[0]
            wafer_len = data[6]
            wafer_id = data[7:7+wafer_len].decode(errors="ignore")
            parsed.update({"HEAD_NUM": head_num, "SITE_GRP": site_grp, "START_T": start_t, "WAFER_ID": wafer_id})
            return parsed

        elif (record_type, sub_type) == (2, 20):  # WRR
            head_num, site_grp = struct.unpack("BB", data[0:2])
            finish_t = struct.unpack(">I", data[2:6])[0]
            part_cnt = struct.unpack(">I", data[6:10])[0]
            rtst_cnt = struct.unpack(">I", data[10:14])[0]
            abrt_cnt = struct.unpack(">I", data[14:18])[0]
            good_cnt = struct.unpack(">I", data[18:22])[0]
            func_cnt = struct.unpack(">I", data[22:26])[0]
            parsed.update({
                "HEAD_NUM": head_num, "SITE_GRP": site_grp,
                "FINISH_T": finish_t, "PART_CNT": part_cnt,
                "RTST_CNT": rtst_cnt, "ABRT_CNT": abrt_cnt,
                "GOOD_CNT": good_cnt, "FUNC_CNT": func_cnt
            })
            return parsed

        elif (record_type, sub_type) == (2, 30):  # WCR
            wafr_siz = struct.unpack(">f", data[0:4])[0]
            die_ht = struct.unpack(">f", data[4:8])[0]
            die_wid = struct.unpack(">f", data[8:12])[0]
            wf_units = data[12]
            wf_flat = chr(data[13])
            center_x = struct.unpack(">h", data[14:16])[0]
            center_y = struct.unpack(">h", data[16:18])[0]
            pos_x = chr(data[18])
            pos_y = chr(data[19])
            parsed.update({
                "WAFR_SIZ": wafr_siz, "DIE_HT": die_ht,
                "DIE_WID": die_wid, "WF_UNITS": wf_units,
                "WF_FLAT": wf_flat, "CENTER_X": center_x,
                "CENTER_Y": center_y, "POS_X": pos_x, "POS_Y": pos_y
            })
            return parsed

        elif (record_type, sub_type) == (5, 15):  # PIR
            head_num, site_num = struct.unpack("BB", data[0:2])
            parsed.update({"HEAD_NUM": head_num, "SITE_NUM": site_num})
            return parsed

        elif (record_type, sub_type) == (10, 30):  # TSR
            head_num, site_num = struct.unpack("BB", data[0:2])
            test_typ = chr(data[2])
            test_num = struct.unpack(">I", data[3:7])[0]
            exec_cnt = struct.unpack(">I", data[7:11])[0]
            fail_cnt = struct.unpack(">I", data[11:15])[0]
            alarm_cnt = struct.unpack(">I", data[15:19])[0]
            parsed.update({
                "HEAD_NUM": head_num, "SITE_NUM": site_num,
                "TEST_TYP": test_typ, "TEST_NUM": test_num,
                "EXEC_CNT": exec_cnt, "FAIL_CNT": fail_cnt, "ALARM_CNT": alarm_cnt
            })
            return parsed

        elif (record_type, sub_type) == (15, 15):  # MPR
            test_num = struct.unpack(">I", data[0:4])[0]
            head_num, site_num = struct.unpack("BB", data[4:6])
            rtn_cnt = struct.unpack(">H", data[8:10])[0]
            rslt_cnt = struct.unpack(">H", data[10:12])[0]
            parsed.update({
                "TEST_NUM": test_num, "HEAD_NUM": head_num,
                "SITE_NUM": site_num, "RTN_CNT": rtn_cnt, "RSLT_CNT": rslt_cnt
            })
            return parsed

        elif (record_type, sub_type) == (15, 10):  # FTR
            test_num = struct.unpack(">I", data[0:4])[0]
            head_num, site_num = struct.unpack("BB", data[4:6])
            result = struct.unpack(">f", data[18:22])[0]
            parsed.update({
                "TEST_NUM": test_num, "HEAD_NUM": head_num,
                "SITE_NUM": site_num, "RESULT": result
            })
            return parsed

        elif (record_type, sub_type) == (5, 30):  # BPS
            parsed.update({"INFO": "Begin Program Section"})
            return parsed

        elif (record_type, sub_type) == (5, 40):  # EPS
            parsed.update({"INFO": "End Program Section"})
            return parsed

        elif (record_type, sub_type) == (1, 91):  # GDR
            if len(data) >= 2:
                field_count = struct.unpack(">H", data[0:2])[0]
                parsed.update({"GENERIC_FIELD_COUNT": field_count, "INFO": "Generic Data Record"})
            return parsed

        elif (record_type, sub_type) == (1, 92):  # DTR
            if len(data) >= 2:
                text_len = struct.unpack(">H", data[0:2])[0]
                if len(data) >= 2 + text_len:
                    d_text = data[2:2+text_len].decode(errors="ignore")
                    parsed.update({"DATALOG_TEXT": d_text})
            return parsed

        parsed["NOTE"] = "Record type implemented without additional safety checks here."
    except Exception as e:
        print(f"❌ Error parsing ({record_type},{sub_type}) - {record_map.get((record_type, sub_type), 'Unknown')} - {e}")
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

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("用法: python stdf_parser.py <輸入STDF檔> <輸出CSV檔>")
    else:
        parse_stdf(sys.argv[1], sys.argv[2])
