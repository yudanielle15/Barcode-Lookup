import streamlit as st
import pandas as pd
from pathlib import Path
import xlwings as xw
from io import BytesIO

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
    df = pd.read_excel(uploaded_file)
    if "Barcode" not in df.columns:
        st.error("❌ Excel must contain a 'Barcode' column.")
        st.stop()

    df["Scan_Status"] = df.get("Scan_Status", "")
    df["Barcode"] = df["Barcode"].astype(str)

    # Reset previous session data
    st.session_state.df = df
    st.session_state.matched_df = pd.DataFrame()
    st.session_state.unmatched_barcodes = []
    st.session_state.barcode_tags = []
    st.session_state.barcode_input = ""

    # Save temporary local file for xlwings
    temp_path = Path("temp_uploaded.xlsx")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.session_state.temp_path = temp_path

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
# Display scanned barcodes
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
# Download updated Excel (xlwings)
# -------------------------------
if uploaded_file and st.session_state.df is not None:
    if st.button("💾 Save Updated Excel (Preserve Everything)"):
        wb = xw.Book(st.session_state.temp_path)
        sheet = wb.sheets[0]

        headers = sheet.range("1:1").value
        barcode_col = headers.index("Barcode") + 1

        # Add Scan_Status if not present
        try:
            scan_col = headers.index("Scan_Status") + 1
        except ValueError:
            scan_col = len(headers) + 1
            sheet.range((1, scan_col)).value = "Scan_Status"

        # Map barcode -> Scan_Status
        status_map = dict(zip(st.session_state.df["Barcode"], st.session_state.df["Scan_Status"]))

        # Update values in Excel
        for r in range(2, sheet.used_range.last_cell.row + 1):
            bc = str(sheet.range((r, barcode_col)).value)
            if bc in status_map:
                sheet.range((r, scan_col)).value = status_map[bc]

        # Save to buffer
        out_path = Path("Updated_" + st.session_state.temp_path.name)
        wb.save(out_path)
        wb.close()

        # Provide download
        with open(out_path, "rb") as f:
            buffer = BytesIO(f.read())

        st.download_button(
            "⬇️ Download Updated Excel",
            buffer,
            file_name=out_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
