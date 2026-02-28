import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
from streamlit_float import *

st.set_page_config(page_title="Weight Tracker", layout="centered")
float_init()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.block-container { max-width: 480px !important; padding: 1.5rem 1rem 5rem 1rem; }
.stTabs [data-baseweb="tab-list"] { display: flex; width: 100%; }
.stTabs [data-baseweb="tab"]      { flex-grow: 1; justify-content: center; text-align: center; }
#MainMenu, footer, header          { visibility: hidden; }
[data-testid="stColumn"]:last-child .stButton { display: flex; justify-content: flex-end; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
HEIGHT_M = 1.79
GOAL_KG  = 90.0

# ── Session state ─────────────────────────────────────────────────────────────
for key in ("offset1", "offset2", "offset3"):
    if key not in st.session_state:
        st.session_state[key] = 0

# ── Data ──────────────────────────────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)
if "df" not in st.session_state:
    st.session_state.df = conn.read(worksheet="Sheet1", ttl=10)


df = st.session_state.df.copy()
df["Date"]   = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True).dt.date
df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")
df = df.dropna(subset=["Date", "Weight"]).sort_values("Date").reset_index(drop=True)
# st.dataframe(df)

if df.empty:
    st.error("No data found in the sheet.")
    st.stop()

latest_w    = df["Weight"].iloc[-1]
latest_date = df["Date"].iloc[-1]

# ── BMI bar ───────────────────────────────────────────────────────────────────
def bmi_indicator(bmi):
    if bmi < 18.5:   cat, col = "Underweight", "#3b82f6"
    elif bmi < 25:   cat, col = "Normal",       "#22c55e"
    elif bmi < 30:   cat, col = "Overweight",   "#f97316"
    else:            cat, col = "Obese",         "#ef4444"

    stops_bmi = [10, 18.5, 25, 30, 45]
    stops_pct = [0,  24,   50, 64, 100]
    pct = 0
    for i in range(len(stops_bmi) - 1):
        if stops_bmi[i] <= bmi <= stops_bmi[i+1]:
            t   = (bmi - stops_bmi[i]) / (stops_bmi[i+1] - stops_bmi[i])
            pct = stops_pct[i] + t * (stops_pct[i+1] - stops_pct[i])
            break
    pct = min(max(pct, 0), 100)

    st.markdown(f"""
    <div style="padding:14px 16px;border-radius:14px;background:rgba(128,128,128,0.08);margin-bottom:12px;">
        <div style="font-size:11px;color:light-dark(#6b7280,#9ca3af);margin-bottom:8px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;">BMI</div>
        <div style="position:relative;height:10px;border-radius:999px;overflow:hidden;display:flex;">
            <div style="width:24%;background:#3b82f6;"></div>
            <div style="width:26%;background:#22c55e;"></div>
            <div style="width:14%;background:#f97316;"></div>
            <div style="width:36%;background:#ef4444;"></div>
        </div>
        <div style="position:relative;height:12px;margin-top:1px;">
            <div style="position:absolute;left:{pct}%;transform:translateX(-50%);">
                <div style="width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:9px solid {col};"></div>
            </div>
        </div>
        <div style="display:flex;font-size:10px;color:light-dark(#6b7280,#9ca3af);">
            <span style="width:24%;">Underweight</span>
            <span style="width:26%;text-align:center;">Normal</span>
            <span style="width:14%;text-align:center;">Overweight</span>
            <span style="width:36%;text-align:right;">Obese</span>
        </div>
        <div style="text-align:center;margin-top:6px;font-weight:700;color:{col};font-size:13px;">{bmi} — {cat}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Tab renderer ──────────────────────────────────────────────────────────────
def render_tab(offset_key, days, label_fmt):
    # ── Period nav ABOVE chart ──
    offset = st.session_state[offset_key]
    end    = date.today() - timedelta(days=days * offset)
    start  = end - timedelta(days=days)

    c1, c2, c3 = st.columns(3, vertical_alignment="center")
    with c1:
        if st.button("◀", key=f"prev_{offset_key}"):
            st.session_state[offset_key] += 1
            st.rerun()
    with c2:
        st.markdown(
            f"<div style='text-align:center;font-size:12px;color:light-dark(#6b7280,#9ca3af);'>"
            f"{start.strftime(label_fmt)} → {end.strftime(label_fmt)}</div>",
            unsafe_allow_html=True
        )
    with c3:
        st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
        if st.button("▶", key=f"next_{offset_key}", disabled=offset == 0):
            st.session_state[offset_key] = max(st.session_state[offset_key] - 1, 0)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    fdf      = df[(df["Date"] > start) & (df["Date"] <= end)]
    prev_fdf = df[(df["Date"] > start - timedelta(days=days)) & (df["Date"] <= start)]

    if fdf.empty:
        st.info("No data for this period.")
        return

    # BMI based on latest weight in period
    period_latest = fdf["Weight"].iloc[-1]
    bmi_indicator(round(period_latest / (HEIGHT_M ** 2), 1))

    # Metrics
    avg_cur  = round(fdf["Weight"].mean(), 1)
    avg_prev = round(prev_fdf["Weight"].mean(), 1) if not prev_fdf.empty else None
    avg_delta = round(avg_cur - avg_prev, 1) if avg_prev is not None else None
    avg_delta_str = (f"+{avg_delta}" if avg_delta is not None and avg_delta > 0 else str(avg_delta)) if avg_delta is not None else None

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Avg (kg)", avg_cur, delta=avg_delta_str, delta_color="inverse", border=True)
    with c2:
        st.metric("Min (kg)", round(fdf["Weight"].min(), 1), border=True)
    with c3:
        st.metric("Max (kg)", round(fdf["Weight"].max(), 1), border=True)

    # Chart
    fig = px.line(fdf, x="Date", y="Weight", markers=True,
                  color_discrete_sequence=["#3b82f6"])
    fig.update_layout(
        margin=dict(t=10, b=10, l=0, r=0), height=220,
        xaxis_title=None, yaxis_title=None,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.15)"),
    )
    st.plotly_chart(fig, width="stretch")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Header
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="margin-bottom:16px;">
    <div style="font-size:26px;font-weight:800;color:light-dark(#111827,#f9fafb);">Weight Tracker</div>
    <div style="font-size:13px;color:light-dark(#6b7280,#9ca3af);">Last logged: <b>{latest_w} kg</b> on {latest_date}</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Period tabs
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["1 Month", "1 Year", "3 Years"])

with tab1:
    render_tab("offset1", 30,      "%b %d")
with tab2:
    render_tab("offset2", 365,     "%b %Y")
with tab3:
    render_tab("offset3", 365 * 3, "%Y")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Goal & History
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🎯 Goal")

to_go      = round(latest_w - GOAL_KG, 1)
goal_pct   = 100 if to_go <= 0 else max(0, min(100, int((GOAL_KG / latest_w) * 100)))
goal_color = "#22c55e" if to_go <= 0 else "#3b82f6"
goal_label = "🎉 Goal reached!" if to_go <= 0 else f"{to_go} kg to go"

st.markdown(f"""
<div style="padding:14px 16px;border-radius:14px;background:rgba(128,128,128,0.08);margin-bottom:12px;">
    <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:8px;">
        <span style="color:light-dark(#374151,#d1d5db);font-weight:600;">Current: {latest_w} kg</span>
        <span style="color:light-dark(#374151,#d1d5db);font-weight:600;">Goal: {GOAL_KG} kg</span>
    </div>
    <div style="height:10px;border-radius:999px;background:rgba(128,128,128,0.2);overflow:hidden;">
        <div style="height:100%;width:{goal_pct}%;background:{goal_color};border-radius:999px;"></div>
    </div>
    <div style="text-align:center;margin-top:8px;font-size:13px;font-weight:700;color:{goal_color};">{goal_label}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 📋 History")

hist = df[["Date", "Weight"]].sort_values("Date", ascending=False).reset_index(drop=True)
hist["Change"] = hist["Weight"].diff(-1).round(1)
hist["Change"] = hist["Change"].apply(
    lambda x: f"+{x}" if pd.notna(x) and x > 0 else (str(x) if pd.notna(x) else "—")
)
st.dataframe(hist, width="stretch", hide_index=True)

# ── Sticky Log Button ─────────────────────────────────────────────────────────
if "go_to_log" not in st.session_state:
    st.session_state.go_to_log = False

btn = st.container()
with btn:
    if st.button("➕ Log Weight", width="stretch"):
        st.session_state.go_to_log = True
        st.rerun()
btn.float("bottom: 1.5rem; left: 50%; transform: translateX(-50%); width: 200px;")

if st.session_state.go_to_log:
    st.session_state.go_to_log = False
    st.switch_page("pages/log_weight.py")
