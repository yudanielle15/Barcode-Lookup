import streamlit as st
import pandas as pd
from io import BytesIO

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(page_title="Biomarker Barcode Scanner", layout="centered")
st.title("🔬 Biomarker Sample Barcode Scanner")
st.write("Scan or type barcodes → they become removable bubbles → process all at once")

# -------------------------------
# Session state initialization
# -------------------------------
if "df" not in st.session_state:
    st.session_state.df = None
if "barcode_tags" not in st.session_state:
    st.session_state.barcode_tags = []
if "matched_df" not in st.session_state:
    st.session_state.matched_df = pd.DataFrame()
if "unmatched_barcodes" not in st.session_state:
    st.session_state.unmatched_barcodes = []
if "barcode_input" not in st.session_state:
    st.session_state.barcode_input = ""

# -------------------------------
# Upload Excel
# -------------------------------
uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])
if uploaded_file and st.session_state.df is None:
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
# Scan / Type Barcode
# -------------------------------
st.subheader("🧪 Scan / Type Barcodes")

barcode_input = st.text_input(
    "Type or scan barcode",
    value=st.session_state.barcode_input,
    key="barcode_input"
)

if barcode_input:
    cleaned = barcode_input.strip()
    if cleaned and cleaned not in st.session_state.barcode_tags:
        st.session_state.barcode_tags.append(cleaned)
    st.session_state.barcode_input = ""  # clear input immediately

# Display scanned barcodes and allow removal
if st.session_state.barcode_tags:
    selected = st.multiselect(
        "Scanned barcodes (click ❌ to remove):",
        options=st.session_state.barcode_tags,
        default=st.session_state.barcode_tags
    )
    st.session_state.barcode_tags = selected

# -------------------------------
# Process All Barcodes
# -------------------------------
if st.button("🚀 Process All Barcodes", use_container_width=True):
    if st.session_state.df is None:
        st.warning("⚠️ Upload an Excel file first.")
    else:
        barcode_list = st.session_state.barcode_tags
        df_barcodes = st.session_state.df["Barcode"].tolist()

        matched = [b for b in barcode_list if b in df_barcodes]
        unmatched = [b for b in barcode_list if b not in df_barcodes]

        st.session_state.df.loc[st.session_state.df["Barcode"].isin(matched), "Scan_Status"] = "Matched"
        st.session_state.matched_df = st.session_state.df[st.session_state.df["Barcode"].isin(matched)]
        st.session_state.unmatched_barcodes = unmatched

        st.success(f"✅ {len(matched)} matched | ❌ {len(unmatched)} unmatched")
        st.session_state.barcode_tags = []

# -------------------------------
# Show results
# -------------------------------
if not st.session_state.matched_df.empty:
    st.subheader("🔹 Matched Samples")

    def highlight_row(row):
        styles = [''] * len(row)
        for i, col in enumerate(row.index):
            if col in ["Screen ID", "Visit", "Sample Name"]:
                styles[i] = "background-color: yellow"
        return styles

    st.dataframe(
        st.session_state.matched_df.style.apply(highlight_row, axis=1),
        use_container_width=True
    )

if st.session_state.unmatched_barcodes:
    st.subheader("❌ Unmatched Barcodes")
    st.code("\n".join(st.session_state.unmatched_barcodes))

# -------------------------------
# Download updated Excel
# -------------------------------
if uploaded_file and st.session_state.df is not None:
    original_filename = uploaded_file.name
    new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")

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
