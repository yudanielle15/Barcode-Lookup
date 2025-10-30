import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Biomarker Sample Barcode Lookup Web App", layout="centered")

st.title("🔬 Biomarker Sample Barcode Lookup Web App")
st.write("Upload your Excel file locally, and scan or enter a barcode.")

# Initialize session state for DataFrame
if "df" not in st.session_state:
    st.session_state.df = None

# Upload Excel file
uploaded_file = st.file_uploader("📁 Upload your sample Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Only read file if first time uploading
        if st.session_state.df is None:
            df = pd.read_excel(uploaded_file)

            # Ensure Scan_Status column exists
            if "Scan_Status" not in df.columns:
                df["Scan_Status"] = ""

            st.session_state.df = df

        st.success("✅ File loaded. Ready to scan.")

        # Optional preview
        with st.expander("🔍 Preview File Contents"):
            st.dataframe(st.session_state.df)

        # Barcode input
        barcode_input = st.text_input("🧪 Scan or type barcode:")

        if barcode_input:
            df = st.session_state.df
            result = df[df['Barcode'].astype(str) == str(barcode_input)]

            if result.empty:
                st.error("❌ No match found.")
            else:
                st.success("✅ Sample found:")

                # Update Scan_Status to "Matched" for this barcode
                df.loc[df['Barcode'].astype(str) == str(barcode_input), 'Scan_Status'] = "Matched"
                st.session_state.df = df

                # Confirmation message
                st.info(f"🗸 Scan status updated for barcode: {barcode_input}")

                # Highlight specific columns of matched row(s)
                highlight_cols = ["Screen ID", "Visit", "Sample Name"]

                def highlight_match(row):
                    if str(row['Barcode']) == str(barcode_input):
                        return ['background-color: yellow' if col in highlight_cols else '' for col in row.index]
                    else:
                        return ['' for _ in row.index]

                st.dataframe(df.style.apply(highlight_match, axis=1))

        # Download updated Excel button (always available once file loaded)
        if st.session_state.df is not None:
            buffer = BytesIO()
            st.session_state.df.to_excel(buffer, index=False)
            buffer.seek(0)

            st.download_button(
                label="💾 Download Updated Excel File",
                data=buffer,
                file_name="updated_samples.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

else:
    st.info("⬆️ Please upload an Excel file to begin.")
