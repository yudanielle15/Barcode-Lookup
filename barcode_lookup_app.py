import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(page_title="Biomarker Barcode Scanner", layout="centered")
st.title("🔬 Biomarker Sample Barcode Scanner")
st.write("Scan or type barcodes → they become removable bubbles → process all at once")

# Session state
if "df" not in st.session_state:
    st.session_state.df = None
if "barcode_tags" not in st.session_state:
    st.session_state.barcode_tags = []
if "matched_df" not in st.session_state:
    st.session_state.matched_df = pd.DataFrame()
if "unmatched_barcodes" not in st.session_state:
    st.session_state.unmatched_barcodes = []

uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])

if uploaded_file:
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
    # Auto-enter barcode input
    # -------------------------------
    st.subheader("🧪 Scan / Type Barcodes")

    barcode_input = st.text_input(
        "Scan or type barcode",
        key="barcode_input",
        placeholder="Type or scan barcode"
    )

    # JavaScript auto-submit
    st.markdown("""
        <script>
        const input = window.parent.document.querySelector('input[data-baseweb="input"]');
        if(input){
            input.addEventListener('input', function(){
                const e = new Event('change', { bubbles: true });
                input.dispatchEvent(e);
            });
        }
        </script>
        """, unsafe_allow_html=True)

    if barcode_input and barcode_input not in st.session_state.barcode_tags:
        st.session_state.barcode_tags.append(barcode_input)
        st.session_state.barcode_input = ""

    # -------------------------------
    # Display scanned barcodes
    # -------------------------------
    if st.session_state.barcode_tags:
        st.multiselect(
            "Scanned barcodes (click ❌ to remove):",
            options=st.session_state.barcode_tags.copy(),
            default=st.session_state.barcode_tags.copy(),
            key="barcode_tags_widget"
        )

    # -------------------------------
    # Process all barcodes
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
        use_container_width=True
    )

else:
    st.info("⬆️ Upload an Excel file to begin.")
