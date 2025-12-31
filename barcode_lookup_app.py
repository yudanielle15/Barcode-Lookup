import streamlit as st
from streamlit_js_eval import st_javascript
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
import time

st.set_page_config(page_title="Biomarker Barcode Scanner", layout="centered")
st.title("🔬 Biomarker Sample Barcode Scanner")
st.write("Scan or paste barcodes — they get added automatically!")

# -------------------
# Session state init
# -------------------
if "df" not in st.session_state:
    st.session_state.df = None
if "barcode_tags" not in st.session_state:
    st.session_state.barcode_tags = []
if "incoming_barcode" not in st.session_state:
    st.session_state.incoming_barcode = ""
if "matched_df" not in st.session_state:
    st.session_state.matched_df = pd.DataFrame()
if "unmatched_barcodes" not in st.session_state:
    st.session_state.unmatched_barcodes = []

# -------------------
# Load Excel
# -------------------
uploaded_file = st.file_uploader("📁 Upload your sample Excel (.xlsx)", type="xlsx")

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
        st.success("✅ File loaded. Ready to scan!")

    st.subheader("🧪 Continuous Barcode Scanner")

    # Run JS code in browser to read input
    script = """
    (() => {
        const existing = window.latestStreamlitBarcode || "";
        const next = window.prompt("Scan or paste here:", "");
        window.latestStreamlitBarcode = next;
        return next;
    })();
    """
    barcode = st_javascript(js_expressions=script, key="scan_input")

    # Add barcode if valid
    if barcode:
        cleaned = barcode.strip()
        if cleaned not in st.session_state.barcode_tags:
            st.session_state.barcode_tags.append(cleaned)

    # Show tags as removable buttons
    if st.session_state.barcode_tags:
        st.write("Scanned barcodes:")
        cols = st.columns(5)
        for i, tag in enumerate(st.session_state.barcode_tags):
            with cols[i % 5]:
                if st.button(f"❌ {tag}", key=f"remove_{tag}"):
                    st.session_state.barcode_tags.remove(tag)
                    st.experimental_rerun()

    # Process all
    if st.button("🚀 Process All Barcodes", use_container_width=True):
        barcode_set = set(st.session_state.barcode_tags)
        df_set = set(st.session_state.df["Barcode"])
        matched = barcode_set & df_set
        unmatched = sorted(barcode_set - df_set)

        st.session_state.df.loc[st.session_state.df["Barcode"].isin(matched), "Scan_Status"] = "Matched"
        st.session_state.matched_df = st.session_state.df[st.session_state.df["Barcode"].isin(matched)]
        st.session_state.unmatched_barcodes = unmatched

        st.success(f"✅ {len(matched)} matched | ❌ {len(unmatched)} unmatched")
        st.session_state.barcode_tags = []

    # Show results
    if not st.session_state.matched_df.empty:
        st.subheader("🔹 Matched Samples")
        st.dataframe(st.session_state.matched_df, use_container_width=True)

    if st.session_state.unmatched_barcodes:
        st.subheader("❌ Unmatched Barcodes")
        st.code("\n".join(st.session_state.unmatched_barcodes))

    # Download updated Excel
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
        use_container_width=True,
    )

else:
    st.info("⬆️ Upload your Excel file to begin.")
