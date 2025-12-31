import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
import streamlit.components.v1 as components

st.set_page_config(page_title="Biomarker Barcode Scanner", layout="centered")

# --- CUSTOM JAVASCRIPT FOR AUTO-ENTER ---
# This script looks for the text input and "presses Enter" 1 second after you stop typing/pasting.
components.html(
    """
    <script>
    const interval = setInterval(() => {
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        for (let input of inputs) {
            if (!input.dataset.listenerAttached) {
                let timeout = null;
                input.addEventListener('input', () => {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        input.dispatchEvent(new KeyboardEvent('keydown', { 'key': 'Enter', 'bubbles': true, 'keyCode': 13 }));
                        input.blur(); // Triggers Streamlit update
                        input.focus(); // Returns focus for next scan
                    }, 1000); // 1 second delay
                });
                input.dataset.listenerAttached = "true";
            }
        }
    }, 500);
    </script>
    """,
    height=0,
)

st.title("🔬 Biomarker Barcode Scanner")
st.info("💡 **Hands-Free Mode:** Paste a barcode and wait 1 second. It will add itself.")

# -------------------------------
# 1. Session State
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
# 2. Logic to process the "Auto-Submit"
# -------------------------------
def add_barcode():
    val = st.session_state.barcode_input.strip()
    if val:
        if val not in st.session_state.barcode_tags:
            st.session_state.barcode_tags.append(val)
        # Clear the box for the next entry
        st.session_state.barcode_input = ""

# -------------------------------
# 3. File Upload
# -------------------------------
uploaded_file = st.file_uploader("📁 Upload Excel file", type=["xlsx"])

if uploaded_file:
    if st.session_state.df is None:
        df = pd.read_excel(uploaded_file)
        if "Barcode" not in df.columns:
            st.error("❌ Excel must contain a 'Barcode' column.")
            st.stop()
        df["Scan_Status"] = df.get("Scan_Status", "")
        df["Barcode"] = df["Barcode"].astype(str)
        st.session_state.df = df

    # -------------------------------
    # 4. The Input Field
    # -------------------------------
    st.text_input(
        "Paste barcode here:", 
        key="barcode_input", 
        on_change=add_barcode
    )

    # -------------------------------
    # 5. Display Bubbles
    # -------------------------------
    if st.session_state.barcode_tags:
        cols = st.columns(5)
        for i, barcode in enumerate(st.session_state.barcode_tags):
            with cols[i % 5]:
                if st.button(f"❌ {barcode}", key=f"remove_{barcode}"):
                    st.session_state.barcode_tags.remove(barcode)
                    st.rerun()

    # -------------------------------
    # 6. Process Button
    # -------------------------------
    if st.button("🚀 Process All Barcodes", use_container_width=True):
        barcode_set = set(st.session_state.barcode_tags)
        df_set = set(st.session_state.df["Barcode"])
        matched = barcode_set & df_set
        unmatched = sorted(barcode_set - df_set)

        st.session_state.df.loc[st.session_state.df["Barcode"].isin(matched), "Scan_Status"] = "Matched"
        st.session_state.matched_df = st.session_state.df[st.session_state.df["Barcode"].isin(matched)]
        st.session_state.unmatched_barcodes = unmatched
        st.session_state.barcode_tags = [] # Reset for next batch
        st.success(f"Processed: {len(matched)} matches found.")

    # -------------------------------
    # 7. Results & Download
    # -------------------------------
    if not st.session_state.matched_df.empty:
        st.dataframe(st.session_state.matched_df, use_container_width=True)

    # Download Logic
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        st.session_state.df.to_excel(writer, index=False)
    
    st.download_button(
        label="💾 Download Updated Excel",
        data=buffer.getvalue(),
        file_name="Scanned_Results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
