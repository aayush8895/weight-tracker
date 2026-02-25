import streamlit as st

# Must be the first line
st.set_page_config(page_title="Weight Tracker", initial_sidebar_state="collapsed")

# Define the pages pointing to your separate files
home_page = st.Page("views/home.py", title="Weight Tracker", icon="🏠", default=True)
log_page = st.Page("views/log_weight.py", title="Log Weight", icon="⚖️")



# # Using position="hidden" removes the sidebar navigation menu entirely
pg = st.navigation([home_page, log_page], position="hidden")

pg.run()