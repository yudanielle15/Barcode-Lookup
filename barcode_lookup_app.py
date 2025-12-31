import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

# ---------------------------
# Page setup
# ---------------------------
st.set_page_config(
    page_title="Biomarker Sample Barcode Lookup Web App",
    layout="centered"
)

st.title("🔬 Biomarker Sample Barcode Lookup Web App")
st.write("Upload your Excel file, enter multiple barcodes, then process them together.")

# ---------------------------
# Session state initialization
# ---------------------------
if "df" not in st.session_state:
    st.session_state.df = None

# ---------------------------
# File upload
# ---------------------------
uploaded_file = st.file_uploader(
    "📁 Upload your sample Excel file",
    type=["xlsx"]
)

if uploaded_file:
    try:
        # Load Excel once
        if st.session_state.df is None:
            df = pd.read_excel(uploaded_file)
            if "Scan_Status" not in df.columns:
                df["Scan_Status"] = ""
            st.session_state.df = df

        st.success("✅ File loaded successfully.")

        # ---------------------------
        # Display loaded table
        # ---------------------------
        st.subheader("📋 Loaded Table")
        st.dataframe(st.session_state.df)

        # ---------------------------
        # Barcode input (manual / continuous)
        # ---------------------------
        st.subheader("🧪 Barcode Input")

        st.info(
            "Enter barcodes separated by **new lines or commas**.\n\n"
            "Example:\n"
            "ABC123\nDEF456\nGHI789\n\n"
            "or\n\n"
            "ABC123, DEF456, GHI789"
        )

        barcode_text = st.text_area(
            "Barcodes:",
            height=180,
            placeholder="ABC123\nDEF456\nGHI789"
        )

        # ---------------------------
        # Process button
        # ---------------------------
        if st.button("▶️ Process All Barcodes"):
            df = st.session_state.df

            # Normalize separators (comma OR newline)
            barcodes = [
                b.strip()
                for b in barcode_text.replace(",", "\n").splitlines()
                if b.strip()
            ]

            if not barcodes:
                st.warning("⚠️ Please enter at least one barcode.")
            else:
                matched = []
                not_found = []

                for barcode in barcodes:
                    matches = df["Barcode"].astype(str) == barcode
                    if matches.any():
                        df.loc[matches, "Scan_Status"] = "Matched"
                        matched.append(barcode)
                    else:
                        not_found.append(barcode)

                st.session_state.df = df

                # ---------------------------
                # Results summary
                # ---------------------------
                st.subheader("📊 Scan Results")

                if matched:
                    st.success(
                        f"✅ Matched ({len(matched)}): {', '.join(matched)}"
                    )

                if not_found:
                    st.error(
                        f"❌ Not found ({len(not_found)}): {', '.join(not_found)}"
                    )

        # ---------------------------
        # Updated table
        # ---------------------------
        st.subheader("📋 Updated Table")
        st.dataframe(st.session_state.df)

        # ---------------------------
        # Download updated Excel
        # ---------------------------
        st.subheader("💾 Download Updated Excel")

        original_filename = uploaded_file.name
        new_filename = original_filename.replace(".xlsx", "_Scanned.xlsx")

        uploaded_file.seek(0)
        wb = load_workbook(uploaded_file)
        ws = wb.active

        # Ensure Scan_Status column exists
        if "Scan_Status" not in [cell.value for cell in ws[1]]:
            ws.cell(
                row=1,
                column=ws.max_column + 1,
                value="Scan_Status"
            )

        header_map = {
            cell.value: idx + 1
            for idx, cell in enumerate(ws[1])
        }

        for i, val in enumerate(
            st.session_state.df["Scan_Status"], start=2
        ):
            ws.cell(
                row=i,
                column=header_map["Scan_Status"],
                value=val
            )

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        st.download_button(
            label="⬇️ Download Updated Excel File",
            data=buffer,
            file_name=new_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

else:
    st.info("⬆️ Please upload an Excel file to begin.")
