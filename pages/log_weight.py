import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time

st.set_page_config(page_title="Log Weight", layout="centered")

st.markdown("""
<style>
.block-container { max-width: 480px !important; padding: 1.5rem 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("## Log Weight")

conn = st.connection("gsheets", type=GSheetsConnection)

# Read latest weight to pre-fill the field
raw_df = conn.read(worksheet="Sheet1", ttl=0)
raw_df["Date"]   = pd.to_datetime(raw_df["Date"], errors="coerce").dt.date
raw_df["Weight"] = pd.to_numeric(raw_df["Weight"], errors="coerce")
raw_df = raw_df.dropna(subset=["Date", "Weight"]).sort_values("Date").reset_index(drop=True)

latest_weight = float(raw_df["Weight"].iloc[-1]) if not raw_df.empty else 0.0

with st.form("log_weight_form"):
    new_date   = st.date_input("Date", value=date.today())
    new_weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1, value=latest_weight)
    submitted  = st.form_submit_button("Save", width="stretch")

if submitted:
    df = conn.read(worksheet="Sheet1", ttl=0)
    df["Date"]   = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")

    existing = df["Date"] == new_date
    if existing.any():
        df.loc[existing, "Weight"] = new_weight
        msg = "Weight updated!"
    else:
        df = df._append({"Date": new_date, "Weight": new_weight}, ignore_index=True)
        msg = "Weight logged!"

    conn.update(worksheet="Sheet1", data=df)

    if "df" in st.session_state:
        del st.session_state["df"]
    st.success(msg)
    time.sleep(1)
    st.switch_page("app.py")

if st.button("← Back"):
    st.switch_page("app.py")
