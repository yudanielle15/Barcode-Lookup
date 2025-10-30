import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

# Set up the Streamlit page configuration
st.set_page_config(page_title="Biomarker Sample Barcode Lookup Web App", layout="centered")
st.title("🔬 Biomarker Sample Barcode Lookup Web App")
st.write("Upload your Excel file locally, and scan or enter a barcode.")

# Initialize session state for storing DataFrame and barcode input
if "df" not in st.session_state:
    st.session_state.df = None
if "barcode_input" not in st.session_state:
    st.session_state.barcode_input = ""

# Barcode input placeholder to reset input UI
barcode_input_placeholder = st.empty()

# Highlight specific columns for matching rows
highlight_cols = ["Screen ID", "Visit", "Sample Name"]

def highlight_match(row):
    """Return highlight style if barcode matches, only for specified columns."""
    styles = []
    for col in row.index:
        # If the value in the 'Barcode' column matches the barcode input
        if str(row['Barcode']) == str(st.session_state.barcode_input) and col in highlight_cols:
            styles.append('background-color: yellow')  # Highlight this column if it's a match
        else:
            styles.append('')  # No highlight for non-matching columns
    return styles

# File upload UI
uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Load the Excel file if it's not already loaded
        if st.session_state.df is None:
            df = pd.read_excel(uploaded_file)
            if "Scan_Status" not in df.columns:
                df["Scan_Status"] = ""  # Add Scan_Status if it's missing
            st.session_state.df = df
            st.success("✅ File loaded. Ready to scan.")

        # Optional file preview
        st.expander("🔍 Preview File Contents").dataframe(st.session_state.df)

        # --- Barcode input ---
        barcode_input = barcode_input_placeholder.text_input("🧪 Scan or type barcode:", value=st.session_state.barcode_input)

        if barcode_input:
            df = st.session_state.df

            # Find the row that matches the barcode input
            current_match = df[df['Barcode'].astype(str) == str(barcode_input)]

            if current_match.empty:
                st.error("❌ No match found.")
            else:
                st.success("✅ Sample found:")
                
                # Update the 'Scan_Status' in the DataFrame for matched barcode
                df.loc[df['Barcode'].astype(str) == str(barcode_input), 'Scan_Status'] = "Matched"
                st.session_state.df = df
                st.info(f"🗸 Scan status updated for barcode: {barcode_input}")

                # Show current match with yellow highlights for the relevant columns
                st.subheader("🔹 Current Match(es)")
                st.dataframe(current_match.style.apply(highlight_match, axis=1))

                # --- Clear the barcode input UI after processing ---
                st.session_state.barcode_input = ""  # Reset barcode input
                barcode_input_placeholder.empty()  # Clear input UI field

                # Re-render the barcode input field with an empty value
                barcode_input_placeholder.text_input("🧪 Scan or type barcode:", value="", key="barcode_input")

        # --- Full table with highlights ---
        st.subheader("📋 Full Table")
        st.dataframe(st.session_state.df.style.apply(highlight_match, axis=1))  # Apply highlight to the full table

        # --- Download updated Excel ---
        if st.session_state.df is not None:
            original_filename = uploaded_file.name
            new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")
            uploaded_file.seek(0)
            wb = load_workbook(uploaded_file)
            ws = wb.active

            # Add Scan_Status column if missing in the original file
            if "Scan_Status" not in [cell.value for cell in ws[1]]:
                ws.cell(row=1, column=ws.max_column + 1, value="Scan_Status")

            # Map headers and write updated Scan_Status to the Excel file
            header = {cell.value: idx + 1 for idx, cell in enumerate(ws[1])}
            df = st.session_state.df
            for i, val in enumerate(df['Scan_Status'], start=2):
                ws.cell(row=i, column=header["Scan_Status"], value=val)

            # Save the updated file in memory and provide download button
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
