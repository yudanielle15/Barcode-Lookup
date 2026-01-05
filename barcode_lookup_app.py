import streamlit as st

# Disable caching for this session
if hasattr(st, "cache_data"):
    st.cache_data.clear()
if hasattr(st, "cache_resource"):
    st.cache_resource.clear()

