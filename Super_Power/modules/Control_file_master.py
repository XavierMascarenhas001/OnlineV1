import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

# =========================================================
#                        FUNCTIONS
# =========================================================

def parse_excel_date(x):
    try:
        if pd.isna(x):
            return np.nan

        # Excel serial number
        if isinstance(x, (int, float)):
            return pd.to_datetime(
                x,
                origin="1899-12-30",
                unit="D",
                errors="coerce"
            )

        return pd.to_datetime(str(x), errors="coerce")

    except Exception:
        return np.nan


def parse_segment_info(segment_str, project_mapping, default_pm=""):

    if not isinstance(segment_str, str) or not segment_str.strip():
        return pd.Series([None, None, None, default_pm])

    segment_str = segment_str.strip()

    # Type
    type_match = re.match(r"^\s*([MC])\s*-\s*", segment_str)
    segment_type = type_match.group(1) if type_match else None

    # Code
    code_match = re.search(r"\b([A-Z]{0,3}\d{5})\b", segment_str)
    segment_code = code_match.group(1) if code_match else None

    # Description
    segment_desc = re.sub(r"^\s*[MC]\s*-\s*", "", segment_str)

    if segment_code:
        segment_desc = re.sub(
            re.escape(segment_code),
            "",
            segment_desc
        )

    segment_desc = segment_desc.strip(" -")

    # Project Manager
    project_manager = ""

    for pm in project_mapping:
        if pm.lower() in segment_str.lower():
            project_manager = pm
            break

    if not project_manager:
        project_manager = default_pm

    return pd.Series([
        segment_type,
        segment_desc,
        segment_code,
        project_manager
    ])


def extract_location(segment_desc, mapping_region):

    if not isinstance(segment_desc, str):
        return ""

    for key, loc in mapping_region.items():
        if key.lower() in segment_desc.lower():
            return ", ".join(loc)

    return ""


def map_teams(codes, teams):

    if pd.isna(codes):
        return "UNKNOWN"

    codes = str(codes).upper().strip()

    if codes in ["", "NAN"]:
        return "UNKNOWN"

    names = []

    for c in codes:
        if c in teams:
            names.extend(teams[c])

    return ", ".join(names) if names else "UNKNOWN"


# =========================================================
#                        MAPPINGS
# =========================================================

project_mapping = {
    "Jonathon Mcclung": ["Ayrshire", "PCB"],
    "Gary MacDonald": ["Ayrshire", "LV"],
    "Jim Gaffney": ["Lanark", "PCB"],
    "Calum Thomson": ["Ayrshire", "Connections"],
    "David Jamieson": ["Lanark", "11kV"],
}

mapping_region = {
    "Newmilns": ["Irvine Valley"],
    "Kilwinning": ["Kilwinning"],
    "Ayr": ["Ayr East", "Ayr West"],
}

teams = {
    "A": ["Paulo Marques"],
    "B": ["Rui Rocha"],
    "C": ["Craig Kerr"],
}

# =========================================================
#                        STREAMLIT PAGE
# =========================================================

st.set_page_config(
    page_title="Excel Aggregation System",
    layout="wide"
)

st.title("📊 Excel Aggregation System")

uploaded_files = st.file_uploader(
    "Upload Excel files",
    type=["xlsx", "xlsm", "xls", "xlsb"],
    accept_multiple_files=True
)

# =========================================================
#                        PROCESS BUTTON
# =========================================================

if st.button("🚀 Run Processing"):

    if not uploaded_files:
        st.warning("Please upload files first.")
        st.stop()

    aggregated_df = pd.DataFrame()
    resume_list_dfs = []

    progress_bar = st.progress(0)

    # =====================================================
    #                    PROCESS FILES
    # =====================================================

    for idx, file in enumerate(uploaded_files):

        file_name = file.name

        st.write(f"📘 Processing: {file_name}")

        ext = file_name.split(".")[-1].lower()

        read_engine = None

        if ext == "xlsb":
            read_engine = "pyxlsb"

        # =================================================
        #                    BLOCK1
        # =================================================

        try:

            file.seek(0)

            df = pd.read_excel(
                file,
                sheet_name="Block1",
                engine=read_engine
            )

            # Normalize columns
            df.columns = (
                df.columns
                .astype(str)
                .str.strip()
                .str.lower()
            )

            # Dates
            if "plan1" in df.columns:
                df["plan1"] = df["plan1"].apply(parse_excel_date)

            if "plan2" in df.columns:
                df["plan2"] = df["plan2"].apply(parse_excel_date)

            if "done" in df.columns:
                df["done"] = df["done"].apply(parse_excel_date)

            if "done" in df.columns and "plan1" in df.columns:
                df["datetouse"] = df["done"].combine_first(df["plan1"])

            # Segment parsing
            if "segment" in df.columns:

                df[
                    [
                        "type",
                        "segmentdesc",
                        "segmentcode",
                        "projectmanager"
                    ]
                ] = df["segment"].apply(
                    lambda x: parse_segment_info(
                        x,
                        project_mapping
                    )
                )

            # Team mapping
            if "team" in df.columns:

                df["team_name"] = df["team"].apply(
                    lambda x: map_teams(x, teams)
                )

            # Source file
            df["sourcefile"] = file_name

            aggregated_df = pd.concat(
                [aggregated_df, df],
                ignore_index=True
            )

            st.success(f"✅ Block1 loaded: {len(df)} rows")

        except Exception as e:

            st.error(f"❌ Block1 error in {file_name}: {e}")

        # =================================================
        #                    PA CONTROL
        # =================================================

        try:

            file.seek(0)

            pa_df = pd.read_excel(
                file,
                sheet_name="PA CONTROL",
                engine=read_engine
            )

            # Keep only first 3 columns safely
            pa_df = pa_df.iloc[:, :3]

            pa_df.columns = [
                "section",
                "value_eur",
                "completion"
            ]

            # Keep only MC sections
            pa_df = pa_df[
                pa_df["section"]
                .astype(str)
                .str.match(r"^[MC]", na=False)
            ]

            # Numeric conversion
            pa_df["value_eur"] = pd.to_numeric(
                pa_df["value_eur"],
                errors="coerce"
            )

            pa_df["completion"] = pd.to_numeric(
                pa_df["completion"],
                errors="coerce"
            )

            # Percent complete
            pa_df["%complete"] = (
                pa_df["completion"] /
                pa_df["value_eur"].replace(0, np.nan)
            ) * 100

            pa_df["sourcefile"] = file_name

            resume_list_dfs.append(pa_df)

            st.success(f"✅ PA CONTROL loaded: {len(pa_df)} rows")

        except Exception as e:

            st.warning(f"⚠️ PA CONTROL error in {file_name}: {e}")

        # =================================================
        #                    PROGRESS
        # =================================================

        progress_bar.progress(
            int(((idx + 1) / len(uploaded_files)) * 100)
        )

    # =====================================================
    #                    OUTPUTS
    # =====================================================

    if aggregated_df.empty:

        st.warning("⚠️ No valid data found.")
        st.stop()

    # Sort by date
    if "datetouse" in aggregated_df.columns:

        aggregated_df = aggregated_df.sort_values(
            by="datetouse"
        ).reset_index(drop=True)

    st.success("✅ Processing complete!")

    # =====================================================
    #                    PREVIEW
    # =====================================================

    st.subheader("Preview")

    st.dataframe(
        aggregated_df.head(50),
        use_container_width=True
    )

    # =====================================================
    #                    EXCEL EXPORT
    # =====================================================

    excel_buffer = BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="xlsxwriter"
    ) as writer:

        aggregated_df.to_excel(
            writer,
            index=False,
            sheet_name="Aggregated"
        )

        if resume_list_dfs:

            resume_df = pd.concat(
                resume_list_dfs,
                ignore_index=True
            )

            resume_df.to_excel(
                writer,
                index=False,
                sheet_name="Resume"
            )

    excel_buffer.seek(0)

    st.download_button(
        label="📥 Download Excel",
        data=excel_buffer,
        file_name="aggregated_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # =====================================================
    #                    PARQUET EXPORT
    # =====================================================

    parquet_buffer = BytesIO()

    parquet_df = aggregated_df.copy()

    # Convert object columns
    for col in parquet_df.select_dtypes(include=["object"]).columns:
        parquet_df[col] = parquet_df[col].astype(str)

    parquet_df.to_parquet(
        parquet_buffer,
        index=False
    )

    parquet_buffer.seek(0)

    st.download_button(
        label="📥 Download Parquet",
        data=parquet_buffer,
        file_name="aggregated.parquet",
        mime="application/octet-stream"
    )

else:

    st.info("Upload files and click 'Run Processing'")
