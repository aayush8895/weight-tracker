import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_float import *

st.set_page_config(page_title="Weight Tracker", layout="centered")
float_init()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Narrow mobile-like content */
.block-container { max-width: 480px !important; padding: 1.5rem 1rem 5rem 1rem; }

/* Full-width tabs */
.stTabs [data-baseweb="tab-list"] { display: flex; width: 100%; }
.stTabs [data-baseweb="tab"]      { flex-grow: 1; justify-content: center; text-align: center; }

/* Metric cards */
div[data-testid="stMetric"] { border-radius: 12px; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
for key, val in {"offset1": 0, "offset2": 0, "offset3": 0}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Data ──────────────────────────────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)
if "df" not in st.session_state:
    st.session_state.df = conn.read(worksheet="Sheet2", ttl=10)

df = st.session_state.df.copy()
df["Date"]   = pd.to_datetime(df["Date"], errors="coerce").dt.date
df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")
df = df.dropna(subset=["Date", "Weight"]).sort_values("Date").reset_index(drop=True)

HEIGHT_M  = 1.778   # ← change your height here
GOAL_KG   = 90.0    # ← change your goal weight here

# ── Helper: BMI bar ───────────────────────────────────────────────────────────
def bmi_indicator(bmi):
    if bmi < 18.5:   cat, col = "Underweight", "#3b82f6"
    elif bmi < 25:   cat, col = "Normal",       "#22c55e"
    elif bmi < 30:   cat, col = "Overweight",   "#f97316"
    else:            cat, col = "Obese",         "#ef4444"

    bmi_stops = [10, 18.5, 25, 30, 45]
    pct_stops = [0,  24,   50, 64, 100]
    pct = 0
    for i in range(len(bmi_stops) - 1):
        if bmi_stops[i] <= bmi <= bmi_stops[i+1]:
            t   = (bmi - bmi_stops[i]) / (bmi_stops[i+1] - bmi_stops[i])
            pct = pct_stops[i] + t * (pct_stops[i+1] - pct_stops[i])
            break
    pct = min(max(pct, 0), 100)

    st.markdown(f"""
    <div style="padding:14px 16px; border-radius:14px; background:rgba(128,128,128,0.08); margin-bottom:8px;">
        <div style="font-size:12px; color:light-dark(#6b7280,#9ca3af); margin-bottom:8px; font-weight:500;">BMI</div>
        <div style="position:relative; height:10px; border-radius:999px; overflow:hidden; display:flex;">
            <div style="width:24%; background:#3b82f6;"></div>
            <div style="width:26%; background:#22c55e;"></div>
            <div style="width:14%; background:#f97316;"></div>
            <div style="width:36%; background:#ef4444;"></div>
        </div>
        <div style="position:relative; height:12px; margin-top:1px;">
            <div style="position:absolute; left:{pct}%; transform:translateX(-50%);">
                <div style="width:0; height:0;
                    border-left:6px solid transparent;
                    border-right:6px solid transparent;
                    border-bottom:9px solid {col};"></div>
            </div>
        </div>
        <div style="display:flex; font-size:10px; color:light-dark(#6b7280,#9ca3af);">
            <span style="width:24%;">Underweight</span>
            <span style="width:26%; text-align:center;">Normal</span>
            <span style="width:14%; text-align:center;">Overweight</span>
            <span style="width:36%; text-align:right;">Obese</span>
        </div>
        <div style="text-align:center; margin-top:6px; font-weight:700; color:{col}; font-size:13px;">
            {bmi} — {cat}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Helper: period nav ────────────────────────────────────────────────────────
def period_nav(offset_key, days, label_fmt):
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1:
        if st.button("◀", key=f"prev_{offset_key}"):
            st.session_state[offset_key] += 1
            st.rerun()
    with c3:
        if st.button("▶", key=f"next_{offset_key}"):
            st.session_state[offset_key] = max(st.session_state[offset_key] - 1, 0)
            st.rerun()
    offset = st.session_state[offset_key]
    end    = date.today() - timedelta(days=days * offset)
    start  = end - timedelta(days=days)
    with c2:
        st.markdown(
            f"<div style='text-align:center; font-size:12px; color:light-dark(#6b7280,#9ca3af); padding-top:6px;'>"
            f"{start.strftime(label_fmt)} → {end.strftime(label_fmt)}</div>",
            unsafe_allow_html=True
        )
    return start, end

# ── Helper: render tab ────────────────────────────────────────────────────────
def render_tab(fdf, prev_fdf):
    if fdf.empty:
        st.info("No data for this period.")
        return

    latest_w = fdf["Weight"].iloc[-1]
    bmi      = round(latest_w / (HEIGHT_M ** 2), 1)
    bmi_indicator(bmi)

    # Delta vs previous period
    delta = None
    if not prev_fdf.empty:
        delta = round(latest_w - prev_fdf["Weight"].iloc[-1], 1)
        delta_str = f"+{delta} kg" if delta > 0 else f"{delta} kg"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Avg", f"{round(fdf['Weight'].mean(), 1)} kg", border=True)
    with c2:
        st.metric("Min", f"{fdf['Weight'].min()} kg", border=True)
    with c3:
        st.metric("Max", f"{fdf['Weight'].max()} kg",
                  delta=delta_str if delta is not None else None,
                  delta_color="inverse",
                  border=True)

    fig = px.line(fdf, x="Date", y="Weight",
                  markers=True,
                  color_discrete_sequence=["#3b82f6"])
    fig.update_layout(
        margin=dict(t=10, b=10, l=0, r=0),
        height=220,
        xaxis_title=None, yaxis_title=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.15)"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Header
# ═══════════════════════════════════════════════════════════════════════════════
latest_w    = df["Weight"].iloc[-1]
latest_date = df["Date"].iloc[-1]

st.markdown(f"""
<div style="margin-bottom:16px;">
    <div style="font-size:26px; font-weight:800; color:light-dark(#111827,#f9fafb);">Weight Tracker</div>
    <div style="font-size:13px; color:light-dark(#6b7280,#9ca3af);">Last logged: <b>{latest_w} kg</b> on {latest_date}</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Charts with period nav
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["1 Month", "1 Year", "3 Years"])

with tab1:
    start, end = period_nav("offset1", 30, "%b %d")
    fdf      = df[(df["Date"] > start) & (df["Date"] <= end)]
    prev_end = start
    prev_start = prev_end - timedelta(days=30)
    prev_fdf = df[(df["Date"] > prev_start) & (df["Date"] <= prev_end)]
    render_tab(fdf, prev_fdf)

with tab2:
    start, end = period_nav("offset2", 365, "%b %Y")
    fdf      = df[(df["Date"] > start) & (df["Date"] <= end)]
    prev_fdf = df[(df["Date"] > start - timedelta(days=365)) & (df["Date"] <= start)]
    render_tab(fdf, prev_fdf)

with tab3:
    start, end = period_nav("offset3", 365*3, "%Y")
    fdf      = df[(df["Date"] > start) & (df["Date"] <= end)]
    prev_fdf = df[(df["Date"] > start - timedelta(days=365*3)) & (df["Date"] <= start)]
    render_tab(fdf, prev_fdf)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Goal & History
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🎯 Goal Tracker")

to_go      = round(latest_w - GOAL_KG, 1)
goal_pct   = max(0, min(100, int((1 - to_go / max(latest_w - GOAL_KG + 1, 1)) * 100))) if to_go > 0 else 100
goal_color = "#22c55e" if to_go <= 0 else "#3b82f6"
goal_label = "🎉 Goal reached!" if to_go <= 0 else f"{to_go} kg to go"

st.markdown(f"""
<div style="padding:14px 16px; border-radius:14px; background:rgba(128,128,128,0.08); margin-bottom:8px;">
    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:8px;">
        <span style="color:light-dark(#374151,#d1d5db); font-weight:600;">Current: {latest_w} kg</span>
        <span style="color:light-dark(#374151,#d1d5db); font-weight:600;">Goal: {GOAL_KG} kg</span>
    </div>
    <div style="height:10px; border-radius:999px; background:rgba(128,128,128,0.2); overflow:hidden;">
        <div style="height:100%; width:{goal_pct}%; background:{goal_color}; border-radius:999px; transition:width 0.3s;"></div>
    </div>
    <div style="text-align:center; margin-top:8px; font-size:13px; font-weight:700; color:{goal_color};">
        {goal_label}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 📋 History")

display_df = df[["Date", "Weight"]].sort_values("Date", ascending=False).reset_index(drop=True)
display_df["Change"] = display_df["Weight"].diff(-1).mul(-1).round(1)
display_df["Change"] = display_df["Change"].apply(
    lambda x: f"+{x}" if pd.notna(x) and x > 0 else (str(x) if pd.notna(x) else "—")
)
st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── Sticky Log Button ─────────────────────────────────────────────────────────
btn = st.container()
with btn:
    if st.button("➕ Log Weight", use_container_width=True):
        st.switch_page("views/log_weight.py")
btn.float("bottom: 1.5rem; left: 50%; transform: translateX(-50%); width: 200px;")