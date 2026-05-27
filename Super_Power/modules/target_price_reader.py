import streamlit as st
import pandas as pd
import re
from rapidfuzz import fuzz
from itertools import combinations
import difflib
from openpyxl import load_workbook
from io import BytesIO

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Target Price Processor", layout="wide")
st.title("⚡ Target Price Processing System")

# =========================
# FUNCTIONS
# =========================

def clean_string(s):
    if pd.isna(s):
        return ""
    s = re.sub(r'\s+', ' ', str(s)).strip()
    s = s.replace('\u00A0', ' ')
    return s.lower()


def highlight_diff(s1, s2):
    seq = difflib.SequenceMatcher(None, s1, s2)
    out = []

    for tag, i1, i2, j1, j2 in seq.get_opcodes():
        if tag == "equal":
            out.append(s1[i1:i2])
        elif tag in ("replace", "delete"):
            out.append(f"[{s1[i1:i2]}]")
        elif tag == "insert":
            out.append(f"(+{s2[j1:j2]})")

    return "".join(out)


def detect_similar(strings, threshold=80):
    unique = list(dict.fromkeys(strings))
    pairs = []

    for s1, s2 in combinations(unique, 2):
        score = fuzz.ratio(s1, s2)
        if threshold <= score < 100:
            pairs.append((s1, s2, score, highlight_diff(s1, s2)))

    return pairs


SIM_THRESHOLD = 90

def build_segment(row, prefix, pm_value, schemetitle_value):
    similarity = fuzz.token_set_ratio(str(schemetitle_value), str(row["Line"]))
    scheme_part = "" if similarity >= SIM_THRESHOLD else f"{schemetitle_value} - "

    line_section_similarity = fuzz.token_set_ratio(str(row["Line"]), str(row["Section"]))
    section_part = "" if line_section_similarity >= SIM_THRESHOLD else f" - {row['Section']}"

    return f"{prefix}{pm_value} - {scheme_part}{row['Circuit']} - {row['Line']}{section_part}"


def process_sheet(df, sheet_name, pm_value, schemetitle_value):
    df["Line"] = df["Line"].astype(str).apply(clean_string)

    # detect similarity (for display only)
    similar = detect_similar(df["Line"].tolist())

    if similar:
        st.warning(f"⚠ Similar lines detected in {sheet_name}")

        for s1, s2, score, diff in similar:
            choice = st.radio(
                f"{sheet_name} | {score}% similarity\n{s1} vs {s2}\n{diff}",
                ["Use first", "Use second", "Keep both"],
                key=f"{sheet_name}-{s1}-{s2}"
            )

            if choice == "Use first":
                df.loc[df["Line"].isin([s1, s2]), "Line"] = s1
            elif choice == "Use second":
                df.loc[df["Line"].isin([s1, s2]), "Line"] = s2

    df["Segment"] = df.apply(
        lambda r: build_segment(
            r,
            "M - " if sheet_name == "Pole Materials" else "C - ",
            pm_value,
            schemetitle_value
        ),
        axis=1
    )

    return df


# =========================
# FILE UPLOAD
# =========================

control_file = st.file_uploader("Upload Control File", type=["xlsx", "xlsm"])
tp_file = st.file_uploader("Upload Target Price File", type=["xlsx", "xlsm"])

if control_file and tp_file:

    wb_tp = load_workbook(tp_file, data_only=True)
    ws = wb_tp["Target"]

    pm_value = ws["D21"].value or "Unknown"
    schemetitle_value = ws["D4"].value or "Unknown"
    PID = ws["D22"].value or ""

    st.info(f"PM: {pm_value} | Scheme: {schemetitle_value}")

    sheets = ["Pole Materials", "OHL"]
    usecols = [1, 2, 3, 4, 6, 8, 9, 11, 13]

    all_data = []

    for sheet in sheets:
        df = pd.read_excel(tp_file, sheet_name=sheet, header=3, usecols=usecols)

        df.columns = [
            "Circuit", "Section", "Line", "ENID", "Item",
            "Work Description", "Span", "Quantity", "Comment"
        ]

        processed = process_sheet(df, sheet, pm_value, schemetitle_value)
        all_data.append(processed)

    tp_combined = pd.concat(all_data, ignore_index=True)

    # =========================
    # WRITE BACK TO CONTROL FILE
    # =========================

    wb = load_workbook(control_file, keep_vba=True)

    if "Auxiliar" in wb.sheetnames:
        ws_aux = wb["Auxiliar"]

        start = 4
        for i, row in tp_combined.iterrows():
            ws_aux.cell(start + i, 1, row["Segment"])
            ws_aux.cell(start + i, 2, row["ENID"])
            ws_aux.cell(start + i, 3, row["Work Description"])
            ws_aux.cell(start + i, 4, row["Quantity"])
            ws_aux.cell(start + i, 5, row["Span"])
            ws_aux.cell(start + i, 6, row["Item"])
            ws_aux.cell(start + i, 7, row["Comment"])

    # =========================
    # DOWNLOAD OUTPUT
    # =========================

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    st.download_button(
        "Download Updated Control File",
        output,
        file_name="updated_control.xlsm"
    )

else:
    st.info("Upload both files to continue")
