import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import date
import time

st.set_page_config(page_title="Log Weight", initial_sidebar_state="collapsed")  # Must be FIRST line after imports

st.title("⚖️ Log Your Weight")

conn = st.connection("gsheets", type=GSheetsConnection)
df = st.session_state.df  # Use the same DataFrame from home.py to ensure consistency

weight = st.number_input("Enter weight (kg)", min_value=0.0, step=0.1)
log_date = st.date_input("Date", value=date.today())

col1, col2 = st.columns(2)
with col1:
    if st.button("✅ Save", use_container_width=True):
        import pandas as pd
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        updated_df = df._append({"Date": log_date, "Weight": weight}, ignore_index=True)
        conn.update(worksheet="Sheet2", data=updated_df)
        st.success("Weight saved!")
        st.session_state.df = updated_df  # Update session state with new DataFrame
        time.sleep(1)
        st.switch_page("views/home.py")  # ✅ Go back to home

with col2:
    if st.button("❌ Cancel", use_container_width=True):
        st.switch_page("views/home.py")  # ✅ Go back without saving