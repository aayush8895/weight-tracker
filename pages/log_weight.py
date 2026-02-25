import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import date
import time
import pandas as pd

st.set_page_config(page_title="Log Weight", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.block-container { max-width: 480px !important; padding: 1.5rem 1rem; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)
if "df" not in st.session_state:
    st.session_state.df = conn.read(worksheet="Sheet2", ttl=10)

df = st.session_state.df.copy()
df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")

last_weight = df["Weight"].iloc[-1]

st.markdown("### ⚖️ Log Your Weight")
st.markdown(f"<div style='font-size:13px; color:gray; margin-bottom:16px;'>Last logged: <b>{last_weight} kg</b></div>",
            unsafe_allow_html=True)

log_date = st.date_input("Date", value=date.today())
weight   = st.number_input("Weight (kg)", value=float(last_weight), min_value=0.0, step=0.1)

# Delta preview
delta = round(weight - last_weight, 1)
delta_color = "#ef4444" if delta > 0 else "#22c55e" if delta < 0 else "#9ca3af"
delta_str   = f"+{delta}" if delta > 0 else str(delta)
if delta != 0:
    st.markdown(
        f"<div style='font-size:13px; color:{delta_color}; margin-bottom:12px;'>{delta_str} kg from last entry</div>",
        unsafe_allow_html=True
    )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("✅ Save", use_container_width=True):
        with st.spinner("Saving..."):
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
            updated_df = df._append({"Date": log_date, "Weight": weight}, ignore_index=True)
            conn.update(worksheet="Sheet2", data=updated_df)
        st.success("Saved!")
        st.session_state.df = updated_df
        time.sleep(1)
        st.switch_page("views/home.py")

with col2:
    if st.button("❌ Cancel", use_container_width=True):
        st.switch_page("views/home.py")