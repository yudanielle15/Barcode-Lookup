import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
import time

st.set_page_config(page_title="Biomarker Barcode Scanner", layout="centered")
st.title("🔬 Biomarker Sample Barcode Scanner")
st.write("Scan barcodes → they automatically clear and add to the list.")

# -------------------------------
# 1. Session State Initialization
# -------------------------------
if "df" not in st.session_state:
    st.session_state.df = None
if "barcode_tags" not in st.session_state:
    st.session_state.barcode_tags = []
if "matched_df" not in st.session_state:
    st.session_state.matched_df = pd.DataFrame()
if "unmatched_barcodes" not in st.session_state:
    st.session_state.unmatched_barcodes = []

# -------------------------------
# 2. The "Auto-Add" Logic (Callback)
# -------------------------------
def process_scan():
    """This function runs automatically when the user (or scanner) hits Enter."""
    val = st.session_state.barcode_input.strip()
    if val:
        if val not in st.session_state.barcode_tags:
            # Simulate a 1-sec processing delay as requested
            time.sleep(1) 
            st.session_state.barcode_tags.append(val)
        # This clears the text box for the next scan
        st.session_state.barcode_input = ""

# -------------------------------
# 3. Upload Excel
# -------------------------------
uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])

if uploaded_file:
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

    # -------------------------------
    # 4. Scan / Type Barcodes
    # -------------------------------
    st.subheader("🧪 Scan / Type Barcodes")
    
    # The key="barcode_input" links this field to the session state
    # The on_change=process_scan triggers the logic without clicking a button
    st.text_input(
        "Focus here and scan barcode", 
        key="barcode_input", 
        on_change=process_scan
    )

    # -------------------------------
    # 5. Display Bubbles
    # -------------------------------
    if st.session_state.barcode_tags:
        st.write("Scanned barcodes (click ❌ to remove):")
        cols = st.columns(5)
        for i, barcode in enumerate(st.session_state.barcode_tags):
            with cols[i % 5]:
                if st.button(f"❌ {barcode}", key=f"remove_{barcode}"):
                    st.session_state.barcode_tags.remove(barcode)
                    st.rerun()

    # -------------------------------
    # 6. Process All Barcodes
    # -------------------------------
    if st.button("🚀 Process All Barcodes", use_container_width=True):
        barcode_set = set(st.session_state.barcode_tags)
        df_set = set(st.session_state.df["Barcode"])
        matched = barcode_set & df_set
        unmatched = sorted(barcode_set - df_set)

        st.session_state.df.loc[st.session_state.df["Barcode"].isin(matched), "Scan_Status"] = "Matched"
        st.session_state.matched_df = st.session_state.df[st.session_state.df["Barcode"].isin(matched)]
        st.session_state.unmatched_barcodes = unmatched

        st.success(f"✅ {len(matched)} matched | ❌ {len(unmatched)} unmatched")
        st.session_state.barcode_tags = [] # Clear the scanner list after processing

    # -------------------------------
    # 7. Show Results & Download
    # -------------------------------
    if not st.session_state.matched_df.empty:
        st.subheader("🔹 Matched Samples")
        st.dataframe(st.session_state.matched_df, use_container_width=True)

    if st.session_state.unmatched_barcodes:
        st.subheader("❌ Unmatched Barcodes")
        st.code("\n".join(st.session_state.unmatched_barcodes))

    # Excel Export
    original_filename = uploaded_file.name
    new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")
    
    wb = load_workbook(uploaded_file)
    ws = wb.active
    header_map = {cell.value: i + 1 for i, cell in enumerate(ws[1])}
    
    if "Scan_Status" not in header_map:
        ws.cell(row=1, column=ws.max_column + 1, value="Scan_Status")
        header_map["Scan_Status"] = ws.max_column

    for i, val in enumerate(st.session_state.df["Scan_Status"], start=2):
        ws.cell(row=i, column=header_map["Scan_Status"], value=val)

    buffer = BytesIO()
    wb.save(buffer)
    st.download_button(
        "💾 Download Updated Excel",
        buffer.getvalue(),
        file_name=new_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

else:
    st.info("⬆️ Upload an Excel file to begin.")
