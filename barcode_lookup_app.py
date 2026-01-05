import streamlit as st
import pandas as pd
from io import BytesIO
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
    try:
        df = pd.read_excel(uploaded_file)
        if "Barcode" not in df.columns:
            st.error("❌ Excel must contain a 'Barcode' column.")
            st.stop()
        if "Scan_Status" not in df.columns:
            df["Scan_Status"] = ""
        df["Barcode"] = df["Barcode"].astype(str)

        # Reset previous session data
        st.session_state.df = df
        st.session_state.barcode_tags = []
        st.session_state.matched_df = pd.DataFrame()
        st.session_state.unmatched_barcodes = []
        st.session_state.barcode_input = ""
        st.session_state.temp_file = uploaded_file

        st.success("✅ File loaded. Ready to scan.")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

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
# Display scanned barcodes (removable bubbles)
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
        df_barcodes = st.session_state.df["Barcode"].tolist()

        matched = [b for b in barcode_list if b in df_barcodes]
        unmatched = [b for b in barcode_list if b not in df_barcodes]

        st.session_state.df.loc[
            st.session_state.df["Barcode"].isin(matched),
            "Scan_Status"
        ] = "Matched"

        st.session_state.matched_df = st.session_state.df[
            st.session_state.df["Barcode"].isin(matched)
        ]

        st.session_state.unmatched_barcodes = unmatched
        st.session_state.barcode_tags = []  # Clear bubbles after processing

        st.success(f"✅ {len(matched)} matched | ❌ {len(unmatched)} unmatched")

st.divider()

# -------------------------------
# Show results
# -------------------------------
if not st.session_state.matched_df.empty:
    st.subheader("🔹 Matched Samples")
    st.dataframe(
        st.session_state.matched_df.style.apply(
            lambda row: [
                "background-color: yellow"
                if col in ["Screen ID", "Visit", "Sample Name"] else ""
                for col in row.index
            ],
            axis=1
        ),
        use_container_width=True
    )

if st.session_state.unmatched_barcodes:
    st.subheader("❌ Unmatched Barcodes")
    st.code("\n".join(st.session_state.unmatched_barcodes))

st.divider()

# -------------------------------
# Download updated Excel (preserve formatting)
# -------------------------------
if uploaded_file and st.session_state.df is not None:
    st.subheader("💾 Download Updated Excel")

    wb = load_workbook(st.session_state.temp_file)
    ws = wb.active

    # Add Scan_Status if missing
    headers = [cell.value for cell in ws[1]]
    if "Scan_Status" not in headers:
        scan_col = ws.max_column + 1
        ws.cell(row=1, column=scan_col, value="Scan_Status")
        headers.append("Scan_Status")
    else:
        scan_col = headers.index("Scan_Status") + 1

    barcode_col = headers.index("Barcode") + 1

    # Update Scan_Status values
    status_map = dict(zip(st.session_state.df["Barcode"], st.session_state.df["Scan_Status"]))
    for r in range(2, ws.max_row + 1):
        bc = str(ws.cell(row=r, column=barcode_col).value)
        ws.cell(row=r, column=scan_col, value=status_map.get(bc, ""))

    # Save to buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    st.download_button(
        label="⬇️ Download Updated Excel File",
        data=buffer,
        file_name=uploaded_file.name.replace(".xlsx", "_Scanned.xlsx"),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
