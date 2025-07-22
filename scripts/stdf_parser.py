import struct
import csv

# Record Type and SubType mapping
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

def parse_cn(data_segment, current_offset, current_endian=">"):
    """Parses a Cn (character string) field from a data segment."""
    if current_offset >= len(data_segment):
        return "", current_offset

    try:
        length = struct.unpack(current_endian + "B", data_segment[current_offset:current_offset+1])[0]
        current_offset += 1

        end_offset = current_offset + length
        if end_offset > len(data_segment):
            # Data is truncated, return what's available
            val = data_segment[current_offset:].decode(errors="ignore")
            return val, len(data_segment)
        else:
            val = data_segment[current_offset:end_offset].decode(errors="ignore")
            return val, end_offset
    except Exception as e:
        return "", current_offset

def parse_record(record_type, sub_type, data, current_endian):
    """Parses a specific STDF record based on its type and sub-type."""
    parsed = {"TYPE": record_map.get((record_type, sub_type), f"{record_type}:{sub_type}")}
    record_data_offset = 0 # Offset within the 'data' segment of the current record

    print(f"DEBUG: Parsing record (Type:{record_type}, SubType:{sub_type}) with {len(data)} bytes of data. Endianness: {current_endian}")

    try:
        # --- Type 0 (Information & Setup Records) ---
        if (record_type, sub_type) == (0, 10):  # FAR - File Attributes Record
            print(f"DEBUG FAR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) >= 2:
                cpu_type = data[0]
                stdf_ver = data[1]
                parsed.update({
                    "CPU_TYPE": cpu_type,
                    "STDF_VER": stdf_ver
                })
            else:
                parsed["ERROR"] = f"FAR record too short: {len(data)} bytes"
            return parsed

        elif (record_type, sub_type) == (0, 20):  # ATR - Audit Trail Record
            print(f"DEBUG ATR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) >= 4:
                mod_time = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG ATR: Parsed MOD_TIM, offset now {record_data_offset}")
                cmd_line, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG ATR: Parsed CMD_LINE, offset now {record_data_offset}")
                parsed.update({"MOD_TIM": mod_time, "CMD_LINE": cmd_line})
            else:
                parsed["ERROR"] = f"ATR record too short: {len(data)} bytes"
            return parsed

        # --- Type 1 (Part Count & Test Information Records) ---
        elif (record_type, sub_type) == (1, 10):  # MIR - Master Information Record
            print(f"DEBUG MIR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) < 40: # Minimum length for fixed fields before Cn
                parsed["ERROR"] = f"MIR record too short for fixed fields: {len(data)} bytes"
                return parsed

            tstamp = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG MIR: Parsed TSTMP, offset now {record_data_offset}")

            mode, rtstfl, prog_sf, rsrv_4 = struct.unpack(current_endian + "BBBB", data[record_data_offset:record_data_offset+4])
            record_data_offset += 4
            print(f"DEBUG MIR: Parsed MODE, RTSTFL, PROG_SF, RSRV_4, offset now {record_data_offset}")

            cpgm_tim = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG MIR: Parsed CPGM_TIM, offset now {record_data_offset}")

            artc_fields_format = current_endian + "HHHHHIHHHHHI" # 5xU2, U4, 5xU2, U4 (28 bytes)
            if record_data_offset + struct.calcsize(artc_fields_format) > len(data):
                parsed["ERROR"] = f"MIR record too short for ARTC fields: {len(data)} bytes"
                return parsed

            (artc_cnt, artc_res, artc_rst, artc_mod, artc_exm, artc_bin,
             artc_cnt_m, artc_rs_m, artc_rst_m, artc_mod_m, artc_exm_m, artc_bin_m) = \
                struct.unpack(artc_fields_format, data[record_data_offset:record_data_offset + struct.calcsize(artc_fields_format)])
            record_data_offset += struct.calcsize(artc_fields_format)
            print(f"DEBUG MIR: Parsed all ARTC fields, offset now {record_data_offset}")


            sblot_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed SBLOT_ID '{sblot_id}', offset now {record_data_offset}")
            lot_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed LOT_ID '{lot_id}', offset now {record_data_offset}")
            part_typ, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed PART_TYP '{part_typ}', offset now {record_data_offset}")
            node_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed NODE_NAM '{node_nam}', offset now {record_data_offset}")
            tst_dev, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed TST_DEV '{tst_dev}', offset now {record_data_offset}")
            job_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed JOB_NAM '{job_nam}', offset now {record_data_offset}")
            job_rev, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed JOB_REV '{job_rev}', offset now {record_data_offset}")
            spu_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed SPU_ID '{spu_id}', offset now {record_data_offset}")
            test_cod, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed TEST_COD '{test_cod}', offset now {record_data_offset}")
            tst_temp, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed TST_TEMP '{tst_temp}', offset now {record_data_offset}")
            user_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed USER_TXT '{user_txt}', offset now {record_data_offset}")
            rsrv_30, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed RSRV_30 '{rsrv_30}', offset now {record_data_offset}")
            spec_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed SPEC_NAM '{spec_nam}', offset now {record_data_offset}")
            spec_ver, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed SPEC_VER '{spec_ver}', offset now {record_data_offset}")
            flow_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed FLOW_ID '{flow_id}', offset now {record_data_offset}")
            setup_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed SETUP_ID '{setup_id}', offset now {record_data_offset}")
            dsgn_rev, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed DSGN_REV '{dsgn_rev}', offset now {record_data_offset}")
            eng_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed ENG_ID '{eng_id}', offset now {record_data_offset}")
            rom_cod, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed ROM_COD '{rom_cod}', offset now {record_data_offset}")
            serl_num, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed SERL_NUM '{serl_num}', offset now {record_data_offset}")
            supr_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MIR: Parsed SUPR_NAM '{supr_nam}', offset now {record_data_offset}")


            parsed.update({
                "TIME_STAMP": tstamp, "MODE": mode, "RTSTFL": rtstfl, "PROG_SF": prog_sf, "RSRV_4": rsrv_4,
                "CPGM_TIM": cpgm_tim,
                "ARTC_CNT": artc_cnt, "ARTC_RES": artc_res, "ARTC_RST": artc_rst, "ARTC_MOD": artc_mod,
                "ARTC_EXM": artc_exm, "ARTC_BIN": artc_bin,
                "ARTC_CNT_M": artc_cnt_m, "ARTC_RS_M": artc_rs_m, "ARTC_RST_M": artc_rst_m,
                "ARTC_MOD_M": artc_mod_m, "ARTC_EXM_M": artc_exm_m, "ARTC_BIN_M": artc_bin_m,
                "SBLOT_ID": sblot_id, "LOT_ID": lot_id, "PART_TYP": part_typ, "NODE_NAM": node_nam,
                "TST_DEV": tst_dev, "JOB_NAM": job_nam, "JOB_REV": job_rev, "SPU_ID": spu_id,
                "TEST_COD": test_cod, "TST_TEMP": tst_temp, "USER_TXT": user_txt, "RSRV_30": rsrv_30,
                "SPEC_NAM": spec_nam, "SPEC_VER": spec_ver, "FLOW_ID": flow_id, "SETUP_ID": setup_id,
                "DSGN_REV": dsgn_rev, "ENG_ID": eng_id, "ROM_COD": rom_cod, "SERL_NUM": serl_num,
                "SUPR_NAM": supr_nam,
            })
            return parsed

        elif (record_type, sub_type) == (1, 20):  # MRR - Master Results Record
            print(f"DEBUG MRR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) < 4: # TSTMP is 4 bytes
                parsed["ERROR"] = f"MRR record too short: {len(data)} bytes"
                return parsed

            tstamp = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG MRR: Parsed TSTMP, offset now {record_data_offset}")

            if record_data_offset + (4*4) > len(data): # 4 U4 fields
                 parsed["ERROR"] = f"MRR record too short for RTST/ABRT/GOOD/FUNC_CNT fields: {len(data)} bytes"
                 return parsed

            rtst_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG MRR: Parsed RTST_CNT, offset now {record_data_offset}")
            abrt_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG MRR: Parsed ABRT_CNT, offset now {record_data_offset}")
            good_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG MRR: Parsed GOOD_CNT, offset now {record_data_offset}")
            func_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG MRR: Parsed FUNC_CNT, offset now {record_data_offset}")

            sblot_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MRR: Parsed SBLOT_ID '{sblot_id}', offset now {record_data_offset}")
            lot_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MRR: Parsed LOT_ID '{lot_id}', offset now {record_data_offset}")
            part_typ, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG MRR: Parsed PART_TYP '{part_typ}', offset now {record_data_offset}")

            parsed.update({
                "TIME_STAMP": tstamp,
                "RTST_CNT": rtst_cnt,
                "ABRT_CNT": abrt_cnt,
                "GOOD_CNT": good_cnt,
                "FUNC_CNT": func_cnt,
                "SBLOT_ID": sblot_id,
                "LOT_ID": lot_id,
                "PART_TYP": part_typ,
            })
            return parsed

        elif (record_type, sub_type) == (1, 30):  # PCR - Part Count Record
            print(f"DEBUG PCR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) >= 22: # 1+1+4*5 = 22 bytes
                head_num = data[record_data_offset]
                record_data_offset += 1
                print(f"DEBUG PCR: Parsed HEAD_NUM, offset now {record_data_offset}")
                site_num = data[record_data_offset]
                record_data_offset += 1
                print(f"DEBUG PCR: Parsed SITE_NUM, offset now {record_data_offset}")

                part_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG PCR: Parsed PART_CNT, offset now {record_data_offset}")
                retest_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG PCR: Parsed RETEST_CNT, offset now {record_data_offset}")
                abrt_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG PCR: Parsed ABRT_CNT, offset now {record_data_offset}")
                good_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG PCR: Parsed GOOD_CNT, offset now {record_data_offset}")
                func_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG PCR: Parsed FUNC_CNT, offset now {record_data_offset}")

                parsed.update({
                    "HEAD_NUM": head_num, "SITE_NUM": site_num, "PART_CNT": part_cnt,
                    "RETEST_CNT": retest_cnt, "ABRT_CNT": abrt_cnt, "GOOD_CNT": good_cnt, "FUNC_CNT": func_cnt
                })
            else:
                parsed["ERROR"] = f"PCR record too short: {len(data)} bytes"
            return parsed

        elif (record_type, sub_type) == (1, 40):  # HBR - Hardware Bin Record
            print(f"DEBUG HBR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) < 11: # 1+1+2+2+4+1 = 11 bytes minimum for fixed fields before Cn
                parsed["ERROR"] = f"HBR record too short for fixed fields: {len(data)} bytes"
                return parsed

            head_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG HBR: Parsed HEAD_NUM, offset now {record_data_offset}")
            site_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG HBR: Parsed SITE_NUM, offset now {record_data_offset}")
            hbr_nam = struct.unpack(current_endian + "H", data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG HBR: Parsed HBR_NAM, offset now {record_data_offset}")
            bin_num = struct.unpack(current_endian + "H", data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG HBR: Parsed BIN_NUM, offset now {record_data_offset}")
            bin_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG HBR: Parsed BIN_CNT, offset now {record_data_offset}")
            bin_pf = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG HBR: Parsed BIN_PF, offset now {record_data_offset}")

            scn_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian) # Optional Cn field
            print(f"DEBUG HBR: Parsed SCN_NAM '{scn_nam}', offset now {record_data_offset}")

            parsed.update({"HEAD_NUM": head_num, "SITE_NUM": site_num, "HBR_NAM": hbr_nam,
                           "BIN_NUM": bin_num, "BIN_CNT": bin_cnt, "BIN_PF": bin_pf,
                           "SCN_NAM": scn_nam})
            return parsed

        elif (record_type, sub_type) == (1, 70):  # RDR - Retest Data Record
            print(f"DEBUG RDR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) >= 2:
                num_bins = struct.unpack(current_endian + "H", data[record_data_offset:record_data_offset+2])[0]
                record_data_offset += 2
                print(f"DEBUG RDR: Parsed NUM_BINS, offset now {record_data_offset}")
                rtst_bin = []
                for i in range(num_bins):
                    if record_data_offset + 2 <= len(data):
                        rtst_bin.append(struct.unpack(current_endian + "H", data[record_data_offset:record_data_offset+2])[0])
                        record_data_offset += 2
                    else:
                        print(f"DEBUG RDR: Truncated RTST_BIN array at index {i}")
                        break # Truncated array
                print(f"DEBUG RDR: Parsed RTST_BIN array, offset now {record_data_offset}")
                parsed.update({"NUM_BINS": num_bins, "RTST_BIN": rtst_bin})
            else:
                parsed["ERROR"] = f"RDR record too short: {len(data)} bytes"
            return parsed

        elif (record_type, sub_type) == (1, 80):  # SDR - Site Description Record
            print(f"DEBUG SDR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) >= 3:
                head_num, site_grp, site_cnt = struct.unpack(current_endian + "BBB", data[record_data_offset:record_data_offset+3])
                record_data_offset += 3
                print(f"DEBUG SDR: Parsed HEAD_NUM, SITE_GRP, SITE_CNT, offset now {record_data_offset}")
                site_nums = []
                for i in range(site_cnt):
                    if record_data_offset + 1 <= len(data):
                        site_nums.append(data[record_data_offset])
                        record_data_offset += 1
                    else:
                        print(f"DEBUG SDR: Truncated SITE_NUM array at index {i}")
                        break # Truncated array
                print(f"DEBUG SDR: Parsed SITE_NUM array, offset now {record_data_offset}")
                parsed.update({"HEAD_NUM": head_num, "SITE_GRP": site_grp, "SITE_CNT": site_cnt, "SITE_NUM": site_nums})
            else:
                parsed["ERROR"] = f"SDR record too short: {len(data)} bytes"
            return parsed

        elif (record_type, sub_type) == (1, 91):  # GDR - Generic Data Record
            print(f"DEBUG GDR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) >= 2:
                field_count = struct.unpack(current_endian + "H", data[record_data_offset:record_data_offset+2])[0]
                record_data_offset += 2
                print(f"DEBUG GDR: Parsed FLD_CNT, offset now {record_data_offset}")
                parsed.update({"GENERIC_FIELD_COUNT": field_count, "INFO": "Generic Data Record (data not parsed)"})
            else:
                parsed["ERROR"] = f"GDR record too short: {len(data)} bytes"
            return parsed

        elif (record_type, sub_type) == (1, 92):  # DTR - Datalog Text Record
            print(f"DEBUG DTR: Data length {len(data)}, current offset {record_data_offset}")
            d_text, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG DTR: Parsed TEXT_DAT '{d_text}', offset now {record_data_offset}")
            parsed.update({"DATALOG_TEXT": d_text})
            return parsed

        # --- Type 2 (Wafer & Die Records) ---
        elif (record_type, sub_type) == (2, 10):  # WIR - Wafer Information Record
            print(f"DEBUG WIR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) < 6: # U1+U1+U4 = 6 bytes minimum before Cn
                parsed["ERROR"] = f"WIR record too short for fixed fields: {len(data)} bytes"
                return parsed

            head_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG WIR: Parsed HEAD_NUM, offset now {record_data_offset}")
            site_grp = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG WIR: Parsed SITE_GRP, offset now {record_data_offset}")
            start_t = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG WIR: Parsed START_T, offset now {record_data_offset}")

            wafer_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG WIR: Parsed WAFER_ID '{wafer_id}', offset now {record_data_offset}")
            parsed.update({"HEAD_NUM": head_num, "SITE_GRP": site_grp, "START_T": start_t, "WAFER_ID": wafer_id})
            return parsed

        elif (record_type, sub_type) == (2, 20):  # WRR - Wafer Results Record
            print(f"DEBUG WRR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) < 26: # 1+1+4*6 = 26 bytes minimum for fixed fields before Cn
                parsed["ERROR"] = f"WRR record too short for fixed fields: {len(data)} bytes"
                return parsed

            head_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG WRR: Parsed HEAD_NUM, offset now {record_data_offset}")
            site_grp = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG WRR: Parsed SITE_GRP, offset now {record_data_offset}")
            finish_t = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG WRR: Parsed FINISH_T, offset now {record_data_offset}")
            part_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG WRR: Parsed PART_CNT, offset now {record_data_offset}")
            rtst_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG WRR: Parsed RTST_CNT, offset now {record_data_offset}")
            abrt_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG WRR: Parsed ABRT_CNT, offset now {record_data_offset}")
            good_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG WRR: Parsed GOOD_CNT, offset now {record_data_offset}")
            func_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG WRR: Parsed FUNC_CNT, offset now {record_data_offset}")

            wafer_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG WRR: Parsed WAFER_ID '{wafer_id}', offset now {record_data_offset}")

            parsed.update({
                "HEAD_NUM": head_num, "SITE_GRP": site_grp, "FINISH_T": finish_t, "PART_CNT": part_cnt,
                "RTST_CNT": rtst_cnt, "ABRT_CNT": abrt_cnt, "GOOD_CNT": good_cnt, "FUNC_CNT": func_cnt,
                "WAFER_ID": wafer_id
            })
            return parsed

        elif (record_type, sub_type) == (2, 30):  # WCR - Wafer Configuration Record
            print(f"DEBUG WCR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) < 20: # 4*3 + 1*2 + 2*2 + 1*2 = 20 bytes
                parsed["ERROR"] = f"WCR record too short: {len(data)} bytes"
                return parsed

            wafr_siz = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG WCR: Parsed WAFR_SIZ, offset now {record_data_offset}")
            die_ht = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG WCR: Parsed DIE_HT, offset now {record_data_offset}")
            die_wid = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG WCR: Parsed DIE_WID, offset now {record_data_offset}")
            wf_units = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG WCR: Parsed WF_UNITS, offset now {record_data_offset}")
            wf_flat = chr(data[record_data_offset])
            record_data_offset += 1
            print(f"DEBUG WCR: Parsed WF_FLAT, offset now {record_data_offset}")
            center_x = struct.unpack(current_endian + "h", data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG WCR: Parsed CENTER_X, offset now {record_data_offset}")
            center_y = struct.unpack(current_endian + "h", data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG WCR: Parsed CENTER_Y, offset now {record_data_offset}")
            pos_x = chr(data[record_data_offset])
            record_data_offset += 1
            print(f"DEBUG WCR: Parsed POS_X, offset now {record_data_offset}")
            pos_y = chr(data[record_data_offset])
            record_data_offset += 1
            print(f"DEBUG WCR: Parsed POS_Y, offset now {record_data_offset}")

            parsed.update({
                "WAFR_SIZ": wafr_siz, "DIE_HT": die_ht, "DIE_WID": die_wid, "WF_UNITS": wf_units,
                "WF_FLAT": wf_flat, "CENTER_X": center_x, "CENTER_Y": center_y, "POS_X": pos_x, "POS_Y": pos_y
            })
            return parsed

        # --- Type 5 (Test & Result Records) ---
        elif (record_type, sub_type) == (5, 10):  # PTR - Parametric Test Record
            print(f"DEBUG PTR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) < 12: # U4+U1+U1+B1+B1+R4 = 12 bytes minimum for required fixed fields.
                parsed["ERROR"] = f"PTR record too short for required fixed fields: {len(data)} bytes"
                return parsed

            test_num = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG PTR: Parsed TEST_NUM, offset now {record_data_offset}")
            head_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG PTR: Parsed HEAD_NUM, offset now {record_data_offset}")
            site_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG PTR: Parsed SITE_NUM, offset now {record_data_offset}")
            test_flg = data[record_data_offset] # B1
            record_data_offset += 1
            print(f"DEBUG PTR: Parsed TEST_FLG, offset now {record_data_offset}")
            parm_flg = data[record_data_offset] # B1
            record_data_offset += 1
            print(f"DEBUG PTR: Parsed PARM_FLG, offset now {record_data_offset}")
            result = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG PTR: Parsed RESULT, offset now {record_data_offset}")

            tsr_str = ""
            if record_data_offset < len(data):
                tsr_str, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed TSR_STR '{tsr_str}', offset now {record_data_offset}")

            test_nam = ""
            if record_data_offset < len(data):
                test_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed TEST_NAM '{test_nam}', offset now {record_data_offset}")

            seq_nam = ""
            if record_data_offset < len(data):
                seq_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed SEQ_NAM '{seq_nam}', offset now {record_data_offset}")

            test_txt = ""
            if record_data_offset < len(data):
                test_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed TEST_TXT '{test_txt}', offset now {record_data_offset}")

            alarm_id = ""
            if record_data_offset < len(data):
                alarm_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed ALARM_ID '{alarm_id}', offset now {record_data_offset}")

            prog_txt = ""
            if record_data_offset < len(data):
                prog_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed PROG_TXT '{prog_txt}', offset now {record_data_offset}")

            rslt_txt = ""
            if record_data_offset < len(data):
                rslt_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed RSLT_TXT '{rslt_txt}', offset now {record_data_offset}")

            llm_txt = ""
            if record_data_offset < len(data):
                llm_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed LLM_TXT '{llm_txt}', offset now {record_data_offset}")

            hl_txt = ""
            if record_data_offset < len(data):
                hl_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed HL_TXT '{hl_txt}', offset now {record_data_offset}")

            lo_limit = None
            if record_data_offset + 4 <= len(data):
                lo_limit = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG PTR: Parsed LO_LIMIT, offset now {record_data_offset}")

            hi_limit = None
            if record_data_offset + 4 <= len(data):
                hi_limit = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG PTR: Parsed HI_LIMIT, offset now {record_data_offset}")

            units = ""
            if record_data_offset < len(data):
                units, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed UNITS '{units}', offset now {record_data_offset}")

            c_resfmt = ""
            if record_data_offset < len(data):
                c_resfmt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed C_RESFMT '{c_resfmt}', offset now {record_data_offset}")

            c_unitfmt = ""
            if record_data_offset < len(data):
                c_unitfmt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG PTR: Parsed C_UNITFMT '{c_unitfmt}', offset now {record_data_offset}")

            lo_spec = None
            if record_data_offset + 4 <= len(data):
                lo_spec = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG PTR: Parsed LO_SPEC, offset now {record_data_offset}")

            hi_spec = None
            if record_data_offset + 4 <= len(data):
                hi_spec = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG PTR: Parsed HI_SPEC, offset now {record_data_offset}")

            parsed.update({
                "TEST_NUM": test_num, "HEAD_NUM": head_num, "SITE_NUM": site_num,
                "TEST_FLG": test_flg, "PARM_FLG": parm_flg, "RESULT": result,
                "TSR_STR": tsr_str, "TEST_NAM": test_nam, "SEQ_NAM": seq_nam, "TEST_TXT": test_txt,
                "ALARM_ID": alarm_id, "PROG_TXT": prog_txt, "RSLT_TXT": rslt_txt,
                "LLM_TXT": llm_txt, "HL_TXT": hl_txt,
                "LO_LIMIT": lo_limit, "HI_LIMIT": hi_limit, "UNITS": units,
                "C_RESFMT": c_resfmt, "C_UNITFMT": c_unitfmt,
                "LO_SPEC": lo_spec, "HI_SPEC": hi_spec
            })
            return parsed

        elif (record_type, sub_type) == (5, 15):  # PIR - Part Information Record
            print(f"DEBUG PIR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) >= 2:
                head_num = data[record_data_offset]
                record_data_offset += 1
                print(f"DEBUG PIR: Parsed HEAD_NUM, offset now {record_data_offset}")
                site_num = data[record_data_offset]
                record_data_offset += 1
                print(f"DEBUG PIR: Parsed SITE_NUM, offset now {record_data_offset}")
                parsed.update({"HEAD_NUM": head_num, "SITE_NUM": site_num})
            else:
                parsed["ERROR"] = f"PIR record too short: {len(data)} bytes"
            return parsed

        elif (record_type, sub_type) == (5, 20):  # PRR - Part Results Record
            print(f"DEBUG PRR: Data length {len(data)}, current offset {record_data_offset}")
            # 固定欄位長度：1+1+1+2+2+2+2+2+4 = 17 bytes
            if len(data) < 17:
                parsed["ERROR"] = f"PRR record too short for fixed fields: {len(data)} bytes"
                return parsed

            head_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG PRR: Parsed HEAD_NUM, offset now {record_data_offset}")

            site_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG PRR: Parsed SITE_NUM, offset now {record_data_offset}")

            part_flg = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG PRR: Parsed PART_FLG, offset now {record_data_offset}")

            # NUM_TEST 應為 2 bytes 的 U*2
            num_test = struct.unpack(current_endian + "H",
                                    data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG PRR: Parsed NUM_TEST, offset now {record_data_offset}")

            hard_bin = struct.unpack(current_endian + "H",
                                    data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG PRR: Parsed HARD_BIN, offset now {record_data_offset}")

            soft_bin = struct.unpack(current_endian + "H",
                                    data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG PRR: Parsed SOFT_BIN, offset now {record_data_offset}")

            x_coord = struct.unpack(current_endian + "h",
                                    data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG PRR: Parsed X_COORD, offset now {record_data_offset}")

            y_coord = struct.unpack(current_endian + "h",
                                    data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG PRR: Parsed Y_COORD, offset now {record_data_offset}")

            test_t = struct.unpack(current_endian + "I",
                                    data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG PRR: Parsed TEST_T, offset now {record_data_offset}")

            # Cn fields
            part_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG PRR: Parsed PART_ID '{part_id}', offset now {record_data_offset}")
            part_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG PRR: Parsed PART_TXT '{part_txt}', offset now {record_data_offset}")
            part_fix, record_data_offset = parse_cn(data, record_data_offset, current_endian)
            print(f"DEBUG PRR: Parsed PART_FIX '{part_fix}', offset now {record_data_offset}")

            parsed.update({
                "HEAD_NUM": head_num, "SITE_NUM": site_num, "PART_FLG": part_flg,
                "NUM_TEST": num_test, "HARD_BIN": hard_bin, "SOFT_BIN": soft_bin,
                "X_COORD": x_coord, "Y_COORD": y_coord, "TEST_T": test_t,
                "PART_ID": part_id, "PART_TXT": part_txt, "PART_FIX": part_fix
            })
            return parsed


        elif (record_type, sub_type) == (5, 30):  # BPS - Begin Program Section
            print(f"DEBUG BPS: Data length {len(data)}, current offset {record_data_offset}")
            parsed.update({"INFO": "Begin Program Section"})
            return parsed

        elif (record_type, sub_type) == (5, 40):  # EPS - End Program Section
            print(f"DEBUG EPS: Data length {len(data)}, current offset {record_data_offset}")
            parsed.update({"INFO": "End Program Section"})
            return parsed

        # --- Type 10 (Test & Result Records) ---
        elif (record_type, sub_type) == (10, 30):  # TSR - Test Summary Record
            print(f"DEBUG TSR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) < 19: # Fixed fields: 1+1+1+4+4+4+4 = 19 bytes
                parsed["ERROR"] = f"TSR record too short: {len(data)} bytes"
                return parsed

            head_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG TSR: Parsed HEAD_NUM, offset now {record_data_offset}")
            site_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG TSR: Parsed SITE_NUM, offset now {record_data_offset}")
            test_typ = chr(data[record_data_offset]) # C1
            record_data_offset += 1
            print(f"DEBUG TSR: Parsed TEST_TYP, offset now {record_data_offset}")
            test_num = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG TSR: Parsed TEST_NUM, offset now {record_data_offset}")
            exec_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG TSR: Parsed EXEC_CNT, offset now {record_data_offset}")
            fail_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG TSR: Parsed FAIL_CNT, offset now {record_data_offset}")
            alarm_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG TSR: Parsed ALARM_CNT, offset now {record_data_offset}")
            rsrv_3 = chr(data[record_data_offset]) # C1 (Reserved)
            record_data_offset += 1
            print(f"DEBUG TSR: Parsed RSRV_3, offset now {record_data_offset}")


            test_nam = ""
            if record_data_offset < len(data):
                test_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG TSR: Parsed TEST_NAM '{test_nam}', offset now {record_data_offset}")

            seq_nam = ""
            if record_data_offset < len(data):
                seq_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG TSR: Parsed SEQ_NAM '{seq_nam}', offset now {record_data_offset}")

            test_lbl = ""
            if record_data_offset < len(data):
                test_lbl, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG TSR: Parsed TEST_LBL '{test_lbl}', offset now {record_data_offset}")

            test_txt = ""
            if record_data_offset < len(data):
                test_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG TSR: Parsed TEST_TXT '{test_txt}', offset now {record_data_offset}")

            alarm_id = ""
            if record_data_offset < len(data):
                alarm_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG TSR: Parsed ALARM_ID '{alarm_id}', offset now {record_data_offset}")

            opt_flag = None
            if record_data_offset + 1 <= len(data):
                opt_flag = data[record_data_offset] # B1
                record_data_offset += 1
                print(f"DEBUG TSR: Parsed OPT_FLAG, offset now {record_data_offset}")

            res_scal = None
            if record_data_offset + 1 <= len(data):
                res_scal = struct.unpack(current_endian + "b", data[record_data_offset:record_data_offset+1])[0] # I1 (signed char)
                record_data_offset += 1
                print(f"DEBUG TSR: Parsed RES_SCAL, offset now {record_data_offset}")

            llm_scal = None
            if record_data_offset + 1 <= len(data):
                llm_scal = struct.unpack(current_endian + "b", data[record_data_offset:record_data_offset+1])[0]
                record_data_offset += 1
                print(f"DEBUG TSR: Parsed LLM_SCAL, offset now {record_data_offset}")

            hl_scal = None
            if record_data_offset + 1 <= len(data):
                hl_scal = struct.unpack(current_endian + "b", data[record_data_offset:record_data_offset+1])[0]
                record_data_offset += 1
                print(f"DEBUG TSR: Parsed HL_SCAL, offset now {record_data_offset}")

            lo_limit = None
            if record_data_offset + 4 <= len(data):
                lo_limit = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG TSR: Parsed LO_LIMIT, offset now {record_data_offset}")

            hi_limit = None
            if record_data_offset + 4 <= len(data):
                hi_limit = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG TSR: Parsed HI_LIMIT, offset now {record_data_offset}")

            units = ""
            if record_data_offset < len(data):
                units, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG TSR: Parsed UNITS '{units}', offset now {record_data_offset}")

            c_resfmt = ""
            if record_data_offset < len(data):
                c_resfmt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG TSR: Parsed C_RESFMT '{c_resfmt}', offset now {record_data_offset}")

            c_unitfmt = ""
            if record_data_offset < len(data):
                c_unitfmt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG TSR: Parsed C_UNITFMT '{c_unitfmt}', offset now {record_data_offset}")

            lo_spec = None
            if record_data_offset + 4 <= len(data):
                lo_spec = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG TSR: Parsed LO_SPEC, offset now {record_data_offset}")

            hi_spec = None
            if record_data_offset + 4 <= len(data):
                hi_spec = struct.unpack(current_endian + "f", data[record_data_offset:record_data_offset+4])[0]
                record_data_offset += 4
                print(f"DEBUG TSR: Parsed HI_SPEC, offset now {record_data_offset}")


            parsed.update({
                "HEAD_NUM": head_num, "SITE_NUM": site_num, "TEST_TYP": test_typ, "TEST_NUM": test_num,
                "EXEC_CNT": exec_cnt, "FAIL_CNT": fail_cnt, "ALARM_CNT": alarm_cnt, "RSRV_3": rsrv_3,
                "TEST_NAM": test_nam, "SEQ_NAM": seq_nam, "TEST_LBL": test_lbl, "TEST_TXT": test_txt,
                "ALARM_ID": alarm_id, "OPT_FLAG": opt_flag, "RES_SCAL": res_scal, "LLM_SCAL": llm_scal,
                "HL_SCAL": hl_scal, "LO_LIMIT": lo_limit, "HI_LIMIT": hi_limit, "UNITS": units,
                "C_RESFMT": c_resfmt, "C_UNITFMT": c_unitfmt, "LO_SPEC": lo_spec, "HI_SPEC": hi_spec
            })
            return parsed

        # --- Type 15 (Test & Result Records) ---
        elif (record_type, sub_type) == (15, 10):  # FTR - Functional Test Record
            print(f"DEBUG FTR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) < 22: # Min fixed fields: U4+U1+U1+B1+B1+U4+U4+U4 = 22 bytes
                parsed["ERROR"] = f"FTR record too short for fixed fields: {len(data)} bytes"
                return parsed

            test_num = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG FTR: Parsed TEST_NUM, offset now {record_data_offset}")
            head_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG FTR: Parsed HEAD_NUM, offset now {record_data_offset}")
            site_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG FTR: Parsed SITE_NUM, offset now {record_data_offset}")
            test_flg = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG FTR: Parsed TEST_FLG, offset now {record_data_offset}")
            op_flg = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG FTR: Parsed OP_FLG, offset now {record_data_offset}")
            cycl_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG FTR: Parsed CYCL_CNT, offset now {record_data_offset}")
            fail_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG FTR: Parsed FAIL_CNT, offset now {record_data_offset}")
            alarm_cnt = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG FTR: Parsed ALARM_CNT, offset now {record_data_offset}")

            test_nam = ""
            if record_data_offset < len(data):
                test_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG FTR: Parsed TEST_NAM '{test_nam}', offset now {record_data_offset}")

            seq_nam = ""
            if record_data_offset < len(data):
                seq_nam, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG FTR: Parsed SEQ_NAM '{seq_nam}', offset now {record_data_offset}")

            test_txt = ""
            if record_data_offset < len(data):
                test_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG FTR: Parsed TEST_TXT '{test_txt}', offset now {record_data_offset}")

            alarm_id = ""
            if record_data_offset < len(data):
                alarm_id, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG FTR: Parsed ALARM_ID '{alarm_id}', offset now {record_data_offset}")

            prog_txt = ""
            if record_data_offset < len(data):
                prog_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG FTR: Parsed PROG_TXT '{prog_txt}', offset now {record_data_offset}")

            rslt_txt = ""
            if record_data_offset < len(data):
                rslt_txt, record_data_offset = parse_cn(data, record_data_offset, current_endian)
                print(f"DEBUG FTR: Parsed RSLT_TXT '{rslt_txt}', offset now {record_data_offset}")

            parsed.update({
                "TEST_NUM": test_num, "HEAD_NUM": head_num, "SITE_NUM": site_num,
                "TEST_FLG": test_flg, "OP_FLG": op_flg, "CYCL_CNT": cycl_cnt,
                "FAIL_CNT": fail_cnt, "ALARM_CNT": alarm_cnt,
                "TEST_NAM": test_nam, "SEQ_NAM": seq_nam, "TEST_TXT": test_txt,
                "ALARM_ID": alarm_id, "PROG_TXT": prog_txt, "RSLT_TXT": rslt_txt
            })
            return parsed

        elif (record_type, sub_type) == (15, 15):  # MPR - Multiple Pin Result
            print(f"DEBUG MPR: Data length {len(data)}, current offset {record_data_offset}")
            if len(data) < 12: # Min fixed fields for your current implementation (U4+U1+U1+B1+B1+U2+U2)
                parsed["ERROR"] = f"MPR record too short: {len(data)} bytes"
                return parsed

            test_num = struct.unpack(current_endian + "I", data[record_data_offset:record_data_offset+4])[0]
            record_data_offset += 4
            print(f"DEBUG MPR: Parsed TEST_NUM, offset now {record_data_offset}")
            head_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG MPR: Parsed HEAD_NUM, offset now {record_data_offset}")
            site_num = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG MPR: Parsed SITE_NUM, offset now {record_data_offset}")
            test_flg = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG MPR: Parsed TEST_FLG, offset now {record_data_offset}")
            parm_flg = data[record_data_offset]
            record_data_offset += 1
            print(f"DEBUG MPR: Parsed PARM_FLG, offset now {record_data_offset}")
            rtn_cnt = struct.unpack(current_endian + "H", data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG MPR: Parsed RTN_CNT, offset now {record_data_offset}")
            rslt_cnt = struct.unpack(current_endian + "H", data[record_data_offset:record_data_offset+2])[0]
            record_data_offset += 2
            print(f"DEBUG MPR: Parsed RSLT_CNT, offset now {record_data_offset}")

            parsed.update({
                "TEST_NUM": test_num, "HEAD_NUM": head_num, "SITE_NUM": site_num,
                "TEST_FLG": test_flg, "PARM_FLG": parm_flg,
                "RTN_CNT": rtn_cnt, "RSLT_CNT": rslt_cnt
            })
            return parsed

        # Fallback for unimplemented or unrecognized records
        print(f"DEBUG: Record type ({record_type},{sub_type}) is implemented partially or not fully parsed yet. Remaining data length: {len(data) - record_data_offset}")
        parsed["NOTE"] = f"Record type ({record_type},{sub_type}) implemented partially or not fully parsed. Raw Data Hex: {data[record_data_offset:].hex()}"

    except Exception as e:
        print(f"❌ Error parsing ({record_type},{sub_type}) - {record_map.get((record_type, sub_type), 'Unknown')} - {e}")
        print(f"  --> Failed at record_data_offset: {record_data_offset}/{len(data)}")
        print(f"  --> Raw Data (hex): {data.hex()}")
        parsed["ERROR"] = str(e)
        parsed["FULL_DATA_HEX"] = data.hex()
        parsed["PARSED_UP_TO_OFFSET_IN_RECORD"] = record_data_offset

    return parsed

def parse_stdf(filepath, output_csv):
    with open(filepath, "rb") as f:
        binary = f.read()

    offset = 0
    parsed_rows = []
    all_fields = set()
    current_file_endian = ">" # Default to Big-Endian

    print(f"⌛️ 開始解析 STDF 檔案: {filepath}")

    # Special handling for FAR (File Attributes Record) to determine endianness
    # FAR is always the first record in a valid STDF file.
    if len(binary) >= 4:
        # Attempt to read FAR header with both Big-Endian and Little-Endian to see which is valid
        # We need to consider that the 'reclen' itself is affected by endianness.
        reclen_be, rectype_be, recsub_be = (0,0,0)
        reclen_le, rectype_le, recsub_le = (0,0,0)

        try:
            reclen_be, rectype_be, recsub_be = struct.unpack(">HBB", binary[0:4])
        except struct.error:
            pass # Not enough data or other issue for Big-Endian unpack

        try:
            reclen_le, rectype_le, recsub_le = struct.unpack("<HBB", binary[0:4])
        except struct.error:
            pass # Not enough data or other issue for Little-Endian unpack

        # Prioritize Little-Endian if it results in a FAR record with a small, valid length
        # A FAR record typically has a data length of 2 bytes (CPU_TYPE, STDF_VER).
        if rectype_le == 0 and recsub_le == 10 and reclen_le == 2:
            current_file_endian = "<"
            print("✅ 檢測到 STDF 檔案為 Little-Endian (小端模式).")
            # Now, parse the FAR using the determined Little-Endian
            far_data = binary[4 : 4 + reclen_le]
            far_parsed = parse_record(rectype_le, recsub_le, far_data, current_file_endian)
            parsed_rows.append(far_parsed)
            all_fields.update(far_parsed.keys())
            offset = 4 + reclen_le # Move offset past FAR

        # If Little-Endian wasn't a perfect match for FAR(0,10) with reclen=2,
        # then check if Big-Endian provides a valid FAR.
        # It's less likely if the initial error was reclen 12590, but worth checking for robustness.
        elif rectype_be == 0 and recsub_be == 10 and reclen_be == 2:
            current_file_endian = ">"
            print("✅ 檢測到 STDF 檔案為 Big-Endian (大端模式).")
            # Parse FAR using Big-Endian
            far_data = binary[4 : 4 + reclen_be]
            far_parsed = parse_record(rectype_be, recsub_be, far_data, current_file_endian)
            parsed_rows.append(far_parsed)
            all_fields.update(far_parsed.keys())
            offset = 4 + reclen_be # Move offset past FAR
        else:
            # If neither attempts yield a standard FAR(0,10) with reclen=2,
            # fall back to default Big-Endian and let the main loop attempt parsing.
            # This might happen if the file is truly odd or corrupted at the very beginning.
            print(f"⚠️ 第一個記錄不是標準 FAR(0,10) 且 reclen=2。預設為 Big-Endian。")
            print(f"   BE 嘗試: reclen={reclen_be}, type={rectype_be}, sub={recsub_be}")
            print(f"   LE 嘗試: reclen={reclen_le}, type={rectype_le}, sub={recsub_le}")

    else:
        print("⚠️ 檔案太短，無法讀取第一個記錄頭。")

    # Main loop for parsing all records
    while offset + 4 <= len(binary):
        try:
            # Use the determined endianness for all subsequent record headers
            # print(f"DEBUG: Reading next record header at offset {offset} with endianness '{current_file_endian}'")
            reclen, rectype, recsub = struct.unpack(current_file_endian + "HBB", binary[offset:offset+4])

            record_start_offset = offset

            # Basic sanity check for reclen to prevent reading beyond file
            if reclen < 0 or offset + 4 + reclen > len(binary):
                print(f"❌ 警告: 無效的記錄長度 {reclen} 或超出檔案範圍，於偏移量 {record_start_offset}。停止解析。")
                print(f"  --> 檔案總長度: {len(binary)} bytes. 預計讀取到: {offset + 4 + reclen}")
                # Optional: dump raw bytes around the error for manual inspection
                # print(f"  --> Data around error (hex): {binary[max(0, record_start_offset-10):min(len(binary), record_start_offset+10+4+reclen)].hex()}")
                break

            print(f"--- 讀取記錄頭: Type={rectype}, SubType={recsub}, Length={reclen} (Start Offset: {record_start_offset}) ---")

            offset += 4 # Move past header
            data = binary[offset:offset+reclen]
            offset += reclen # Move past data to next record header

            parsed = parse_record(rectype, recsub, data, current_file_endian)
            parsed_rows.append(parsed)
            all_fields.update(parsed.keys())
            print(f"✅ 成功解析記錄: TYPE={record_map.get((rectype, recsub), f'{rectype}:{recsub}')} (實際長度: {4 + reclen} bytes) at offset {record_start_offset}. Next record starts at {offset}")

        except struct.error as se:
            print(f"❌ struct 解包錯誤於偏移量 {offset}，可能位元組順序或資料損壞: {se}")
            # Try to dump raw bytes around the error
            error_data_start = max(0, offset - 10)
            error_data_end = min(len(binary), offset + 10)
            print(f"  --> Data around error (hex): {binary[error_data_start:error_data_end].hex()}")
            break
        except IndexError as ie:
            print(f"❌ 讀取資料超出檔案範圍於偏移量 {offset}，可能記錄長度有誤: {ie}")
            # Try to dump raw bytes around the error
            error_data_start = max(0, offset - 10)
            error_data_end = min(len(binary), offset + 10)
            print(f"  --> Data around error (hex): {binary[error_data_start:error_data_end].hex()}")
            break
        except Exception as e:
            print(f"❌ 泛型錯誤於偏移量 {offset}: {e}")
            # Try to dump raw bytes around the error
            error_data_start = max(0, offset - 10)
            error_data_end = min(len(binary), offset + 10)
            print(f"  --> Data around error (hex): {binary[error_data_start:error_data_end].hex()}")
            break

    # Write parsed data to CSV
    all_fields = sorted(list(all_fields))
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        writer.writeheader()
        for row in parsed_rows:
            cleaned_row = {k: v for k, v in row.items() if k in all_fields}
            writer.writerow(cleaned_row)

    print(f"✅ 解析完成，共 {len(parsed_rows)} 筆記錄，輸出為 {output_csv}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("用法: python your_script_name.py <輸入STDF檔> <輸出CSV檔>")
        print("範例: python stdf_parser.py input.stdf output.csv")
    else:
        parse_stdf(sys.argv[1], sys.argv[2])