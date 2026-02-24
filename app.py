import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
import time

filter1 = 30
filter2 = 365
filter3 = 365*3


st.title("Weight tracker")

conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Sheet2")

# st.dataframe(df)

df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date

# st.dataframe(df)

lastWeight = str(df['Weight'][len(df)-1])
# lastWeightLogDate = pd.to_datetime(df['Date'][len(df)-1]).date()
lastWeightLogDate = df['Date'][len(df)-1]
st.write(f"Current: {lastWeight} on {lastWeightLogDate}")

# st.line_chart(df,x="Date",y="Weight")





import streamlit as st

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        width: 100%;
    }
    .stTabs [data-baseweb="tab"] {
        flex-grow: 1;
        justify-content: center;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["1 Month", "1 Year", "3 Years"])

with tab1:
    filter1df = df[(df['Date'] >=  date.today() - timedelta(days=filter1)) ]
    # st.dataframe(filter1df)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Avg", value=round(filter1df['Weight'].mean(), 1), border=True,)
    
    with col2:
        st.metric(label="Min", value=filter1df['Weight'].min(), border=True)
    

    with col3:
        st.metric(label="Max", value=filter1df['Weight'].max(), border=True)
    fig = px.line(filter1df, x='Date', y='Weight')
    st.plotly_chart(fig) 

with tab2:
    filter2df = df[(df['Date'] >=  date.today() - timedelta(days=filter2)) ]
    # st.dataframe(filter1df)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Avg", value=round(filter2df['Weight'].mean(), 1), border=True,)
    
    with col2:
        st.metric(label="Min", value=filter2df['Weight'].min(), border=True)
    
    with col3:
        st.metric(label="Max", value=filter2df['Weight'].max(), border=True)
    fig = px.line(filter2df, x='Date', y='Weight')
    st.plotly_chart(fig)

with tab3:
    filter3df = df[(df['Date'] >=  date.today() - timedelta(days=filter3)) ]
    # st.dataframe(filter1df)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Avg", value=round(filter3df['Weight'].mean(), 1), border=True,)
    
    with col2:
        st.metric(label="Min", value=filter3df['Weight'].min(), border=True)
    
    with col3:
        st.metric(label="Max", value=filter3df['Weight'].max(), border=True)
    fig = px.line(filter3df, x='Date', y='Weight')
    st.plotly_chart(fig)

with st.form("add_weight"):
    new_date = st.date_input("Date", value=date.today())
    new_weight = st.number_input("Weight", min_value=0.0, step=0.1)
    submitted = st.form_submit_button("Add")

    if submitted:
        conn.update(worksheet="Sheet2", data=df._append({"Date": new_date, "Weight": new_weight}, ignore_index=True))
        st.success("Weight added!")
        # st.delay(2)
        time.sleep(2)
        st.rerun()
