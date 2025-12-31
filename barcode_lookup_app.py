import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(page_title="Biomarker Barcode Scanner", layout="centered")

# -------------------------------
# 1. Automatic Logic: Catch Barcode from URL
# -------------------------------
# We use query parameters because JavaScript can update the URL 
# without needing the user to press "Enter" or click any buttons.

if "barcode_tags" not in st.session_state:
    st.session_state.barcode_tags = []
if "df" not in st.session_state:
    st.session_state.df = None
if "matched_df" not in st.session_state:
    st.session_state.matched_df = pd.DataFrame()

# Check if a barcode was just sent by our JavaScript component
if "barcode" in st.query_params:
    new_barcode = st.query_params["barcode"].strip()
    if new_barcode and new_barcode not in st.session_state.barcode_tags:
        st.session_state.barcode_tags.append(new_barcode)
    
    # Clear the URL immediately so it doesn't add the same barcode twice
    st.query_params.clear()
    st.rerun()

# -------------------------------
# 2. Main UI
# -------------------------------
st.title("🔬 Biomarker Barcode Scanner")
st.markdown("### ⚡ Hands-Free Mode Active")
st.write("Paste a barcode below. Do **not** press Enter. It will add itself after 1 second.")

# -------------------------------
# 3. Custom HTML Input Component
# -------------------------------
# This creates a real-time listener that standard Streamlit widgets can't do.
st.components.v1.html(
    """
    <div style="font-family: sans-serif;">
        <input type="text" id="barcode-input" placeholder="Paste barcode here..." 
            style="width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 5px; font-size: 16px; outline: none;">
        <p id="status" style="color: #666; font-size: 12px; margin-top: 5px;">Ready for scan/paste...</p>
    </div>

    <script>
        const input = document.getElementById('barcode-input');
        const status = document.getElementById('status');
        let timeout = null;

        // Automatically focus the box on load
        input.focus();

        input.addEventListener('input', (e) => {
            const val = e.target.value.trim();
            status.innerText = "Detected input... waiting 1s to auto-submit...";
            
            // Reset the 1-second timer every time something is pasted/typed
            clearTimeout(timeout);
            
            if (val) {
                timeout = setTimeout(() => {
                    // This updates the parent URL, which Streamlit detects instantly
                    const url = new URL(window.parent.location.href);
                    url.searchParams.set('barcode', val);
                    window.parent.location.search = url.searchParams.toString();
                }, 1000);
            }
        });
    </script>
    """,
    height=100,
)

# -------------------------------
# 4. Excel Upload & Processing Logic
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

    # Display Bubbles
    if st.session_state.barcode_tags:
        st.subheader("📋 Scanned List")
        cols = st.columns(4)
        for i, tag in enumerate(st.session_state.barcode_tags):
            with cols[i % 4]:
                if st.button(f"❌ {tag}", key=f"del_{tag}_{i}"):
                    st.session_state.barcode_tags.remove(tag)
                    st.rerun()

    # Process Button
    if st.button("🚀 Process All Barcodes", use_container_width=True):
        tags = set(st.session_state.barcode_tags)
        df = st.session_state.df
        
        # Logic to match
        df.loc[df["Barcode"].isin(tags), "Scan_Status"] = "Matched"
        st.session_state.matched_df = df[df["Barcode"].isin(tags)]
        st.session_state.barcode_tags = [] # Reset scanner list
        st.success("Successfully processed barcodes!")

    # Show Results & Download
    if not st.session_state.matched_df.empty:
        st.dataframe(st.session_state.matched_df, use_container_width=True)
        
        # Export logic
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.df.to_excel(writer, index=False)
        
        st.download_button(
            "💾 Download Updated Excel",
            output.getvalue(),
            file_name="Scanned_Results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
else:
    st.info("⬆️ Please upload an Excel file to begin.")
