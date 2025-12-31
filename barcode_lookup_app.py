import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

# ---------------------------------
# Page setup
# ---------------------------------
st.set_page_config(
    page_title="Biomarker Barcode Scanner",
    layout="centered"
)

st.title("🔬 Biomarker Sample Barcode Scanner")
st.write("Scan or type barcodes → they become removable bubbles → process all at once")

# ---------------------------------
# Session state
# ---------------------------------
if "df" not in st.session_state:
    st.session_state.df = None

if "barcode_tags" not in st.session_state:
    st.session_state.barcode_tags = []

if "matched_df" not in st.session_state:
    st.session_state.matched_df = pd.DataFrame()

if "missing_barcodes" not in st.session_state:
    st.session_state.missing_barcodes = []

# ---------------------------------
# Upload Excel
# ---------------------------------
uploaded_file = st.file_uploader(
    "📁 Upload your sample Excel file",
    type=["xlsx"]
)

if uploaded_file:
    try:
        if st.session_state.df is None:
            df = pd.read_excel(uploaded_file)

            if "Barcode" not in df.columns:
                st.error("❌ Excel must contain a 'Barcode' column.")
                st.stop()

            if "Scan_Status" not in df.columns:
                df["Scan_Status"] = ""

            df["Barcode"] = df["Barcode"].astype(str)
            st.session_state.df = df

        st.success("✅ File loaded. Ready to scan.")

        # ---------------------------------
        # START NEW SET
        # ---------------------------------
        if st.button("🆕 Start New Set"):
            st.session_state.barcode_tags = []
            st.session_state.matched_df = pd.DataFrame()
            st.session_state.missing_barcodes = []

        # ---------------------------------
        # SCAN / TYPE BARCODES
        # ---------------------------------
        st.subheader("🧪 Scan / Type Barcodes")

        barcode_input = st.text_input(
            "Scan or type barcode (Enter = add):",
            key="barcode_input"
        )

        if barcode_input:
            cleaned = barcode_input.strip()
            if cleaned and cleaned not in st.session_state.barcode_tags:
                st.session_state.barcode_tags.append(cleaned)
            st.session_state.barcode_input = ""  # Clear input after Enter

        # ---------------------------------
        # DISPLAY SCANNED BARCODES
        # ---------------------------------
        if st.session_state.barcode_tags:
            st.multiselect(
                "Scanned barcodes (click ❌ to remove):",
                options=st.session_state.barcode_tags,
                default=st.session_state.barcode_tags,
                key="barcode_tags"
            )

        # ---------------------------------
        # PROCESS ALL BARCODES
        # ---------------------------------
        if st.button("🚀 Process All Barcodes", use_container_width=True):

            if not st.session_state.barcode_tags:
                st.warning("⚠️ No barcodes to process.")
            else:
                df = st.session_state.df.copy()

                barcode_set = set(st.session_state.barcode_tags)
                df_set = set(df["Barcode"])

                matched = barcode_set & df_set
                missing = sorted(barcode_set - df_set)

                df.loc[df["Barcode"].isin(matched), "Scan_Status"] = "Matched"

                st.session_state.df = df
                st.session_state.matched_df = df[df["Barcode"].isin(matched)]
                st.session_state.missing_barcodes = missing

                st.success(f"✅ {len(matched)} matched | ❌ {len(missing)} missing")

        # ---------------------------------
        # RESULTS
        # ---------------------------------
        if not st.session_state.matched_df.empty:
            st.subheader("🔹 Matched Samples")

            def highlight_row(row):
                styles = [''] * len(row)
                for i, col in enumerate(row.index):
                    if col in ["Screen ID", "Visit", "Sample Name"]:
                        styles[i] = "background-color: yellow"
                return styles

            st.dataframe(
                st.session_state.matched_df.style.apply(highlight_row, axis=1),
                use_container_width=True
            )

        if st.session_state.missing_barcodes:
            st.subheader("❌ Missing Barcodes")
            st.code("\n".join(st.session_state.missing_barcodes))

        # ---------------------------------
        # DOWNLOAD UPDATED EXCEL
        # ---------------------------------
        original_filename = uploaded_file.name
        new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")

        uploaded_file.seek(0)
        wb = load_workbook(uploaded_file)
        ws = wb.active

        headers = [cell.value for cell in ws[1]]
        if "Scan_Status" not in headers:
            ws.cell(row=1, column=ws.max_column + 1, value="Scan_Status")

        header_map = {cell.value: i + 1 for i, cell in enumerate(ws[1])}

        for i, val in enumerate(st.session_state.df["Scan_Status"], start=2):
            ws.cell(row=i, column=header_map["Scan_Status"], value=val)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        st.download_button(
            "💾 Download Updated Excel",
            buffer,
            file_name=new_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")

else:
    st.info("⬆️ Upload an Excel file to begin.")
