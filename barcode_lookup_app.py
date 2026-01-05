import streamlit as st
import pandas as pd
from io import BytesIO
from pathlib import Path
import time

# -------------------------------
# TEST MODE SWITCH
# -------------------------------
TEST_MODE = True   # ← set to False when using a real barcode scanner

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
    "barcode_input": "",
    "last_input": "",
    "last_input_time": 0.0
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
    st.session_state.last_input = ""
    st.session_state.last_input_time = 0.0

st.text_input(
    "Type or scan barcode",
    key="barcode_input",
    on_change=add_barcode
)

# -------------------------------
# Auto-add timer (TEST MODE ONLY)
# -------------------------------
if TEST_MODE:
    current_input = st.session_state.barcode_input
    now = time.time()

    if current_input != st.session_state.last_input:
        st.session_state.last_input = current_input
        st.session_state.last_input_time = now

    # Auto-add if input is stable for 0.8 seconds
    if (
        current_input
        and now - st.session_state.last_input_time > 0.8
    ):
        add_barcode()
        st.experimental_rerun()

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
# Download updated Excel
# -------------------------------
if uploaded_file and st.session_state.df is not None:
    new_filename = Path(uploaded_file.name).stem + "_Scanned.xlsx"
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        st.session_state.df.to_excel(writer, index=False, sheet_name="Sheet1")

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
