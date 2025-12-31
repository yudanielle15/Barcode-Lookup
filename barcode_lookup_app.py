import streamlit as st

st.title("JS Auto-Add Barcode Example")

barcode = st.text_input("Scanned Barcode", key="barcode_input")

# JS snippet: auto-add after 1s
js = f"""
<input id="barcode" type="text" placeholder="Scan here" style="width:300px;"/>
<script>
var input = document.getElementById("barcode");
input.addEventListener("change", function(e) {{
    var value = input.value.trim();
    if(value) {{
        setTimeout(() => {{
            const streamlitInput = window.parent.document.querySelector('[data-testid="stTextInput"] input');
            streamlitInput.value = value;
            streamlitInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.value = "";  // clear js input
        }}, 1000);  // 1 second delay
    }}
}});
</script>
"""
st.components.v1.html(js, height=50)
