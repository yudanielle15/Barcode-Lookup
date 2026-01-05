import streamlit as st
import pandas as pd
from io import BytesIO
from pathlib import Path
from openpyxl import load_workbook

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(page_title="Biomarker Barcode Scanner", layout="centered")
st.title("🔬 Biomarker Sample Barcode Scanner")
st.write("Scan or type barcodes → they become removable bubbles → process all at once")
st.divider()

# -------------------------------
# Initialize session state
# -------------------------------
defaults = {
    "df": None,
    "barcode_tags": [],
    "matched_df": pd.DataFrame(),
    "unmatched_barcodes": [],
    "barcode_input": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -------------------------------
# Upload Excel
# -------------------------------
uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])
if uploaded_file:
    # Reset all session state on new upload
    st.session_state.df = None
    st.session_state.matched_df = pd.DataFrame()
    st.session_state.unmatched_barcodes = []
    st.session_state.barcode_tags = []
    st.session_state.barcode_input = ""

    # Load new Excel
    df = pd.read_excel(uploaded_file)
    if "Barcode" not in df.columns:
        st.error("❌ Excel must contain a 'Barcode' column.")
        st.stop()
    df["Scan_Status"] = df.get("Scan_Status", "")
    df["Barcode"] = df["Barcode"].astype(str)
    st.session_state.df = df
    st.success("✅ File loaded. Ready to scan.")

st.divider()

# -------------------------------
# Barcode input
# -------------------------------
st.subheader("🧪 Scan / Type Barcodes")

def add_barcode():
    barcode = st.session_state.barcode_input.strip()
    if barcode and barcode not in st.session_state.barcode_tags:
        st.session_state.barcode_tags.append(barcode)
    st.session_state.barcode_input = ""

st.text_input("Type or scan barcode", key="barcode_input", on_change=add_barcode)

# -------------------------------
# Display scanned barcodes (removable)
# -------------------------------
if st.session_state.barcode_tags:
    selected = st.multiselect(
        "Scanned barcodes (click ❌ to remove):",
        options=st.session_state.barcode_tags,
        default=st.session_state.barcode_tags
    )
    st.session_state.barcode_tags = selected

st.divider()

# -------------------------------
# Process all barcodes
# -------------------------------
if st.button("🚀 Process All Barcodes", use_container_width=True):
    if st.session_state.df is None:
        st.warning("⚠️ Upload an Excel file first.")
    else:
        barcode_list = st.session_state.barcode_tags
        df_barcodes_set = set(st.session_state.df["Barcode"])  # faster lookup

        matched = [b for b in barcode_list if b in df_barcodes_set]
        unmatched = [b for b in barcode_list if b not in df_barcodes_set]

        st.session_state.df.loc[st.session_state.df["Barcode"].isin(matched), "Scan_Status"] = "Matched"
        st.session_state.matched_df = st.session_state.df[st.session_state.df["Barcode"].isin(matched)]
        st.session_state.unmatched_barcodes = unmatched
        st.session_state.barcode_tags = []

        st.success(f"✅ {len(matched)} matched | ❌ {len(unmatched)} unmatched")

st.divider()

# -------------------------------
# Show results
# -------------------------------
if not st.session_state.matched_df.empty:
    st.subheader("🔹 Matched Samples")
    st.dataframe(
        st.session_state.matched_df.style.apply(
            lambda row: ["background-color: yellow" if col in ["Screen ID", "Visit", "Sample Name"] else "" for col in row.index],
            axis=1
        ),
        use_container_width=True
    )

if st.session_state.unmatched_barcodes:
    st.subheader("❌ Unmatched Barcodes")
    st.code("\n".join(st.session_state.unmatched_barcodes))

st.divider()

# -------------------------------
# Download updated Excel (keep formatting)
# -------------------------------
if uploaded_file and st.session_state.df is not None:
    new_filename = Path(uploaded_file.name).stem + "_Scanned.xlsx"
    buffer = BytesIO()

    # Load original workbook
    uploaded_file.seek(0)  # reset pointer
    wb = load_workbook(uploaded_file)
    ws = wb.active  # assuming first sheet; adjust if needed

    # Update Scan_Status column
    header = [cell.value for cell in ws[1]]
    if "Scan_Status" not in header:
        ws.cell(row=1, column=len(header)+1, value="Scan_Status")
        scan_col_idx = len(header)+1
    else:
        scan_col_idx = header.index("Scan_Status")+1

    # Map Barcode -> Scan_Status
    barcode_status = dict(zip(st.session_state.df["Barcode"], st.session_state.df["Scan_Status"]))

    for row in ws.iter_rows(min_row=2):
        barcode = str(row[header.index("Barcode")].value)
        if barcode in barcode_status:
            row[scan_col_idx-1].value = barcode_status[barcode]

    # Save to BytesIO
    wb.save(buffer)
    buffer.seek(0)

    st.download_button(
        "💾 Download Updated Excel",
        buffer,
        file_name=new_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
else:
    st.info("⬆️ Upload an Excel file to begin.")
