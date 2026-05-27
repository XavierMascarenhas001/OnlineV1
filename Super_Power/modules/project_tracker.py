import streamlit as st
import pandas as pd
import os
from io import BytesIO

# =========================================================
# STREAMLIT UI
# =========================================================

st.title("📊 Workbank Generator")

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

sheets = ["Ayrshire", "Lanark", "Glasgow"]

columns_needed = {
    "Scope": "Scope",
    "Job Name": "job name",
    "Circuit": "Circuit",
    "Control File": "Control file",
    "PID": "PID",
    "PO": "PO"
}

# =========================================================
# PROCESS BUTTON
# =========================================================

if st.button("🚀 Run Workbank Processing"):

    if not uploaded_file:
        st.warning("Please upload a file first.")
        st.stop()

    all_data = []

    for sheet in sheets:

        try:
            df = pd.read_excel(uploaded_file, sheet_name=sheet, header=1)

            df.columns = df.columns.str.strip()

            selected_cols = {}

            for col in df.columns:
                col_lower = col.lower()

                for key, val in columns_needed.items():
                    if val.lower() == col_lower:
                        selected_cols[col] = key

            if not selected_cols:
                st.warning(f"No matching columns in {sheet}")
                continue

            df = df[list(selected_cols.keys())]
            df.rename(columns=selected_cols, inplace=True)

            df.rename(columns={
                "Scope": "Project",
                "Circuit": "SegmentCode"
            }, inplace=True)

            df["shire"] = sheet

            all_data.append(df)

            st.success(f"Loaded {sheet}: {len(df)} rows")

        except Exception as e:
            st.error(f"Skipping sheet {sheet}: {e}")

    if not all_data:
        st.error("No data loaded.")
        st.stop()

    final_df = pd.concat(all_data, ignore_index=True)

    # =====================================================
    # FIX TYPES FOR PARQUET
    # =====================================================

    for col in final_df.columns:
        if final_df[col].dtype == "object":
            final_df[col] = final_df[col].astype("string")

    # Move shire first
    cols = list(final_df.columns)

    if "shire" in cols:
        cols.insert(0, cols.pop(cols.index("shire")))

    final_df = final_df[cols]

    # =====================================================
    # DOWNLOADS
    # =====================================================

    excel_buffer = BytesIO()
    final_df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    parquet_buffer = BytesIO()
    final_df.to_parquet(parquet_buffer, index=False)
    parquet_buffer.seek(0)

    st.success("✅ Processing complete")

    st.download_button(
        "📥 Download Excel (Workbank)",
        data=excel_buffer,
        file_name="workbank.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        "📥 Download Parquet (Workbank)",
        data=parquet_buffer,
        file_name="workbank.parquet",
        mime="application/octet-stream"
    )

else:
    st.info("Upload file and click Run Processing")
