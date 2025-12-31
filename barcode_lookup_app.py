import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
import time

st.set_page_config(page_title="Biomarker Barcode Scanner", layout="centered")
st.title("🔬 Biomarker Barcode Scanner")

# -------------------------------
# 1. Session State Initialization
# -------------------------------
if "df" not in st.session_state:
    st.session_state.df = None
if "barcode_tags" not in st.session_state:
    st.session_state.barcode_tags = []
if "temp_input" not in st.session_state:
    st.session_state.temp_input = ""
if "last_change_time" not in st.session_state:
    st.session_state.last_change_time = time.time()
if "matched_df" not in st.session_state:
    st.session_state.matched_df = pd.DataFrame()

# -------------------------------
# 2. File Upload
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
        st.success("✅ File loaded.")

    # -------------------------------
    # 3. Auto-Processing Fragment
    # -------------------------------
    # This block runs independently to check the timer
    @st.fragment(run_every=0.5)
    def barcode_input_area():
        st.subheader("🧪 Scan / Paste Barcode")
        
        # Text input tied to temp_input
        current_input = st.text_input(
            "The list updates 1s after you stop pasting:", 
            value=st.session_state.temp_input,
            key="input_field",
            placeholder="Paste here..."
        )

        # Logic: If text is entered...
        if current_input != st.session_state.temp_input:
            st.session_state.temp_input = current_input
            st.session_state.last_change_time = time.time()

        # If 1 second has passed since the last change and the box isn't empty
        if st.session_state.temp_input.strip() != "":
            if time.time() - st.session_state.last_change_time > 1.0:
                barcode = st.session_state.temp_input.strip()
                if barcode not in st.session_state.barcode_tags:
                    st.session_state.barcode_tags.append(barcode)
                
                # RESET: Clear the input and the timer
                st.session_state.temp_input = ""
                st.rerun()

    barcode_input_area()

    # -------------------------------
    # 4. Display Bubbles
    # -------------------------------
    if st.session_state.barcode_tags:
        st.write("Current List:")
        cols = st.columns(4)
        for i, tag in enumerate(st.session_state.barcode_tags):
            with cols[i % 4]:
                if st.button(f"❌ {tag}", key=f"btn_{tag}_{i}"):
                    st.session_state.barcode_tags.remove(tag)
                    st.rerun()

    # -------------------------------
    # 5. Process & Download
    # -------------------------------
    st.divider()
    if st.button("🚀 Process All Barcodes", use_container_width=True):
        tags = set(st.session_state.barcode_tags)
        st.session_state.df.loc[st.session_state.df["Barcode"].isin(tags), "Scan_Status"] = "Matched"
        st.session_state.matched_df = st.session_state.df[st.session_state.df["Barcode"].isin(tags)]
        st.session_state.barcode_tags = [] # Clear the list
        st.success("Processing complete!")

    if not st.session_state.matched_df.empty:
        st.dataframe(st.session_state.matched_df, use_container_width=True)
        
        # Prepare Excel Download
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.df.to_excel(writer, index=False)
        
        st.download_button(
            "💾 Download Scanned Excel",
            data=output.getvalue(),
            file_name="Updated_Samples.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Please upload an Excel file to start.")
