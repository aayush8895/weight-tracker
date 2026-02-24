import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go  # Added for better charting
from streamlit_gsheets import GSheetsConnection
from datetime import date, timedelta


# --- AUTH GATE ---
if not st.user.is_logged_in:
    st.title("📧 Email Dashboard")
    st.write("Please log in to continue.")
    st.button("Log in with Google", on_click=st.login)
    st.stop()

# --- EMAIL ALLOWLIST ---
ALLOWED_EMAILS = ["aayush8895@gmail.com"]

if st.user.email not in ALLOWED_EMAILS:
    st.error(f"Access denied. Your account ({st.user.email}) is not authorized to use this app.")
    st.button("Log out", on_click=st.logout)
    st.stop()

# --- YOUR ACTUAL APP STARTS HERE ---
st.sidebar.write(f"Logged in as {st.user.email}")
st.sidebar.button("Log out", on_click=st.logout)

# ... rest of your app.py code below ...

API_URL = "https://script.google.com/macros/s/AKfycbwhjKRD51zeX48m--l07euUq_oYoNBUbt-kY6B8u7-Gu-idjuGICdHUQu9NZIzTrxpgTg/exec"

st.set_page_config(page_title="Email Productivity", layout="wide")
# st.title("📧 Email Performance Dashboard")



# --- 1. Fetch Data ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Sheet2")

# st.dataframe(df)


# --- 2. Data Cleaning ---
df['msg_date'] = pd.to_datetime(df['msg_date']).dt.date
read_col_name = df.columns[-1] 
df['Read date'] = pd.to_datetime(df[read_col_name], errors='coerce').dt.date

total_rec_email_count=len(df)
total_read_df = df[df['Read date'].notnull()].copy()
total_read_email_count=len(total_read_df)
total_unread_email_count = total_rec_email_count-total_read_email_count

# st.dataframe(df)
# --- 3. Sidebar Filters ---
st.sidebar.header("Dashboard Controls")
# group_choice = st.sidebar.selectbox("Group By:", options=["Day", "Week", "Month"], index=0)
# group_map = {"Day": "D", "Week": "W", "Month": "ME"}

min_date = df['msg_date'].min()
max_date = df['msg_date'].max()
user_selection = st.sidebar.date_input("Select Date Range", value=(date.today()-timedelta(days=6), date.today()))

if st.sidebar.button('Sync Emails Now'):
    with st.spinner('Syncing with Gmail...'):
        try:
            # allow_redirects=True is mandatory for Google Apps Script
            response = requests.get(API_URL, allow_redirects=True)
            
            if response.status_code == 200:
                data = response.json()
                
                # Display success message with all three stats
                st.success(f"Sync Complete!")
                
                # Create three columns for metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("New Emails", data['newEmails'])
                col2.metric("Marked Read", data['markedRead'])
                col3.metric("Removed (Deleted)", data['deleted'])
                
                st.info(f"🕒 Last updated at: {data['lastUpdated']}")
                
                st.cache_data.clear()
                st.cache_resource.clear()
                st.rerun()
            else:
                st.error(f"Server Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

if st.sidebar.button("clear cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("cleared")

if st.sidebar.button("rerun"):
    st.rerun()


if len(user_selection) == 2:
    # st.sidebar.write(user_selection)
    start_date, end_date = user_selection
    days_count=end_date-start_date + timedelta(days=1)
    days_count = days_count.days
    rec_mask = (df['msg_date'] >= start_date) & (df['msg_date'] <= end_date)
    rec_filtered_df = df.loc[rec_mask].copy()
    rec_emails_count = len(rec_filtered_df)
    # st.write(f"Mails recieved: {rec_emails_count}")
    # st.dataframe(rec_filtered_df)

    rec_chart_data = rec_filtered_df.groupby('msg_date')['Msg ID'].count().reset_index()
    rec_chart_data = rec_chart_data.rename(columns={'msg_date': 'Date', 'Msg ID': 'Received Count'})
    # st.write(rec_chart_data)

    read_mask = (df['Read date'] >= start_date) & (df['Read date'] <= end_date)
    read_filtered_df = df.loc[read_mask].copy()
    read_emails_count = len(read_filtered_df)
    # st.write(f"Mails read: {read_emails_count}")
    # st.dataframe(read_filtered_df)

    read_chart_data = read_filtered_df.groupby('Read date')['Msg ID'].count().reset_index()
    read_chart_data = read_chart_data.rename(columns={'Read date': 'Date', 'Msg ID': 'Read Count'})
    # st.write(read_chart_data)


    combined_df = pd.merge(rec_chart_data, read_chart_data, on='Date', how='outer')
    # --- 1. Final Data Preparation ---
    # Ensure all missing values are 0 and data is sorted
    combined_df = combined_df.fillna(0).sort_values('Date')

    # Convert Date to string to remove the "Hour" gaps on the X-axis
    combined_df['Date_Str'] = pd.to_datetime(combined_df['Date']).dt.strftime('%Y-%m-%d')

    st.title(f"In {days_count} days, you received {rec_emails_count} emails and read {read_emails_count} emails")

    read_per_day = read_emails_count/days_count
    days_to_finish = total_unread_email_count/read_per_day

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total unread",total_unread_email_count)
    m2.metric("Received per day", f"{rec_emails_count/days_count:.1f}")  # f"{total_rec/num_days:.1f}")
    m3.metric("Read per day",  f"{read_per_day:.1f}")
    m4.metric("Days to finish", f"{days_to_finish:.1f}")

    # --- 2. Create the Side-by-Side Chart ---
    st.subheader("Daily Email Volume: Received vs Read")

    st.bar_chart(
        combined_df, 
        x="Date_Str", 
        y=["Received Count", "Read Count"], 
        color=["#e82929", "#1dad15"], # Optional: Custom colors
        stack=False  # THIS IS KEY: It moves bars from on top of each other to side-by-side
    )
else:
    st.info("Please select a valid date range.")