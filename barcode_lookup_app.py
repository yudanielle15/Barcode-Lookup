import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(page_title="Biomarker Sample Barcode Lookup Web App", layout="centered")
st.title("🔬 Biomarker Sample Barcode Lookup Web App")
st.write("Upload your Excel file locally, and scan or enter a barcode.")

# Initialize session state for DataFrame and barcode input
if "df" not in st.session_state:
    st.session_state.df = None
if "barcode_input" not in st.session_state:
    st.session_state.barcode_input = ""
if "current_match" not in st.session_state:
    st.session_state.current_match = pd.DataFrame()

# Callback to clear input after pressing Enter
def clear_input():
    st.session_state.barcode_input = ""

# File uploader
uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Only read file if first time uploading
        if st.session_state.df is None:
            df = pd.read_excel(uploaded_file)
            if "Scan_Status" not in df.columns:
                df["Scan_Status"] = ""
            st.session_state.df = df
            st.success("✅ File loaded. Ready to scan.")

            # Optional preview
            with st.expander("🔍 Preview File Contents"):
                st.dataframe(st.session_state.df)

        df = st.session_state.df

        # Barcode input field
        barcode_input = st.text_input(
            "🧪 Scan or type barcode:",
            value=st.session_state.barcode_input,
            key="barcode_input",
            on_change=clear_input
        )

        # Process barcode input
        if barcode_input:
            current_match = df[df['Barcode'].astype(str) == str(barcode_input)]
            st.session_state.current_match = current_match  # Save match in session_state

            if current_match.empty:
                st.error("❌ No match found.")
            else:
                st.success("✅ Sample found:")
                df.loc[df['Barcode'].astype(str) == str(barcode_input), 'Scan_Status'] = "Matched"
                st.session_state.df = df
                st.info(f"🗸 Scan status updated for barcode: {barcode_input}")

        # Display last scanned results
        if not st.session_state.current_match.empty:
            current_match = st.session_state.current_match

            highlight_cols = ["Screen ID", "Visit", "Sample Name"]

            def highlight_match(row):
                if str(row['Barcode']) in list(current_match['Barcode'].astype(str)):
                    return ['background-color: yellow' if col in highlight_cols else '' for col in row.index]
                else:
                    return ['' for _ in row.index]

            st.subheader("🔹 Current Match(es)")
            st.dataframe(current_match.style.apply(highlight_match, axis=1))

            st.subheader("📋 Full Table")
            st.dataframe(df.style.apply(highlight_match, axis=1))

        # Download button
        if df is not None:
            original_filename = uploaded_file.name
            new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")

            uploaded_file.seek(0)
            wb = load_workbook(uploaded_file)
            ws = wb.active

            # Add Scan_Status column if not exist
            if "Scan_Status" not in [cell.value for cell in ws[1]]:
                ws.cell(row=1, column=ws.max_column + 1, value="Scan_Status")

            # Map headers to column index
            header = {cell.value: idx + 1 for idx, cell in enumerate(ws[1])}

            # Update Scan_Status in Excel
            for i, val in enumerate(df['Scan_Status'], start=2):
                ws.cell(row=i, column=header["Scan_Status"], value=val)

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
