import streamlit as st
import pandas as pd
from io import BytesIO

# =========================================================
#                    MAIN FUNCTION
# =========================================================

def run_merge_control_tracker():

    st.header("🔗 Merge Control Tracker")

    # =========================================================
    #                    FILE UPLOADERS
    # =========================================================

    aggregated_file = st.file_uploader(
        "Select CF_aggregated.parquet",
        type=["parquet"],
        key="agg_parquet"
    )

    tracker_file = st.file_uploader(
        "Select Project Tracker.parquet",
        type=["parquet"],
        key="tracker_parquet"
    )

    misc_file = st.file_uploader(
        "Select miscelaneous.parquet",
        type=["parquet"],
        key="misc_parquet"
    )

    # =========================================================
    #                    PROCESS BUTTON
    # =========================================================

    if st.button("🚀 Run Merge"):

        # -----------------------------
        # VALIDATION
        # -----------------------------

        if not aggregated_file:
            st.warning("Please upload CF_aggregated.parquet")
            st.stop()

        if not tracker_file:
            st.warning("Please upload Project Tracker.parquet")
            st.stop()

        if not misc_file:
            st.warning("Please upload miscelaneous.parquet")
            st.stop()

        # =========================================================
        #                    LOAD DATA
        # =========================================================

        try:
            agg_df = pd.read_parquet(aggregated_file)
            tracker_df = pd.read_parquet(tracker_file)
            misc_df = pd.read_parquet(misc_file)

            st.success("✅ Files loaded successfully")

        except Exception as e:
            st.error(f"❌ Error loading parquet files: {e}")
            st.stop()

        # =========================================================
        #                    CLEAN COLUMN NAMES
        # =========================================================

        for df in [agg_df, tracker_df, misc_df]:
            df.columns = df.columns.str.strip().str.lower()

        # =========================================================
        #                    NORMALIZE KEYS
        # =========================================================

        key_cols = ['shire', 'project', 'segmentcode']

        for col in key_cols:

            if col in agg_df.columns:
                agg_df[col] = (
                    agg_df[col]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

            if col in tracker_df.columns:
                tracker_df[col] = (
                    tracker_df[col]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

        # -----------------------------
        # TEXT NORMALIZATION
        # -----------------------------

        if 'segment' in agg_df.columns:
            agg_df['segment'] = (
                agg_df['segment']
                .astype(str)
                .str.lower()
            )

        if 'job name' in tracker_df.columns:
            tracker_df['job name'] = (
                tracker_df['job name']
                .astype(str)
                .str.lower()
            )

        # =========================================================
        #                    CREATE OUTPUT COLUMNS
        # =========================================================

        if 'pid' not in agg_df.columns:
            agg_df['pid'] = None

        if 'po' not in agg_df.columns:
            agg_df['po'] = None

        if 'material_code' not in agg_df.columns:
            agg_df['material_code'] = None

        # =========================================================
        #                    GROUP TRACKER
        # =========================================================

        try:
            tracker_groups = tracker_df.groupby(
                ['shire', 'project', 'segmentcode']
            )

        except Exception as e:
            st.error(f"❌ Error grouping tracker data: {e}")
            st.stop()

        # =========================================================
        #                    MATCH PID + PO
        # =========================================================

        progress_bar = st.progress(0)

        for i, row in agg_df.iterrows():

            key = (
                row.get('shire'),
                row.get('project'),
                row.get('segmentcode')
            )

            if key not in tracker_groups.groups:
                progress_bar.progress((i + 1) / len(agg_df))
                continue

            subset = tracker_groups.get_group(key)

            segment_text = str(
                row.get('segment', '')
            ).strip().lower()

            for _, trow in subset.iterrows():

                job_name = str(
                    trow.get('job name', '')
                ).strip().lower()

                if job_name and job_name in segment_text:

                    agg_df.at[i, 'pid'] = trow.get('pid')
                    agg_df.at[i, 'po'] = trow.get('po')

                    break

            progress_bar.progress((i + 1) / len(agg_df))

        # =========================================================
        #                    MATERIAL CODE
        # =========================================================

        try:

            required_cols = [
                'item',
                'column_1',
                'column_2',
                'column_3'
            ]

            missing_cols = []

            for col in required_cols:

                if (
                    col not in agg_df.columns
                    and col == 'item'
                ):
                    missing_cols.append(col)

                if (
                    col not in misc_df.columns
                    and col != 'item'
                ):
                    missing_cols.append(col)

            if missing_cols:

                st.warning(
                    f"⚠️ Missing columns: {missing_cols}"
                )

            else:

                agg_df['item'] = (
                    agg_df['item']
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                misc_df['column_1'] = (
                    misc_df['column_1']
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                item_to_column_3 = (
                    misc_df
                    .set_index('column_1')['column_3']
                    .to_dict()
                )

                item_to_column_2 = (
                    misc_df
                    .set_index('column_1')['column_2']
                    .to_dict()
                )

                agg_df['material_code'] = (
                    agg_df['item']
                    .map(item_to_column_3)
                )

                agg_df['MD Poling'] = (
                    agg_df['item']
                    .map(item_to_column_2)
                )

                st.success("✅ Material mapping completed")

        except Exception as e:
            st.error(f"❌ Material mapping error: {e}")

        # =========================================================
        #                    COLUMN ORDER
        # =========================================================

        def move_before(df, target, before):

            cols = list(df.columns)

            if target in cols and before in cols:

                cols.remove(target)

                idx = cols.index(before)

                cols.insert(idx, target)

                return df[cols]

            return df

        agg_df = move_before(
            agg_df,
            'material_code',
            'pid'
        )

        agg_df = move_before(
            agg_df,
            'po',
            'pid'
        )

        if 'MD Poling' in agg_df.columns:

            cols = [
                c for c in agg_df.columns
                if c != 'MD Poling'
            ] + ['MD Poling']

            agg_df = agg_df[cols]

        # =========================================================
        #                    PREVIEW
        # =========================================================

        st.success("✅ Merge completed")

        st.subheader("📋 Preview")

        st.dataframe(
            agg_df.head(50),
            use_container_width=True
        )

        # =========================================================
        #                    EXCEL OUTPUT
        # =========================================================

        excel_buffer = BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="xlsxwriter"
        ) as writer:

            agg_df.to_excel(
                writer,
                index=False,
                sheet_name="Merged"
            )

        excel_buffer.seek(0)

        st.download_button(
            label="📥 Download Excel",
            data=excel_buffer,
            file_name="master_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # =========================================================
        #                    PARQUET OUTPUT
        # =========================================================

        parquet_buffer = BytesIO()

        parquet_df = agg_df.copy()

        for col in parquet_df.select_dtypes(
            include=['object']
        ).columns:

            parquet_df[col] = (
                parquet_df[col]
                .astype(str)
            )

        parquet_df.to_parquet(
            parquet_buffer,
            index=False
        )

        parquet_buffer.seek(0)

        st.download_button(
            label="📥 Download Parquet",
            data=parquet_buffer,
            file_name="master_output.parquet",
            mime="application/octet-stream"
        )

    else:
        st.info("Upload the required parquet files and click Run Merge")
