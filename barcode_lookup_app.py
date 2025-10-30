import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(page_title="Biomarker Sample Barcode Lookup Web App", layout="centered")
st.title("🔬 Biomarker Sample Barcode Lookup Web App")
st.write("Upload your Excel file locally, and scan or enter a barcode.")

# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = None
if "barcode_input" not in st.session_state:
    st.session_state.barcode_input = ""  # To track barcode input in session state

# Barcode input placeholder to reset input UI
barcode_input_placeholder = st.empty()

uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])

# Function to highlight rows
def highlight_matched_rows(df, match_cols=["Screen ID", "Visit", "Sample Name"]):
    # Create a style for rows that match the 'Screen ID', 'Visit', and 'Sample Name'
    def highlight(row):
        color = 'background-color: yellow'  # Highlight color for matches
        return [color if row[col] in df[col].values else '' for col in match_cols]
    
    return df.style.apply(highlight, axis=1)

if uploaded_file:
    try:
        # Load the file if it's not already loaded
        if st.session_state.df is None:
            df = pd.read_excel(uploaded_file)
            if "Scan_Status" not in df.columns:
                df["Scan_Status"] = ""
            st.session_state.df = df
            st.success("✅ File loaded. Ready to scan.")
        
        # Optional preview with st.expander("🔍 Preview File Contents"):
        st.dataframe(st.session_state.df)

        # --- Barcode input ---
        barcode_input = barcode_input_placeholder.text_input("🧪 Scan or type barcode:", value=st.session_state.barcode_input)

        if barcode_input:
            df = st.session_state.df
            current_match = df[df['Barcode'].astype(str) == str(barcode_input)]

            if current_match.empty:
                st.error("❌ No match found.")
            else:
                st.success("✅ Sample found:")
                # Update Scan_Status in backend
                df.loc[df['Barcode'].astype(str) == str(barcode_input), 'Scan_Status'] = "Matched"
                st.session_state.df = df
                st.info(f"🗸 Scan status updated for barcode: {barcode_input}")

            # Show current match with highlighted rows
            st.subheader("🔹 Current Match(es)")
            st.dataframe(highlight_matched_rows(current_match))

        # --- Clear the barcode input UI after processing ---
        st.session_state.barcode_input = ""  # Reset the barcode input value in session state
        barcode_input_placeholder.empty()  # Clear the input UI field

        # Re-render barcode input placeholder with an empty value
        barcode_input_placeholder.text_input("🧪 Scan or type barcode:", value="", key="barcode_input")

        # --- Full table with highlighted matches ---
        st.subheader("📋 Full Table")
        st.dataframe(highlight_matched_rows(st.session_state.df))

        # --- Download updated Excel ---
        if st.session_state.df is not None:
            original_filename = uploaded_file.name
            new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")
            uploaded_file.seek(0)
            wb = load_workbook(uploaded_file)
            ws = wb.active

            # Add Scan_Status column if missing
            if "Scan_Status" not in [cell.value for cell in ws[1]]:  # Ensure Scan_Status column exists
                ws.cell(row=1, column=ws.max_column + 1, value="Scan_Status")

            # Map headers
            header = {cell.value: idx + 1 for idx, cell in enumerate(ws[1])}
            df = st.session_state.df
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
