import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(page_title="Biomarker Sample Barcode Lookup Web App", layout="centered")
st.title("🔬 Biomarker Sample Barcode Lookup Web App")
st.write("Upload your Excel file locally, and scan or enter a barcode.")

# Initialize session state if not already initialized
if "df" not in st.session_state:
    st.session_state.df = None
if "barcode_input" not in st.session_state:
    st.session_state.barcode_input = ""

# Barcode input placeholder for reset
barcode_input_placeholder = st.empty()

# Columns to highlight when barcode matches
highlight_cols = ["Screen ID", "Visit", "Sample Name"]

# Function to apply highlights to the rows that match the barcode
def highlight_match(row):
    styles = []
    for col in row.index:
        if str(row['Barcode']) == str(st.session_state.barcode_input) and col in highlight_cols:
            styles.append('background-color: yellow')  # Highlight matching columns
        else:
            styles.append('')
    return styles

# Upload the file
uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Load the file if it's not already loaded
        if st.session_state.df is None:
            df = pd.read_excel(uploaded_file)
            if "Scan_Status" not in df.columns:
                df["Scan_Status"] = ""  # Add Scan_Status column if not present
            st.session_state.df = df
        st.success("✅ File loaded. Ready to scan.")

        # Barcode input field
        barcode_input = barcode_input_placeholder.text_input("🧪 Scan or type barcode:", value=st.session_state.barcode_input)

        if barcode_input:
            # Find rows matching the barcode input
            df = st.session_state.df
            current_match = df[df['Barcode'].astype(str) == str(barcode_input)]
            
            if current_match.empty:
                st.error("❌ No match found.")
            else:
                # Update the Scan_Status to "Matched" for the matching barcode
                df.loc[df['Barcode'].astype(str) == str(barcode_input), 'Scan_Status'] = "Matched"
                st.session_state.df = df

                # Show success message and updated status for barcode
                st.info(f"🗸 Scan status updated for barcode: {barcode_input}")
                
                # Show current match with yellow highlights
                st.subheader("🔹 Current Match(es)")
                st.dataframe(current_match.style.apply(highlight_match, axis=1))

                # --- Clear the barcode input UI after processing ---
                st.session_state.barcode_input = ""  # Reset the barcode input value in session state
                barcode_input_placeholder.empty()  # Clear the input UI field
                barcode_input_placeholder.text_input("🧪 Scan or type barcode:", value="", key="barcode_input")  # Re-render

        # --- Full table with highlights ---
        st.subheader("📋 Full Table")
        st.dataframe(st.session_state.df.style.apply(highlight_match, axis=1))  # Apply highlight to full table

        # --- Download updated Excel ---
        if st.session_state.df is not None:
            original_filename = uploaded_file.name
            new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")
            uploaded_file.seek(0)  # Reset the file pointer
            wb = load_workbook(uploaded_file)
            ws = wb.active

            # Add Scan_Status column if missing in the Excel file
            if "Scan_Status" not in [cell.value for cell in ws[1]]:
                ws.cell(row=1, column=ws.max_column + 1, value="Scan_Status")

            # Map headers for Scan_Status column
            header = {cell.value: idx + 1 for idx, cell in enumerate(ws[1])}
            df = st.session_state.df

            # Write Scan_Status values to the Excel sheet
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
