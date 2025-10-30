import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(page_title="Biomarker Sample Barcode Lookup Web App", layout="centered")

st.title("🔬 Biomarker Sample Barcode Lookup Web App")
st.write("Upload your Excel file locally, and scan or enter a barcode.")

# Initialize session state for DataFrame
if "df" not in st.session_state:
    st.session_state.df = None

uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Only read file if first time uploading
        if st.session_state.df is None:
            df = pd.read_excel(uploaded_file)
            if "Scan_Status" not in df.columns:
                df["Scan_Status"] = ""
            st.session_state.df = df

        df = st.session_state.df  # always use session state

        st.success("✅ File loaded. Ready to scan.")

        # Optional preview
        with st.expander("🔍 Preview File Contents"):
            st.dataframe(df)

        # --- Barcode input using session_state ---
        if "barcode_input" not in st.session_state:
            st.session_state.barcode_input = ""

        # Text input linked to session_state (do NOT use 'value=')
        barcode_input = st.text_input(
            "🧪 Scan or type barcode:",
            key="barcode_input"
        )

        # Process barcode if not empty
        if barcode_input.strip() != "":
            current_barcode = barcode_input.strip()
            current_match = df[df['Barcode'].astype(str) == current_barcode]

            if current_match.empty:
                st.error("❌ No match found.")
            else:
                st.success("✅ Sample found:")

                # Update Scan_Status
                df.loc[df['Barcode'].astype(str) == current_barcode, 'Scan_Status'] = "Matched"
                st.session_state.df = df

                st.info(f"🗸 Scan status updated for barcode: {current_barcode}")

                # Columns to highlight
                highlight_cols = ["Screen ID", "Visit", "Sample Name"]

                def highlight_match(row):
                    if str(row['Barcode']) == current_barcode:
                        return ['background-color: yellow' if col in highlight_cols else '' for col in row.index]
                    else:
                        return ['' for _ in row.index]

                # Show current match on top
                st.subheader("🔹 Current Match(es)")
                st.dataframe(current_match.style.apply(highlight_match, axis=1))

                # Full table below
                st.subheader("📋 Full Table")
                st.dataframe(df.style.apply(highlight_match, axis=1))

            # --- CLEAR the input field safely ---
            st.session_state.barcode_input = ""

        # Download button preserving original formatting
        if df is not None and not df.empty:
            original_filename = uploaded_file.name
            new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")

            # Load original workbook
            uploaded_file.seek(0)
            wb = load_workbook(uploaded_file)
            ws = wb.active

            # Add Scan_Status column if not exist
            if "Scan_Status" not in [cell.value for cell in ws[1]]:
                ws.cell(row=1, column=ws.max_column + 1, value="Scan_Status")

            # Map headers to column index
            header = {cell.value: idx + 1 for idx, cell in enumerate(ws[1])}

            # Update Scan_Status values
            for i, val in enumerate(df['Scan_Status'], start=2):
                ws.cell(row=i, column=header["Scan_Status"], value=val)

            # Save workbook to BytesIO
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            st.download_button(
                label="💾 Download Updated Excel File",
                data=buffer,
                file_name=new_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

else:
    st.info("⬆️ Please upload an Excel file to begin.")
