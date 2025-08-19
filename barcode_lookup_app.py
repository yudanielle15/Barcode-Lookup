import streamlit as st
import pandas as pd

st.set_page_config(page_title="Biomarker Sample Lookup", layout="centered")

st.title("🔬 Biomarker Sample Lookup System (Secure & Online)")
st.write("Upload your Excel file locally, and scan or enter a barcode.")

# Upload Excel
uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        st.success("✅ File loaded. Ready to scan.")
        
        # Optional: Preview
        with st.expander("🔍 Preview File Contents"):
            st.dataframe(df)

        barcode_input = st.text_input("🧪 Scan or type barcode:")

        if barcode_input:
            result = df[df['Barcode'].astype(str) == str(barcode_input)]

            if result.empty:
                st.error("❌ No match found.")
            else:
                st.success("✅ Sample found:")
                st.dataframe(result)

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
else:
    st.info("⬆️ Please upload an Excel file to begin.")
