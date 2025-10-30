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

uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])

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
        barcode_input = st.text_input("🧪 Scan or type barcode:", value=st.session_state.barcode_input)

        if barcode_input:
            df = st.session_state.df
            current_match = df[df['Barcode'].astype(str) == str(barcode_input)]

            if current_match.empty:
                st.error("❌ No match found.")
            else:
                st.success("✅ Sample found:")
                # Highlight matched columns
                current_match_highlighted = current_match.style.apply(
                    lambda x: ['background-color: yellow' if x.name in ['Screen ID', 'Visit', 'Sample Name'] else '' for _ in x],
                    axis=1
                )

                # Show highlighted current match
                st.subheader("🔹 Current Match(es)")
                st.dataframe(current_match_highlighted)

                # Update Scan_Status in backend
                df.loc[df['Barcode'].astype(str) == str(barcode_input), 'Scan_Status'] = "Matched"
                st.session_state.df = df
                st.info(f"🗸 Scan status updated for barcode: {barcode_input}")

        # --- Clear the barcode input UI after displaying matches --- 
        # Reset the barcode input value in session state after processing and showing matches
        st.session_state.barcode_input = ""  

        # Re-render barcode input placeholder with an empty value
        st.text_input("🧪 Scan or type barcode:", value="", key="barcode_input")

        # --- Full table --- 
        st.subheader("📋 Full Table")
        st.dataframe(st.session_state.df)

        # --- Download updated Excel --- 
        if st.session_state.df is not None:
            original_filename = uploaded_file.name
            new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")
            uploaded_file.seek(0)
            wb = load_workbook(uploaded_file)
            ws = wb.active

            # Add Scan_Status column if missing
            if "Scan_Status" not in [cell.value for cell in ws[1]]: 
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
