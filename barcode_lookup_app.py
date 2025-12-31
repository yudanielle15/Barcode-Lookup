import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

# -------------------------------
# Page setup
# -------------------------------
st.set_page_config(
    page_title="Biomarker Sample Barcode Lookup Web App",
    layout="centered"
)

st.title("🔬 Biomarker Sample Barcode Lookup Web App")
st.write("Upload your Excel file, continuously scan barcodes, then process them in one click.")

# -------------------------------
# Session state initialization
# -------------------------------
if "df" not in st.session_state:
    st.session_state.df = None

if "scanned_barcodes_raw" not in st.session_state:
    st.session_state.scanned_barcodes_raw = ""

if "matched_df" not in st.session_state:
    st.session_state.matched_df = pd.DataFrame()

if "missing_barcodes" not in st.session_state:
    st.session_state.missing_barcodes = []

# -------------------------------
# Upload Excel file
# -------------------------------
uploaded_file = st.file_uploader(
    "📁 Upload your sample Excel file",
    type=["xlsx"]
)

if uploaded_file:
    try:
        if st.session_state.df is None:
            df = pd.read_excel(uploaded_file)

            if "Barcode" not in df.columns:
                st.error("❌ Excel file must contain a 'Barcode' column.")
                st.stop()

            if "Scan_Status" not in df.columns:
                df["Scan_Status"] = ""

            # Convert Barcode column to string once (performance)
            df["Barcode"] = df["Barcode"].astype(str)

            st.session_state.df = df

        st.success("✅ File loaded. Ready for continuous scanning.")

        # -------------------------------
        # Continuous barcode scanning
        # -------------------------------
        st.subheader("🧪 Continuous Barcode Scanning")

        st.text_area(
            "Scan barcodes (one per line):",
            height=220,
            placeholder="Scan barcode → Enter → Scan next → Enter",
            key="scanned_barcodes_raw"
        )

        # -------------------------------
        # Process button
        # -------------------------------
        process_clicked = st.button("🚀 Process Scanned Barcodes", use_container_width=True)

        if process_clicked:
            df = st.session_state.df.copy()

            # Clean & deduplicate barcodes
            scanned = [
                b.strip()
                for b in st.session_state.scanned_barcodes_raw.splitlines()
                if b.strip()
            ]
            scanned = list(set(scanned))

            if not scanned:
                st.warning("⚠️ No barcodes scanned.")
            else:
                barcode_set = set(scanned)
                df_barcode_set = set(df["Barcode"])

                matched_barcodes = barcode_set & df_barcode_set
                missing_barcodes = sorted(barcode_set - df_barcode_set)

                # Bulk update (FAST)
                df.loc[df["Barcode"].isin(matched_barcodes), "Scan_Status"] = "Matched"

                st.session_state.df = df
                st.session_state.missing_barcodes = missing_barcodes
                st.session_state.matched_df = df[df["Barcode"].isin(matched_barcodes)]

                st.success(f"✅ {len(matched_barcodes)} barcode(s) matched.")

                if missing_barcodes:
                    st.error(f"❌ {len(missing_barcodes)} barcode(s) not found.")

                # Clear input after processing
                st.session_state.scanned_barcodes_raw = ""

        # -------------------------------
        # Display matched samples
        # -------------------------------
        if not st.session_state.matched_df.empty:
            st.subheader("🔹 Matched Samples")

            def highlight_row(row):
                styles = [''] * len(row)
                highlight_cols = ['Screen ID', 'Visit', 'Sample Name']
                for i, col in enumerate(row.index):
                    if col in highlight_cols:
                        styles[i] = 'background-color: yellow'
                return styles

            st.dataframe(
                st.session_state.matched_df.style.apply(highlight_row, axis=1),
                use_container_width=True
            )

        # -------------------------------
        # Display missing barcodes
        # -------------------------------
        if st.session_state.missing_barcodes:
            st.subheader("❌ Missing Barcodes")
            st.code("\n".join(st.session_state.missing_barcodes))

        # -------------------------------
        # Full table (optional, collapsible)
        # -------------------------------
        with st.expander("📋 View Full Table"):
            st.dataframe(st.session_state.df, use_container_width=True)

        # -------------------------------
        # Download updated Excel
        # -------------------------------
        if st.session_state.df is not None:
            original_filename = uploaded_file.name
            new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")

            uploaded_file.seek(0)
            wb = load_workbook(uploaded_file)
            ws = wb.active

            headers = [cell.value for cell in ws[1]]
            if "Scan_Status" not in headers:
                ws.cell(row=1, column=ws.max_column + 1, value="Scan_Status")

            header_map = {
                cell.value: idx + 1
                for idx, cell in enumerate(ws[1])
            }

            for i, val in enumerate(st.session_state.df["Scan_Status"], start=2):
                ws.cell(row=i, column=header_map["Scan_Status"], value=val)

            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            st.download_button(
                label="💾 Download Updated Excel File",
                data=buffer,
                file_name=new_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

else:
    st.info("⬆️ Please upload an Excel file to begin.")
