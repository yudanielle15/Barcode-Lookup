import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(
    page_title="Biomarker Sample Barcode Lookup Web App",
    layout="centered"
)

st.title("🔬 Biomarker Sample Barcode Lookup Web App")
st.write("Upload your Excel file, continuously scan barcodes, then process them together.")

# ---------------------------
# Session state init
# ---------------------------
if "df" not in st.session_state:
    st.session_state.df = None

if "scanned_barcodes" not in st.session_state:
    st.session_state.scanned_barcodes = ""

# ---------------------------
# File upload
# ---------------------------
uploaded_file = st.file_uploader(
    "📁 Upload your sample Excel file",
    type=["xlsx"]
)

if uploaded_file:
    try:
        if st.session_state.df is None:
            df = pd.read_excel(uploaded_file)
            if "Scan_Status" not in df.columns:
                df["Scan_Status"] = ""
            st.session_state.df = df

        st.success("✅ File loaded. Ready for continuous scanning.")

        # ---------------------------
        # Barcode input (continuous)
        # ---------------------------
        st.subheader("🧪 Continuous Barcode Scanning")

        st.info(
            "Scan barcodes continuously. Each scan should appear on a new line. "
            "When finished, click **Process All Barcodes**."
        )

        barcode_text = st.text_area(
            "Scanned barcodes (one per line):",
            value=st.session_state.scanned_barcodes,
            height=200,
            placeholder="Scan barcode here...\nNext scan appears on a new line"
        )

        st.session_state.scanned_barcodes = barcode_text

        # ---------------------------
        # Process button
        # ---------------------------
        if st.button("▶️ Process All Barcodes"):
            df = st.session_state.df

            barcodes = [
                b.strip()
                for b in barcode_text.splitlines()
                if b.strip()
            ]

            if not barcodes:
                st.warning("⚠️ No barcodes to process.")
            else:
                found = []
                not_found = []
                duplicates = set()

                for b in barcodes:
                    matches = df['Barcode'].astype(str) == str(b)
                    if matches.any():
                        if df.loc[matches, 'Scan_Status'].eq("Matched").any():
                            duplicates.add(b)
                        else:
                            df.loc[matches, 'Scan_Status'] = "Matched"
                            found.append(b)
                    else:
                        not_found.append(b)

                st.session_state.df = df

                # ---------------------------
                # Results summary
                # ---------------------------
                st.subheader("📊 Scan Results")

                if found:
                    st.success(f"✅ Matched ({len(found)}): {', '.join(found)}")

                if duplicates:
                    st.warning(f"🔁 Already scanned: {', '.join(sorted(duplicates))}")

                if not_found:
                    st.error(f"❌ Not found ({len(not_found)}): {', '.join(not_found)}")

                # Clear input AFTER processing
                st.session_state.scanned_barcodes = ""

        # ---------------------------
        # Display updated table
        # ---------------------------
        st.subheader("📋 Updated Table")
        st.dataframe(st.session_state.df)

        # ---------------------------
        # Download updated Excel
        # ---------------------------
        st.subheader("💾 Download")

        original_filename = uploaded_file.name
        new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")

        uploaded_file.seek(0)
        wb = load_workbook(uploaded_file)
        ws = wb.active

        if "Scan_Status" not in [cell.value for cell in ws[1]]:
            ws.cell(row=1, column=ws.max_column + 1, value="Scan_Status")

        header = {cell.value: idx + 1 for idx, cell in enumerate(ws[1])}

        for i, val in enumerate(st.session_state.df["Scan_Status"], start=2):
            ws.cell(row=i, column=header["Scan_Status"], value=val)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        st.download_button(
            "⬇️ Download Updated Excel File",
            data=buffer,
            file_name=new_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

else:
    st.info("⬆️ Please upload an Excel file to begin.")
