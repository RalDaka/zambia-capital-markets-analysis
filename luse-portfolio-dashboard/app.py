import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import calendar
import numpy as np
from supabase import create_client

# ──────────────────────────────────────────────
# SUPABASE CONFIG
# ──────────────────────────────────────────────
SUPABASE_URL = "https://pkqekyvzwtarmjujcfva.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBrcWVreXZ6d3Rhcm1qdWpjZnZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkyMDc4MzAsImV4cCI6MjA5NDc4MzgzMH0.cl1FFhofy4QxLq330pl6nQLRwMkCS6Y7rlWQpD1lLyo"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="LuSE Portfolio Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# FOREX-DASHBOARD INSPIRED CSS
# ──────────────────────────────────────────────
st.markdown(
    """
<style>
    /* ── Reset & Base ── */
    #root > div:nth-child(1) > div > div > div > div > section > div {
        padding-top: 0 !important;
    }
    .stApp {
        background: #0f141b;
    }
    .main > div {
        background: #0f141b;
    }
    .block-container {
        max-width: 1400px;
        padding: 0 24px 34px !important;
        margin: 0 auto;
    }

    /* ── Typography ── */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
        color: #e6edf3;
    }

    /* ── App Header ── */
    .app-header {
        background: #0b1118;
        border-bottom: 1px solid #2a3441;
        padding: 18px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 0 -24px 18px;
    }
    .app-header h1 {
        margin: 0;
        font-size: 20px;
        font-weight: 700;
        color: #e6edf3;
    }
    .app-header .subtitle {
        margin: 2px 0 0;
        color: #9aa8b5;
        font-size: 13px;
    }
    .header-badge {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 0px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge.green { background: #102219; color: #74d99f; border: 1px solid #26734c; }
    .badge.blue { background: #0a1a33; color: #6ea8ff; border: 1px solid #1f4a8a; }
    .badge.amber { background: #1f1a0e; color: #e8a838; border: 1px solid #7a5f1a; }

    /* ── Overview Panel ── */
    .overview-panel {
        background: #151b23;
        border: 1px solid #2a3441;
        border-radius: 0px;
        padding: 16px 20px;
        margin-bottom: 18px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 20px;
    }
    .overview-item {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .overview-item .label {
        font-size: 11px;
        color: #9aa8b5;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .overview-item .value {
        font-size: 15px;
        font-weight: 700;
        color: #e6edf3;
    }
    .overview-item .value.small {
        font-size: 13px;
        font-weight: 400;
        color: #9aa8b5;
    }
    .overview-item .value.green { color: #74d99f; }
    .overview-item .value.red { color: #ff8b8b; }
    .overview-item .value.amber { color: #f0b86a; }
    .overview-item .value.blue { color: #6ea8ff; }
    .overview-divider {
        width: 1px;
        height: 36px;
        background: #2a3441;
    }

    /* ── Section Cards ── */
    .section-card {
        background: #151b23;
        border: 1px solid #2a3441;
        border-radius: 0px;
        padding: 16px 18px;
        margin-bottom: 24px;
    }
    .section-card .section-title {
        font-size: 16px;
        font-weight: 700;
        color: #e6edf3;
        margin: 0 0 2px;
    }
    .section-card .section-subtitle {
        font-size: 13px;
        color: #9aa8b5;
        margin: 0 0 18px;
    }

    /* ── Spacing between elements inside section cards ── */
    .section-card .stSelectbox, .section-card .stDateInput, .section-card .stNumberInput {
        margin-bottom: 16px !important;
    }
    .section-card .element-spacer {
        height: 12px;
    }
    .section-card .row-spacer {
        height: 16px;
    }
    .section-card .stPlotlyChart {
        margin-top: 8px;
        margin-bottom: 16px;
    }
    .section-card .stDataFrame {
        margin-top: 8px;
        margin-bottom: 12px;
    }
    .section-card .row-widget.stHorizontal {
        margin-bottom: 24px;
    }
    .section-card .stMarkdown {
        margin-bottom: 4px;
    }
    .section-card .stExpander {
        margin-top: 16px;
        margin-bottom: 4px;
    }
    .section-card .data-note {
        margin-bottom: 16px;
    }
    .section-card .interpretation-box {
        margin-bottom: 20px;
    }
    .section-card .metric-card {
        margin-bottom: 0;
    }
    /* Ensure spacing between metric card rows and what follows */
    .section-card .row-widget.stHorizontal + .stPlotlyChart,
    .section-card .row-widget.stHorizontal + .stMarkdown,
    .section-card .row-widget.stHorizontal + .interpretation-box {
        margin-top: 20px !important;
    }
    /* Target the element-container that wraps st.columns() metric card rows */
    .section-card .element-container:has(.metric-card) {
        margin-bottom: 20px !important;
    }
    /* Target the column wrapper that contains metric cards */
    .section-card div[data-testid="column"]:has(.metric-card) {
        margin-bottom: 0;
    }
    /* Add spacing after any element-container that contains metric cards */
    .section-card .element-container:has(.metric-card) + .element-container {
        margin-top: 20px !important;
    }
    /* Ensure spacing between chart and what follows */
    .section-card .stPlotlyChart + .row-widget.stHorizontal {
        margin-top: 8px;
    }
    /* Ensure spacing between table and interpretation box */
    .section-card .stDataFrame + .interpretation-box {
        margin-top: 12px;
    }
    /* Ensure spacing between interpretation box and expander */
    .section-card .interpretation-box + .stExpander {
        margin-top: 20px;
    }

    /* ── Metric Cards ── */
    .metric-card {
        background: #111820;
        border: 1px solid #2a3441;
        border-radius: 0px;
        padding: 12px 14px;
    }
    .metric-card .metric-label {
        font-size: 11px;
        color: #9aa8b5;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .metric-card .metric-value {
        font-size: 15px;
        font-weight: 700;
        color: #e6edf3;
    }
    .metric-card .metric-value.green { color: #74d99f; }
    .metric-card .metric-value.red { color: #ff8b8b; }
    .metric-card .metric-value.amber { color: #f0b86a; }
    .metric-card .metric-value.blue { color: #6ea8ff; }

    /* ── Status Badge (inline) ── */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 0px;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
    }
    .status-badge .dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-badge.good { background: #102219; color: #74d99f; border: 1px solid #26734c; }
    .status-badge.good .dot { background: #74d99f; }
    .status-badge.warn { background: #1f1a0e; color: #e8a838; border: 1px solid #7a5f1a; }
    .status-badge.warn .dot { background: #e8a838; }
    .status-badge.bad { background: #2a1212; color: #ff8b8b; border: 1px solid #7a2f2f; }
    .status-badge.bad .dot { background: #ff8b8b; }
    .status-badge.info { background: #0a1a33; color: #6ea8ff; border: 1px solid #1f4a8a; }
    .status-badge.info .dot { background: #6ea8ff; }

    /* ── Interpretation Box ── */
    .interpretation-box {
        background: #111820;
        border: 1px solid #2a3441;
        border-radius: 0px;
        padding: 12px 14px;
        font-size: 13px;
        color: #9aa8b5;
        line-height: 1.6;
        margin-top: 12px;
        margin-bottom: 16px;
    }
    .interpretation-box strong {
        color: #e6edf3;
    }
    .interpretation-box .highlight-green { color: #74d99f; font-weight: 700; }
    .interpretation-box .highlight-red { color: #ff8b8b; font-weight: 700; }
    .interpretation-box .highlight-blue { color: #6ea8ff; font-weight: 700; }
    .interpretation-box .highlight-amber { color: #f0b86a; font-weight: 700; }

    /* ── Data Note ── */
    .data-note {
        font-size: 12px;
        color: #9aa8b5;
        font-style: italic;
        margin-top: 8px;
        margin-bottom: 20px;
        padding: 8px 10px;
        background: #111820;
        border-radius: 0px;
        border-left: 3px solid #2a3441;
    }

    /* ── Table Overrides ── */
    .stDataFrame {
        font-size: 13px;
    }
    .stDataFrame [data-testid="StyledDataFrameDataCell"] {
        font-size: 12px;
    }
    .stDataFrame thead tr th {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #9aa8b5;
        background: #0b1118;
    }

    /* ── Selectbox / Input Overrides ── */
    .stSelectbox label, .stDateInput label, .stSlider label {
        font-size: 11px !important;
        color: #9aa8b5 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background: #111820;
        border-color: #2a3441;
        border-radius: 0px;
    }
    .stDateInput input {
        background: #111820;
        border-color: #2a3441;
        border-radius: 0px;
        color: #e6edf3;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #111820;
        border-radius: 0px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0px;
        font-size: 12px;
        font-weight: 600;
        color: #9aa8b5;
    }
    .stTabs [aria-selected="true"] {
        background: #0a1a33;
        color: #6ea8ff;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #2a3441; border-radius: 0px; }

    /* ── Period Return Cards ── */
    .period-card {
        background: #111820;
        border: 1px solid #2a3441;
        border-radius: 0px;
        padding: 10px 12px;
        text-align: center;
        transition: border-color 0.2s, box-shadow 0.2s;
        cursor: pointer;
    }
    .period-card:hover {
        border-color: #6ea8ff;
        box-shadow: 0 0 0 1px rgba(110, 168, 255, 0.3);
    }
    .period-card.selected {
        border-color: #6ea8ff;
        box-shadow: 0 0 0 2px rgba(110, 168, 255, 0.4);
    }
    .period-card .period-label {
        font-size: 10px;
        color: #9aa8b5;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .period-card .period-return {
        font-size: 16px;
        font-weight: 700;
    }
    .period-card .period-return.green { color: #74d99f; }
    .period-card .period-return.red { color: #ff8b8b; }
    .period-card .period-return.zero { color: #9aa8b5; }
    .period-card .period-sub {
        font-size: 10px;
        color: #6a7a8a;
        margin-top: 2px;
    }
    .period-card.full-year { border-left: 3px solid #6ea8ff; }
    .period-card.half-year { border-left: 3px solid #f0b86a; }
    .period-card.quarter { border-left: 3px solid #74d99f; }
    .period-card.month { border-left: 3px solid #9aa8b5; }

    /* ── Simulation Panel ── */
    .sim-panel {
        background: #111820;
        border: 1px solid #2a3441;
        border-radius: 0px;
        padding: 20px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .sim-panel .sim-title {
        font-size: 11px;
        color: #9aa8b5;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 16px;
    }
    .sim-panel .sim-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #1e2833;
    }
    .sim-panel .sim-row:last-child {
        border-bottom: none;
    }
    .sim-panel .sim-label {
        font-size: 13px;
        color: #9aa8b5;
    }
    .sim-panel .sim-value {
        font-size: 16px;
        font-weight: 700;
        color: #e6edf3;
    }
    .sim-panel .sim-value.green { color: #74d99f; }
    .sim-panel .sim-value.red { color: #ff8b8b; }
    .sim-panel .sim-big {
        font-size: 28px;
        font-weight: 700;
        text-align: center;
        padding: 16px 0;
    }
    .sim-panel .sim-big.green { color: #74d99f; }
    .sim-panel .sim-big.red { color: #ff8b8b; }
    .sim-panel .sim-note {
        font-size: 11px;
        color: #6a7a8a;
        text-align: center;
        margin-top: 8px;
        font-style: italic;
    }

    /* ── Responsive ── */
    @media (max-width: 768px) {
        .app-header { flex-direction: column; align-items: flex-start; gap: 10px; }
        .overview-panel { flex-direction: column; align-items: flex-start; gap: 10px; }
        .overview-divider { display: none; }
        .block-container { padding: 0 16px 24px !important; }
    }

    /* ── SVG Icon Styles ── */
    .svg-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        vertical-align: middle;
    }
    .svg-icon.live-dot {
        width: 8px;
        height: 8px;
        margin-right: 4px;
    }
    .svg-icon.info-icon {
        width: 16px;
        height: 16px;
        margin-right: 6px;
    }

    /* ── Expander Override (square corners) ── */
    .stExpander {
        border-radius: 0px !important;
    }
    .stExpander > div:first-child {
        border-radius: 0px !important;
    }
    .stExpander > div:first-child > div {
        border-radius: 0px !important;
    }
    .stExpander div[data-testid="stExpanderToggleIcon"] {
        border-radius: 0px !important;
    }
    .streamlit-expanderHeader {
        border-radius: 0px !important;
    }
    .streamlit-expanderContent {
        border-radius: 0px !important;
    }

    /* ── Hide Streamlit Branding ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────


@st.cache_data(ttl=300)
def get_table_summary():
    """Get aggregate summary stats via SQL RPC (efficient, no full-table fetch)."""
    try:
        resp = supabase.rpc("get_luse_historical_summary").execute()
        if resp.data and len(resp.data) > 0:
            return resp.data[0]
    except Exception as e:
        st.warning(f"Could not fetch table summary via RPC: {e}")
    return None


@st.cache_data(ttl=300)
def get_distinct_tickers():
    """Get distinct tickers via SQL RPC (efficient, no full-table fetch)."""
    try:
        resp = supabase.rpc("get_luse_distinct_tickers").execute()
        if resp.data:
            return sorted([row["ticker"] for row in resp.data])
    except Exception as e:
        st.warning(f"Could not fetch distinct tickers via RPC: {e}")
    return None


@st.cache_data(ttl=300)
def load_prices():
    """Load prices via SQL RPC (efficient server-side query, no pagination)."""
    try:
        resp = supabase.rpc("get_luse_all_prices").execute()
        data = resp.data
        if not data:
            st.warning("No data found in Supabase 'luse_historical_prices' table. Please upload data first.")
            return pd.DataFrame(columns=["ticker", "date", "price", "volume", "daily_return"])
        df = pd.DataFrame(data)
        df = df.rename(columns={"trade_date": "date"})
        df["date"] = pd.to_datetime(df["date"])
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
        df["daily_return"] = pd.to_numeric(df["daily_return"], errors="coerce")
        df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
        return df
    except Exception as e:
        st.warning(f"Could not fetch prices via RPC: {e}")
        return pd.DataFrame(columns=["ticker", "date", "price", "volume", "daily_return"])


@st.cache_data(ttl=300)
def load_index():
    """Load index via SQL RPC (efficient server-side query, no pagination)."""
    try:
        resp = supabase.rpc("get_luse_all_index").execute()
        data = resp.data
        if not data:
            st.warning("No data found in Supabase 'luse_index' table. Please upload data first.")
            return pd.DataFrame(columns=["date", "price", "ticker"])
        df = pd.DataFrame(data)
        df = df.rename(columns={"index_date": "date", "luse_index": "price"})
        df["date"] = pd.to_datetime(df["date"])
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["ticker"] = "LuSE Index"
        df = df.sort_values("date").reset_index(drop=True)
        return df
    except Exception as e:
        st.warning(f"Could not fetch index via RPC: {e}")
        return pd.DataFrame(columns=["date", "price", "ticker"])


prices = load_prices()
index_df = load_index()

# Try to get tickers from efficient RPC first, fall back to prices DataFrame
rpc_tickers = get_distinct_tickers()
if rpc_tickers:
    tickers = rpc_tickers
else:
    tickers = sorted(prices["ticker"].unique())
ALL_TICKERS = ["LuSE Index"] + tickers

# ──────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────
def fmt_pct(v):
    if pd.isna(v) or v is None:
        return "\u2014"
    return f"{v:+.2f}%"


def fmt_kwacha(v):
    if pd.isna(v) or v is None:
        return "\u2014"
    return f"K{v:,.2f}"


def fmt_volume(v):
    if pd.isna(v) or v is None:
        return "\u2014"
    if v >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{v:.0f}"


def color_for_change(val):
    if pd.isna(val) or val is None:
        return ""
    if val > 0:
        return "green"
    if val < 0:
        return "red"
    return ""


def compute_return(series):
    valid = series.dropna()
    if len(valid) < 2:
        return None
    return (valid.iloc[-1] - valid.iloc[0]) / valid.iloc[0] * 100


def get_price_range(series):
    valid = series.dropna()
    if len(valid) < 2:
        return None, None
    return valid.iloc[0], valid.iloc[-1]


def build_plotly_layout(title="", y_title=""):
    return dict(
        paper_bgcolor="#151b23",
        plot_bgcolor="#151b23",
        font=dict(
            color="#e6edf3",
            size=12,
            family="-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif",
        ),
        title=dict(
            text=title, font=dict(size=14, color="#e6edf3"), x=0, xanchor="left"
        ),
        hovermode="x unified",
    )


# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
st.markdown(
    f"""
<div class="app-header">
    <div>
        <h1>LuSE Portfolio Analytics Dashboard</h1>
        <div class="subtitle">LuSE Stock Exchange — performance, activity & data quality analysis</div>
    </div>
    <div class="header-badge">
        <span class="badge green"><svg class="svg-icon live-dot" viewBox="0 0 8 8" fill="none"><circle cx="4" cy="4" r="3" fill="#74d99f"/></svg> Live Data</span>
        <span class="badge blue">{len(tickers)} Companies</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# OVERVIEW PANEL
# ──────────────────────────────────────────────
latest_price_date = prices["date"].max()
latest_index_row = index_df[index_df["date"] == index_df["date"].max()]
latest_index_val = (
    latest_index_row["price"].values[0] if len(latest_index_row) > 0 else None
)
total_volume_30d = prices[
    prices["date"] >= prices["date"].max() - pd.Timedelta(days=30)
]["volume"].sum()

st.markdown(
    f"""
<div class="overview-panel">
    <div class="overview-item">
        <span class="label">Companies Tracked</span>
        <span class="value blue">{len(tickers)}</span>
    </div>
    <div class="overview-divider"></div>
    <div class="overview-item">
        <span class="label">LuSE Index</span>
        <span class="value">{f'K{latest_index_val:,.2f}' if latest_index_val else '—'}</span>
    </div>
    <div class="overview-divider"></div>
    <div class="overview-item">
        <span class="label">30-Day Volume</span>
        <span class="value">{fmt_volume(total_volume_30d)}</span>
    </div>
    <div class="overview-divider"></div>
    <div class="overview-item">
        <span class="label">Data Range</span>
        <span class="value small">{prices['date'].min().strftime('%b %Y')} — {prices['date'].max().strftime('%b %Y')}</span>
    </div>
    <div class="overview-divider"></div>
    <div class="overview-item">
        <span class="label">Latest Price Date</span>
        <span class="value small">{latest_price_date.strftime('%d %b %Y')}</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════
# SECTION 1: HISTORICAL PERFORMANCE
# ══════════════════════════════════════════════
st.markdown(
    """
<div class="section-card">
    <h2 class="section-title">1. Historical Performance</h2>
    <p class="section-subtitle">Compare company returns over a selected period. Ranked by total return.</p>
""",
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    perf_company = st.selectbox("Select Asset", ALL_TICKERS, index=0, key="perf_company")
with col2:
    min_date = prices["date"].min().date()
    max_date = prices["date"].max().date()
    default_start = max_date - pd.Timedelta(days=365)
    start_dt = st.date_input(
        "Start Date",
        value=default_start,
        min_value=min_date,
        max_value=max_date,
        key="perf_start",
    )
with col3:
    end_dt = st.date_input(
        "End Date",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
        key="perf_end",
    )
with col4:
    available_years_perf = sorted(prices["date"].dt.year.unique(), reverse=True)
    perf_year = st.selectbox(
        "Quick Year",
        ["Custom"] + [str(y) for y in available_years_perf],
        index=0,
        key="perf_year",
    )

start_dt = pd.Timestamp(start_dt)
end_dt = pd.Timestamp(end_dt)

# Override dates if a specific year is selected
if perf_year != "Custom":
    yr = int(perf_year)
    start_dt = pd.Timestamp(f"{yr}-01-01")
    end_dt = pd.Timestamp(f"{yr}-12-31")

# Compute returns for all companies
perf_results = []
for t in tickers:
    tp = prices[
        (prices["ticker"] == t)
        & (prices["date"] >= start_dt)
        & (prices["date"] <= end_dt)
    ]
    if len(tp) < 2:
        continue
    sp, ep = get_price_range(tp["price"])
    if sp is None:
        continue
    ret = (ep - sp) / sp * 100
    perf_results.append(
        {"Ticker": t, "Start Price": sp, "End Price": ep, "Change": round(ep - sp, 2), "Return %": round(ret, 2)}
    )

perf_df = (
    pd.DataFrame(perf_results)
    .sort_values("Return %", ascending=False)
    .reset_index(drop=True)
)
perf_df["Rank"] = range(1, len(perf_df) + 1)
perf_df = perf_df[["Rank", "Ticker", "Start Price", "End Price", "Change", "Return %"]]

# LuSE Index return
idx_perf = index_df[
    (index_df["date"] >= start_dt) & (index_df["date"] <= end_dt)
]
idx_ret = None
if len(idx_perf) >= 2:
    idx_sp, idx_ep = get_price_range(idx_perf["price"])
    if idx_sp:
        idx_ret = (idx_ep - idx_sp) / idx_sp * 100

# Selected company return
sel_ret = None
if perf_company == "LuSE Index":
    sel_ret = idx_ret
else:
    sp = prices[
        (prices["ticker"] == perf_company)
        & (prices["date"] >= start_dt)
        & (prices["date"] <= end_dt)
    ]
    if len(sp) >= 2:
        sel_start, sel_end = get_price_range(sp["price"])
        sel_ret = (sel_end - sel_start) / sel_start * 100

avg_ret = perf_df["Return %"].mean() if len(perf_df) > 0 else None

# Summary cards
mcol1, mcol2, mcol3, mcol4 = st.columns(4)
with mcol1:
    rc = color_for_change(sel_ret)
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-label">{perf_company}</div>
        <div class="metric-value {rc}">{fmt_pct(sel_ret)}</div>
    </div>""",
        unsafe_allow_html=True,
    )
with mcol2:
    rc2 = color_for_change(idx_ret)
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-label">LuSE Index</div>
        <div class="metric-value {rc2}">{fmt_pct(idx_ret)}</div>
    </div>""",
        unsafe_allow_html=True,
    )
with mcol3:
    rc3 = color_for_change(avg_ret)
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-label">Avg Company Return</div>
        <div class="metric-value {rc3}">{fmt_pct(avg_ret)}</div>
    </div>""",
        unsafe_allow_html=True,
    )
with mcol4:
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-label">Companies Ranked</div>
        <div class="metric-value blue">{len(perf_df)}</div>
    </div>""",
        unsafe_allow_html=True,
    )

# Spacer after metric cards
st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

# Chart: selected vs index
chart_col, table_col = st.columns([1.6, 1])
with chart_col:
    fig = go.Figure()
    if perf_company == "LuSE Index":
        plot_df = idx_perf.copy()
        if len(plot_df) > 0:
            base = plot_df["price"].iloc[0]
            plot_df["normalized"] = plot_df["price"] / base * 100
            fig.add_trace(
                go.Scatter(
                    x=plot_df["date"],
                    y=plot_df["normalized"],
                    mode="lines",
                    name="LuSE Index",
                    line=dict(color="#6ea8ff", width=2),
                )
            )
    else:
        sp = prices[
            (prices["ticker"] == perf_company)
            & (prices["date"] >= start_dt)
            & (prices["date"] <= end_dt)
        ]
        if len(sp) > 0:
            base = sp["price"].iloc[0]
            sp = sp.copy()
            sp["normalized"] = sp["price"] / base * 100
            fig.add_trace(
                go.Scatter(
                    x=sp["date"],
                    y=sp["normalized"],
                    mode="lines",
                    name=perf_company,
                    line=dict(color="#74d99f", width=2),
                )
            )
        if len(idx_perf) > 0:
            idx_base = idx_perf["price"].iloc[0]
            idxp = idx_perf.copy()
            idxp["normalized"] = idxp["price"] / idx_base * 100
            fig.add_trace(
                go.Scatter(
                    x=idxp["date"],
                    y=idxp["normalized"],
                    mode="lines",
                    name="LuSE Index",
                    line=dict(color="#6ea8ff", width=1.5, dash="dot"),
                )
            )

    fig.update_layout(
        **build_plotly_layout(
            title="Normalized Performance (Base=100)", y_title="Normalized Value"
        ),
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)

with table_col:
    display_df = perf_df.copy()
    display_df["Change"] = display_df["Change"].apply(lambda x: f"K{x:+,.2f}")
    display_df["Return %"] = display_df["Return %"].apply(lambda x: f"{x:+.2f}%")
    display_df["Start Price"] = display_df["Start Price"].apply(
        lambda x: f"K{x:,.2f}"
    )
    display_df["End Price"] = display_df["End Price"].apply(lambda x: f"K{x:,.2f}")

    # Apply conditional coloring: green for positive, red for negative
    def color_change(val):
        if val.startswith("K+"):
            return "color: #74d99f"
        elif val.startswith("K-"):
            return "color: #ff8b8b"
        return ""

    def color_pct(val):
        if val.startswith("+"):
            return "color: #74d99f"
        elif val.startswith("-"):
            return "color: #ff8b8b"
        return ""

    styled_df = display_df.style.map(color_change, subset=["Change"]).map(color_pct, subset=["Return %"])

    st.markdown(
        '<div style="font-size:11px;color:#9aa8b5;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">All Companies by Return</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(styled_df, hide_index=True, width="stretch", height=450)

# Interpretation
if sel_ret is not None and idx_ret is not None and avg_ret is not None:
    vs_index = sel_ret - idx_ret
    vs_avg = sel_ret - avg_ret
    rank_pos = perf_df[
        perf_df["Ticker"]
        == (perf_company if perf_company != "LuSE Index" else "")
    ].index
    rank_text = ""
    if len(rank_pos) > 0:
        rank_text = (
            f"ranked <strong>#{rank_pos[0] + 1}</strong> of {len(perf_df)} companies"
        )

    sel_color = color_for_change(sel_ret) if color_for_change(sel_ret) else "amber"
    interp_parts = [
        f'Over the selected period, <strong>{perf_company}</strong> returned <span class="highlight-{sel_color}">{fmt_pct(sel_ret)}</span>',
    ]
    if rank_text:
        interp_parts.append(f"({rank_text})")
    interp_parts.append(".")
    if vs_index > 0:
        interp_parts.append(
            f'This <span class="highlight-green">outperformed</span> the LuSE Index by <span class="highlight-green">{fmt_pct(vs_index)}</span>.'
        )
    else:
        interp_parts.append(
            f'This <span class="highlight-red">underperformed</span> the LuSE Index by <span class="highlight-red">{fmt_pct(abs(vs_index))}</span>.'
        )
    if vs_avg > 0:
        interp_parts.append(
            f'It also <span class="highlight-green">exceeded</span> the average company return by <span class="highlight-green">{fmt_pct(vs_avg)}</span>.'
        )
    else:
        interp_parts.append(
            f'It <span class="highlight-red">trailed</span> the average company return by <span class="highlight-red">{fmt_pct(abs(vs_avg))}</span>.'
        )

    st.markdown(
        f'<div class="interpretation-box">{" ".join(interp_parts)}</div>',
        unsafe_allow_html=True,
    )

with st.expander("How to read this section"):
    st.markdown(
        """
    <div class="interpretation-box" style="margin-top:0;">
        <strong>Historical Performance</strong> shows how each company's stock price has changed over a selected period.
        <br><br>
        • <strong>Select Asset</strong> — Choose a company or the LuSE Index to compare.
        <br>
        • <strong>Start Date / End Date</strong> — Pick a custom date range for the analysis period.
        <br>
        • <strong>Quick Year</strong> — Select a specific year to instantly view full-year performance (Jan 1 – Dec 31). Choose "Custom" to return to manual date selection.
        <br>
        • The <strong>chart</strong> normalizes prices to a base of 100, so you can see percentage growth/decline regardless of absolute price.
        <br>
        • The <strong>table</strong> ranks all companies by total return over the period. Scroll to see all entries.
        <br>
        • The <strong>interpretation box</strong> below the chart explains how the selected asset performed vs the index and average.
        <br><br>
        <strong>Key:</strong> <span class="highlight-green">Green</span> = positive return, <span class="highlight-red">Red</span> = negative return.
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SECTION 2: PERIOD RETURN HEATMAP
# ══════════════════════════════════════════════
st.markdown(
    """
<div class="section-card">
    <h2 class="section-title">2. Period Return Heatmap</h2>
    <p class="section-subtitle">Annual, half-year, quarterly, and monthly returns for a selected company.</p>
""",
    unsafe_allow_html=True,
)

# Year selector — side by side with company selector
hm_sel_col1, hm_sel_col2 = st.columns(2)
with hm_sel_col1:
    hm_company = st.selectbox("Select Company", tickers, index=0, key="hm_company")
with hm_sel_col2:
    available_years_hm = sorted(prices["date"].dt.year.unique(), reverse=True)
    hm_year = st.selectbox("Select Year", available_years_hm, index=0, key="hm_year")

# Compute all period returns for the selected company
hm_data = prices[prices["ticker"] == hm_company].copy()
hm_data = hm_data.set_index("date")

hm_data["year"] = hm_data.index.year
annual_returns = {}
for yr, grp in hm_data.groupby("year"):
    r = compute_return(grp["price"])
    if r is not None:
        annual_returns[yr] = round(r, 2)

hm_data["half"] = pd.Series(hm_data.index.month).apply(lambda m: "H1" if m <= 6 else "H2").values
half_returns = {}
for (yr, half), grp in hm_data.groupby(["year", "half"]):
    r = compute_return(grp["price"])
    if r is not None:
        half_returns[f"{yr} {half}"] = round(r, 2)

hm_data["quarter"] = hm_data.index.quarter
qtr_returns = {}
for (yr, qtr), grp in hm_data.groupby(["year", "quarter"]):
    r = compute_return(grp["price"])
    if r is not None:
        qtr_returns[f"{yr} Q{qtr}"] = round(r, 2)

hm_data["month"] = hm_data.index.month
month_returns = {}
for (yr, mo), grp in hm_data.groupby(["year", "month"]):
    r = compute_return(grp["price"])
    if r is not None:
        month_returns[f"{yr}-{mo:02d}"] = round(r, 2)

# ── Two-column layout: Heatmap (left) | Simulation (right) ──
hm_left, hm_right = st.columns([1.6, 1])

with hm_left:
    st.markdown(
        '<div style="font-size:11px;color:#9aa8b5;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">Period Returns</div>',
        unsafe_allow_html=True,
    )

    # ── Row 1: Annual Card (full width) ──
    ann_val = annual_returns.get(hm_year)
    if ann_val is not None:
        ann_color = "green" if ann_val > 0 else ("red" if ann_val < 0 else "zero")
        st.markdown(
            f"""
    <div class="period-card full-year selected" style="margin-bottom:8px;">
        <div class="period-label">Full Year {hm_year}</div>
        <div class="period-return {ann_color}">{fmt_pct(ann_val)}</div>
        <div class="period-sub">Annual return</div>
    </div>""",
            unsafe_allow_html=True,
        )

    # ── Row 2: Half-Year Cards (2 columns, single HTML block) ──
    h1_val = half_returns.get(f"{hm_year} H1")
    h2_val = half_returns.get(f"{hm_year} H2")
    h1c = "green" if h1_val is not None and h1_val > 0 else ("red" if h1_val is not None and h1_val < 0 else "zero")
    h2c = "green" if h2_val is not None and h2_val > 0 else ("red" if h2_val is not None and h2_val < 0 else "zero")
    h1_display = fmt_pct(h1_val) if h1_val is not None else "—"
    h2_display = fmt_pct(h2_val) if h2_val is not None else "—"
    st.markdown(
        f"""
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:8px;">
        <div class="period-card half-year" style="margin:0;">
            <div class="period-label">H1 {hm_year}</div>
            <div class="period-return {h1c}">{h1_display}</div>
            <div class="period-sub">Jan - Jun</div>
        </div>
        <div class="period-card half-year" style="margin:0;">
            <div class="period-label">H2 {hm_year}</div>
            <div class="period-return {h2c}">{h2_display}</div>
            <div class="period-sub">Jul - Dec</div>
        </div>
    </div>""",
        unsafe_allow_html=True,
    )

    # ── Row 3: Quarterly Cards (4 columns, single HTML block) ──
    q_cards = ""
    for i, qnum in enumerate([1, 2, 3, 4]):
        q_val = qtr_returns.get(f"{hm_year} Q{qnum}")
        qc = "green" if q_val is not None and q_val > 0 else ("red" if q_val is not None and q_val < 0 else "zero")
        q_display = fmt_pct(q_val) if q_val is not None else "—"
        q_cards += f"""
        <div class="period-card quarter" style="margin:0;">
            <div class="period-label">Q{qnum}</div>
            <div class="period-return {qc}">{q_display}</div>
            <div class="period-sub">{['Jan-Mar','Apr-Jun','Jul-Sep','Oct-Dec'][i]}</div>
        </div>"""
    st.markdown(
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px;">{q_cards}</div>',
        unsafe_allow_html=True,
    )

    # ── Row 4: Monthly Cards (12 columns, single HTML block) ──
    m_cards = ""
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for mi, mname in enumerate(month_names, start=1):
        m_val = month_returns.get(f"{hm_year}-{mi:02d}")
        mc = "green" if m_val is not None and m_val > 0 else ("red" if m_val is not None and m_val < 0 else "zero")
        m_display = fmt_pct(m_val) if m_val is not None else "—"
        m_cards += f"""
        <div class="period-card month" style="padding:6px 4px;">
            <div class="period-label" style="font-size:8px;">{mname}</div>
            <div class="period-return {mc}" style="font-size:11px;">{m_display}</div>
        </div>"""
    st.markdown(
        f'<div style="display:grid;grid-template-columns:repeat(12,1fr);gap:4px;margin-bottom:16px;">{m_cards}</div>',
        unsafe_allow_html=True,
    )

with hm_right:
    # ── Investment Simulation Panel ──
    st.markdown(
        '<div style="font-size:11px;color:#9aa8b5;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">Investment Simulation</div>',
        unsafe_allow_html=True,
    )

    # Investment amount input
    sim_amount = st.number_input(
        "Investment Amount (K)",
        min_value=1,
        max_value=10_000_000,
        value=1000,
        step=100,
        format="%d",
        key="sim_amount",
    )

    # Use annual return as default for simulation
    sim_return = annual_returns.get(hm_year)
    sim_label = f"Full Year {hm_year}"

    if sim_return is not None:
        final_value = sim_amount * (1 + sim_return / 100)
        gain = final_value - sim_amount
        gain_color = "green" if gain >= 0 else "red"
        st.markdown(
            f"""
        <div class="sim-panel">
            <div class="sim-title">K{sim_amount:,} invested in {hm_company}</div>
            <div class="sim-row">
                <span class="sim-label">Period</span>
                <span class="sim-value">{sim_label}</span>
            </div>
            <div class="sim-row">
                <span class="sim-label">Return</span>
                <span class="sim-value {gain_color}">{fmt_pct(sim_return)}</span>
            </div>
            <div class="sim-row">
                <span class="sim-label">Amount Invested</span>
                <span class="sim-value">K{sim_amount:,.2f}</span>
            </div>
            <div class="sim-big {gain_color}">K{final_value:,.2f}</div>
            <div class="sim-row" style="border-bottom:none;">
                <span class="sim-label">Gain / Loss</span>
                <span class="sim-value {gain_color}">{fmt_kwacha(gain)}</span>
            </div>
            <div class="sim-note">Based on annual return for {hm_year}</div>
        </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="sim-panel"><div class="sim-note">Insufficient data for {hm_year}.</div></div>',
            unsafe_allow_html=True,
        )

# Spacer after the heatmap + simulation columns
st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

with st.expander("How to read this section"):
    st.markdown(
        """
    <div class="interpretation-box" style="margin-top:0;">
        <strong>Period Return Heatmap</strong> breaks down a company's performance for a selected year into nested time periods.
        <br><br>
        • <strong>Select Company</strong> — Choose which company to analyze.
        <br>
        • <strong>Select Year</strong> — Pick a year to view its period breakdown.
        <br>
        • Cards are arranged by period length: <strong>Full Year</strong> (top, full width) → <strong>H1 & H2</strong> (side by side) → <strong>Q1-Q4</strong> (four in a row) → <strong>Jan-Dec</strong> (12 months).
        <br>
        • <span class="highlight-green">Green</span> = positive return, <span class="highlight-red">Red</span> = negative return.
        <br>
        • The <strong>Investment Simulation</strong> panel shows what K1,000 invested for the full year would be worth.
        <br><br>
        <strong>Tip:</strong> Compare H1 vs H2 to see which half of the year performed better, or check quarterly patterns.
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SECTION 3: PRICE MOVEMENT TORNADO
# ══════════════════════════════════════════════
st.markdown(
    """
<div class="section-card">
    <h2 class="section-title">3. Price Movement Tornado</h2>
    <p class="section-subtitle">Compare absolute price movement (Kwacha) versus percentage return for all companies in a selected year.</p>
""",
    unsafe_allow_html=True,
)

# Year selector
available_years = sorted(prices["date"].dt.year.unique(), reverse=True)
tornado_year = st.selectbox(
    "Select Year", available_years, index=0, key="tornado_year"
)

# Compute per-company for the selected year
tornado_data = []
for t in tickers:
    tp = prices[
        (prices["ticker"] == t)
        & (prices["date"].dt.year == tornado_year)
    ]
    if len(tp) < 2:
        continue
    sp, ep = get_price_range(tp["price"])
    if sp is None:
        continue
    kwacha_change = ep - sp
    pct_return = (ep - sp) / sp * 100
    tornado_data.append(
        {
            "Ticker": t,
            "Start Price": sp,
            "End Price": ep,
            "Kwacha Change": round(kwacha_change, 2),
            "Return %": round(pct_return, 2),
        }
    )

tornado_df = pd.DataFrame(tornado_data).sort_values(
    "Kwacha Change", ascending=False
).reset_index(drop=True)

if len(tornado_df) > 0:
    # Tornado chart: all bars radiate outward from center using abs() values
    fig = go.Figure()
    # Sort by kwacha change for display
    plot_df = tornado_df.sort_values("Kwacha Change", ascending=True)
    ticker_labels = plot_df["Ticker"].tolist()

    kwacha_vals = plot_df["Kwacha Change"].tolist()
    pct_vals = plot_df["Return %"].tolist()

    # Use absolute values so all bars extend right (outward) from center
    kwacha_abs = [abs(v) for v in kwacha_vals]
    pct_abs = [abs(v) for v in pct_vals]

    # Kwacha bars — start from center (right edge of left axis) and extend left
    # Using positive abs() values with autorange="reversed" so zero is at right (center)
    fig.add_trace(
        go.Bar(
            y=ticker_labels,
            x=kwacha_abs,
            name="Kwacha Change",
            orientation="h",
            marker=dict(
                color=["#74d99f" if v >= 0 else "#ff8b8b" for v in kwacha_vals],
                line=dict(color="#2a3441", width=0.5),
            ),
            hovertemplate="%{y}: K%{customdata:,.2f}<extra></extra>",
            customdata=kwacha_vals,
            xaxis="x",
            yaxis="y",
            showlegend=True,
        )
    )

    # % bars — all extend right from center, colored by sign
    fig.add_trace(
        go.Bar(
            y=ticker_labels,
            x=pct_abs,
            name="Return %",
            orientation="h",
            marker=dict(
                color=["#74d99f" if v >= 0 else "#ff8b8b" for v in pct_vals],
                line=dict(color="#2a3441", width=0.5),
            ),
            hovertemplate="%{y}: %{customdata:+.2f}%<extra></extra>",
            customdata=pct_vals,
            xaxis="x2",
            yaxis="y",
            showlegend=True,
        )
    )

    fig.update_layout(
        **build_plotly_layout(
            title=f"Price Movement Tornado — {tornado_year}",
            y_title="",
        ),
        barmode="group",
        xaxis=dict(
            title=dict(text="Kwacha Change", font=dict(size=11, color="#9aa8b5")),
            side="top",
            gridcolor="#2a3441",
            tickfont=dict(size=10, color="#9aa8b5"),
            domain=[0, 0.42],
            zeroline=True,
            zerolinecolor="#6a7a8a",
            zerolinewidth=1.5,
            autorange="reversed",
        ),
        xaxis2=dict(
            title=dict(text="Return %", font=dict(size=11, color="#9aa8b5")),
            side="top",
            gridcolor="#2a3441",
            tickfont=dict(size=10, color="#9aa8b5"),
            domain=[0.58, 1.0],
            anchor="y",
            zeroline=True,
            zerolinecolor="#6a7a8a",
            zerolinewidth=1.5,
            rangemode="nonnegative",
        ),
        yaxis=dict(
            tickfont=dict(size=11, color="#e6edf3"),
            gridcolor="#2a3441",
            domain=[0, 1],
            showticklabels=False,
        ),
        height=max(350, len(ticker_labels) * 28),
        margin=dict(l=10, r=10, t=50, b=60),
        showlegend=True,
        legend=dict(
            font=dict(size=11, color="#9aa8b5"),
            orientation="h",
            y=1.08,
            x=0.3,
        ),
    )

    # Add ticker labels in the center gap between the two axes
    for tkr in ticker_labels:
        fig.add_annotation(
            xref="paper",
            yref="y",
            x=0.5,
            y=tkr,
            text=tkr,
            showarrow=False,
            font=dict(size=11, color="#e6edf3", family="monospace", weight="bold"),
            xanchor="center",
            yanchor="middle",
        )

    # Add annotation about dual units
    fig.add_annotation(
        text="← Kwacha Change | Ticker → | Return % →",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.08,
        showarrow=False,
        font=dict(size=11, color="#9aa8b5"),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary cards
    top_gainer_k = tornado_df.loc[tornado_df["Kwacha Change"].idxmax()]
    top_loser_k = tornado_df.loc[tornado_df["Kwacha Change"].idxmin()]
    top_gainer_pct = tornado_df.loc[tornado_df["Return %"].idxmax()]
    top_loser_pct = tornado_df.loc[tornado_df["Return %"].idxmin()]

    tcol1, tcol2, tcol3, tcol4 = st.columns(4)
    with tcol1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Top Gainer (K)</div>
            <div class="metric-value green">{top_gainer_k['Ticker']} <span style="font-size:13px;font-weight:400;">{fmt_kwacha(top_gainer_k['Kwacha Change'])}</span></div>
        </div>""",
            unsafe_allow_html=True,
        )
    with tcol2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Top Loser (K)</div>
            <div class="metric-value red">{top_loser_k['Ticker']} <span style="font-size:13px;font-weight:400;">{fmt_kwacha(top_loser_k['Kwacha Change'])}</span></div>
        </div>""",
            unsafe_allow_html=True,
        )
    with tcol3:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Top Gainer (%)</div>
            <div class="metric-value green">{top_gainer_pct['Ticker']} <span style="font-size:13px;font-weight:400;">{fmt_pct(top_gainer_pct['Return %'])}</span></div>
        </div>""",
            unsafe_allow_html=True,
        )
    with tcol4:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Top Loser (%)</div>
            <div class="metric-value red">{top_loser_pct['Ticker']} <span style="font-size:13px;font-weight:400;">{fmt_pct(top_loser_pct['Return %'])}</span></div>
        </div>""",
            unsafe_allow_html=True,
        )

    # Spacer after metric cards
    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="data-note">Note: The two sides of the tornado chart use different units. Left shows absolute Kwacha change; right shows percentage return. This allows comparison of magnitude vs. relative performance.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="data-note">Insufficient data for the selected year.</div>',
        unsafe_allow_html=True,
    )

with st.expander("How to read this section"):
    st.markdown(
        """
    <div class="interpretation-box" style="margin-top:0;">
        <strong>Price Movement Tornado</strong> compares all companies side-by-side for a selected year.
        <br><br>
        • <strong>Select Year</strong> — Choose which year to analyze.
        <br>
        • The <strong>left side</strong> of the chart shows the absolute Kwacha change in price (start to end of year).
        <br>
        • The <strong>right side</strong> shows the percentage return for the same period.
        <br>
        • Companies are sorted by Kwacha change. Bars extending <span class="highlight-green">right (green)</span> = gain, <span class="highlight-red">left (red)</span> = loss.
        <br>
        • The <strong>summary cards</strong> highlight the top gainers and losers in both Kwacha and percentage terms.
        <br><br>
        <strong>Note:</strong> A company can be a top gainer in Kwacha but not in percentage (e.g., a high-priced stock moving slightly), and vice versa.
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SECTION 4: TRADING ACTIVITY VS PRICE MOVEMENT FLOW
# ══════════════════════════════════════════════
st.markdown(
    """
<div class="section-card">
    <h2 class="section-title">4. Trading Activity vs Price Movement Flow</h2>
    <p class="section-subtitle">Compare trading volume share against price movement share for each company in the selected year.</p>
""",
    unsafe_allow_html=True,
)

flow_year = st.selectbox(
    "Select Year", available_years, index=0, key="flow_year"
)

# Compute volume share and price movement share for Sankey
flow_data = []
for t in tickers:
    tp = prices[
        (prices["ticker"] == t)
        & (prices["date"].dt.year == flow_year)
    ]
    if len(tp) < 2:
        continue
    total_vol = tp["volume"].sum()
    if total_vol == 0 or pd.isna(total_vol):
        continue
    sp, ep = get_price_range(tp["price"])
    if sp is None:
        continue
    kwacha_movement = ep - sp
    return_pct = (ep - sp) / sp * 100
    flow_data.append(
        {
            "Ticker": t,
            "Total Volume": total_vol,
            "Kwacha Movement": round(kwacha_movement, 2),
            "Start Price": sp,
            "End Price": ep,
            "Return %": round(return_pct, 2),
        }
    )

flow_df = pd.DataFrame(flow_data)
if len(flow_df) > 0:
    total_vol_all = flow_df["Total Volume"].sum()
    total_abs_return_all = flow_df["Return %"].abs().sum()
    flow_df["Volume Share %"] = round(
        flow_df["Total Volume"] / total_vol_all * 100, 2
    )
    flow_df["Movement Share %"] = round(
        flow_df["Return %"].abs() / total_abs_return_all * 100, 2
    )

    # Sort by volume share descending
    flow_df = flow_df.sort_values("Volume Share %", ascending=False).reset_index(
        drop=True
    )

    # ── 3-Column Sankey Diagram ──
    # Left: Volume Buckets (High, Med, Low)
    # Middle: Company Tickers
    # Right: Movement Buckets (High/Med/Low Gain, High/Med/Low Loss)

    # Assign volume buckets (split into thirds by count)
    n = len(flow_df)
    vol_bucket_map = {}
    for i, tkr in enumerate(flow_df["Ticker"]):
        if i < n / 3:
            vol_bucket_map[tkr] = "High Volume"
        elif i < 2 * n / 3:
            vol_bucket_map[tkr] = "Med Volume"
        else:
            vol_bucket_map[tkr] = "Low Volume"

    # Assign movement buckets (split gainers and losers separately)
    gainers = flow_df[flow_df["Return %"] >= 0].sort_values("Movement Share %", ascending=False)
    losers = flow_df[flow_df["Return %"] < 0].sort_values("Movement Share %", ascending=False)
    mov_bucket_map = {}
    for i, (_, row) in enumerate(gainers.iterrows()):
        ng = len(gainers)
        if ng <= 2:
            mov_bucket_map[row["Ticker"]] = "High Gain" if i == 0 else "Low Gain"
        elif i < ng / 3:
            mov_bucket_map[row["Ticker"]] = "High Gain"
        elif i < 2 * ng / 3:
            mov_bucket_map[row["Ticker"]] = "Med Gain"
        else:
            mov_bucket_map[row["Ticker"]] = "Low Gain"
    for i, (_, row) in enumerate(losers.iterrows()):
        nl = len(losers)
        if nl <= 2:
            mov_bucket_map[row["Ticker"]] = "High Loss" if i == 0 else "Low Loss"
        elif i < nl / 3:
            mov_bucket_map[row["Ticker"]] = "High Loss"
        elif i < 2 * nl / 3:
            mov_bucket_map[row["Ticker"]] = "Med Loss"
        else:
            mov_bucket_map[row["Ticker"]] = "Low Loss"

    # Build node lists (3 columns)
    vol_buckets_ordered = ["High Volume", "Med Volume", "Low Volume"]
    mov_buckets_ordered = ["High Gain", "Med Gain", "Low Gain", "High Loss", "Med Loss", "Low Loss"]
    tickers_ordered = flow_df["Ticker"].tolist()

    # Node labels and colors
    node_labels = []
    node_colors = []

    # Column 0: Volume buckets
    vol_node_indices = {}
    for b in vol_buckets_ordered:
        vol_node_indices[b] = len(node_labels)
        node_labels.append(b)
        node_colors.append("#6ea8ff")

    # Column 1: Company tickers
    ticker_node_indices = {}
    for tkr in tickers_ordered:
        ticker_node_indices[tkr] = len(node_labels)
        node_labels.append(tkr)
        # Color by return sign
        row = flow_df[flow_df["Ticker"] == tkr].iloc[0]
        if row["Return %"] >= 0:
            node_colors.append("#74d99f")
        else:
            node_colors.append("#ff8b8b")

    # Column 2: Movement buckets
    mov_node_indices = {}
    for b in mov_buckets_ordered:
        mov_node_indices[b] = len(node_labels)
        node_labels.append(b)
        if "Gain" in b:
            node_colors.append("#74d99f")
        else:
            node_colors.append("#ff8b8b")

    # Build links
    source_indices = []
    target_indices = []
    link_values = []
    link_colors = []

    # Links: Volume Bucket → Ticker
    for tkr in tickers_ordered:
        row = flow_df[flow_df["Ticker"] == tkr].iloc[0]
        bucket = vol_bucket_map[tkr]
        src = vol_node_indices[bucket]
        tgt = ticker_node_indices[tkr]
        val = max(row["Volume Share %"], 0.1)
        source_indices.append(src)
        target_indices.append(tgt)
        link_values.append(val)
        link_colors.append("rgba(110, 168, 255, 0.3)")

    # Links: Ticker → Movement Bucket
    for tkr in tickers_ordered:
        row = flow_df[flow_df["Ticker"] == tkr].iloc[0]
        bucket = mov_bucket_map[tkr]
        src = ticker_node_indices[tkr]
        tgt = mov_node_indices[bucket]
        val = max(row["Movement Share %"], 0.1)
        source_indices.append(src)
        target_indices.append(tgt)
        link_values.append(val)
        if row["Return %"] >= 0:
            link_colors.append("rgba(116, 217, 159, 0.3)")
        else:
            link_colors.append("rgba(255, 139, 139, 0.3)")

    fig = go.Figure(data=[
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="#2a3441", width=1),
                label=node_labels,
                color=node_colors,
                hovertemplate="%{label}<br>Value: %{value:.1f}%<extra></extra>",
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=link_values,
                color=link_colors,
                hovertemplate="%{source.label} → %{target.label}<br>Flow: %{value:.1f}%<extra></extra>",
            ),
        )
    ])

    fig.update_layout(
        **build_plotly_layout(
            title=f"Volume → Price Movement Flow — {flow_year}",
            y_title="",
        ),
        height=max(400, len(flow_df) * 35),
        margin=dict(l=80, r=80, t=50, b=30),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary cards
    top_vol = flow_df.loc[flow_df["Volume Share %"].idxmax()]
    top_mov = flow_df.loc[flow_df["Movement Share %"].idxmax()]
    highest_gain = flow_df.loc[flow_df["Return %"].idxmax()]
    largest_loss = flow_df.loc[flow_df["Return %"].idxmin()]

    fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)
    with fcol1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Top Volume Share</div>
            <div class="metric-value blue">{top_vol['Ticker']} <span style="font-size:13px;font-weight:400;">{top_vol['Volume Share %']:.1f}%</span></div>
        </div>""",
            unsafe_allow_html=True,
        )
    with fcol2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Top Movement Share</div>
            <div class="metric-value blue">{top_mov['Ticker']} <span style="font-size:13px;font-weight:400;">{top_mov['Movement Share %']:.1f}%</span></div>
        </div>""",
            unsafe_allow_html=True,
        )
    with fcol3:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Highest Gain</div>
            <div class="metric-value green">{highest_gain['Ticker']} <span style="font-size:13px;font-weight:400;">{fmt_pct(highest_gain['Return %'])}</span></div>
        </div>""",
            unsafe_allow_html=True,
        )
    with fcol4:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Largest Loss</div>
            <div class="metric-value red">{largest_loss['Ticker']} <span style="font-size:13px;font-weight:400;">{fmt_pct(largest_loss['Return %'])}</span></div>
        </div>""",
            unsafe_allow_html=True,
        )
    with fcol5:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Companies</div>
            <div class="metric-value blue">{len(flow_df)}</div>
        </div>""",
            unsafe_allow_html=True,
        )

    # Spacer after metric cards
    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="interpretation-box">This <strong>Sankey diagram</strong> shows how trading volume concentration flows through companies to price movement concentration. <strong>Left (blue):</strong> Volume buckets — companies are split into High, Med, Low volume tiers. <strong>Middle:</strong> Company tickers (<span class="highlight-green">green</span> = positive return, <span class="highlight-red">red</span> = negative). <strong>Right:</strong> Movement buckets — companies are grouped by their share of total absolute price movement into gain/loss tiers. The thickness of each flow represents the relative share. This is a <strong>relative comparison</strong> — it shows concentration patterns, not cause-and-effect.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="data-note">Insufficient data for the selected year.</div>',
        unsafe_allow_html=True,
    )

with st.expander("How to read this section"):
    st.markdown(
        """
    <div class="interpretation-box" style="margin-top:0;">
        <strong>Trading Activity vs Price Movement Flow</strong> uses a 3-column Sankey diagram to show how trading volume concentration maps to price movement concentration.
        <br><br>
        • <strong>Select Year</strong> — Choose which year to analyze.
        <br>
        • <strong>Left column (blue nodes)</strong> — Volume buckets: companies are split into <strong>High Volume</strong>, <strong>Med Volume</strong>, and <strong>Low Volume</strong> tiers (by count, sorted by volume share).
        <br>
        • <strong>Middle column</strong> — Company tickers. <span class="highlight-green">Green</span> = positive return, <span class="highlight-red">Red</span> = negative return.
        <br>
        • <strong>Right column</strong> — Movement buckets: companies are grouped by their share of total absolute price movement into <strong>High/Med/Low Gain</strong> and <strong>High/Med/Low Loss</strong> tiers.
        <br>
        • <strong>Flows</strong> — Left → Middle: volume share flows from bucket to ticker. Middle → Right: movement share flows from ticker to movement bucket. Thicker = larger share.
        <br>
        • The <strong>summary cards</strong> show the top company in each category.
        <br><br>
        <strong>Key insight:</strong> A company in the High Volume bucket but Low Gain/Loss bucket suggests high trading activity but price stability. A company in the Low Volume bucket but High Gain/Loss bucket suggests a volatile stock with less trading activity.
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SECTION 5: DATA COVERAGE & QUALITY
# ══════════════════════════════════════════════
st.markdown(
    """
<div class="section-card">
    <h2 class="section-title">5. Data Coverage & Quality</h2>
    <p class="section-subtitle">Historical coverage and completeness for each company and the LuSE Index.</p>
""",
    unsafe_allow_html=True,
)

# Compute coverage stats
coverage_data = []
for t in tickers:
    tp = prices[prices["ticker"] == t].sort_values("date")
    if len(tp) == 0:
        continue
    start = tp["date"].min()
    end = tp["date"].max()
    obs = len(tp)
    coverage_days = (end - start).days
    # Coverage quality: based on observation density
    expected_days = coverage_days
    density = obs / max(expected_days, 1) * 100 if expected_days > 0 else 0
    if density >= 60:
        quality = "Good"
        qclass = "good"
    elif density >= 30:
        quality = "Moderate"
        qclass = "warn"
    else:
        quality = "Weak"
        qclass = "bad"

    coverage_data.append(
        {
            "Ticker": t,
            "Start": start,
            "End": end,
            "Observations": obs,
            "Coverage Days": coverage_days,
            "Density %": round(density, 1),
            "Quality": quality,
            "qclass": qclass,
        }
    )

cov_df = pd.DataFrame(coverage_data).sort_values("Start")

# Coverage timeline chart
fig = go.Figure()
for _, row in cov_df.iterrows():
    color_map = {"Good": "#74d99f", "Moderate": "#f0b86a", "Weak": "#ff8b8b"}
    bar_color = color_map.get(row["Quality"], "#6ea8ff")
    fig.add_trace(
        go.Bar(
            y=[row["Ticker"]],
            x=[row["Coverage Days"]],
            name=row["Ticker"],
            orientation="h",
            marker=dict(color=bar_color, line=dict(color="#2a3441", width=0.5)),
            hovertemplate=(
                f"<b>{row['Ticker']}</b><br>"
                f"Start: {row['Start'].strftime('%d %b %Y')}<br>"
                f"End: {row['End'].strftime('%d %b %Y')}<br>"
                f"Observations: {row['Observations']:,}<br>"
                f"Density: {row['Density %']}%<br>"
                f"Quality: {row['Quality']}<br>"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )

fig.update_layout(
    **build_plotly_layout(
        title="Data Coverage Timeline (Coverage Days)",
        y_title="",
    ),
    xaxis=dict(
        title=dict(text="Coverage Days", font=dict(size=11, color="#9aa8b5")),
        gridcolor="#2a3441",
        tickfont=dict(size=10, color="#9aa8b5"),
    ),
    yaxis=dict(
        tickfont=dict(size=11, color="#e6edf3"),
        gridcolor="#2a3441",
        categoryorder="total ascending",
    ),
    height=max(300, len(cov_df) * 28),
    margin=dict(l=10, r=20, t=40, b=40),
    bargap=0.3,
)

st.plotly_chart(fig, use_container_width=True)

# Summary cards
earliest_start = cov_df["Start"].min()
latest_end = cov_df["End"].max()
longest_cov = cov_df.loc[cov_df["Coverage Days"].idxmax()]
weak_count = len(cov_df[cov_df["Quality"] == "Weak"])

ccol1, ccol2, ccol3, ccol4, ccol5 = st.columns(5)
with ccol1:
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-label">Companies</div>
        <div class="metric-value blue">{len(cov_df)}</div>
    </div>""",
        unsafe_allow_html=True,
    )
with ccol2:
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-label">Earliest Coverage</div>
        <div class="metric-value" style="font-size:13px;">{earliest_start.strftime('%d %b %Y')}</div>
    </div>""",
        unsafe_allow_html=True,
    )
with ccol3:
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-label">Latest Coverage</div>
        <div class="metric-value" style="font-size:13px;">{latest_end.strftime('%d %b %Y')}</div>
    </div>""",
        unsafe_allow_html=True,
    )
with ccol4:
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-label">Longest Coverage</div>
        <div class="metric-value green">{longest_cov['Ticker']} <span style="font-size:13px;font-weight:400;">{longest_cov['Coverage Days']} days</span></div>
    </div>""",
        unsafe_allow_html=True,
    )
    with ccol5:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Weak Coverage</div>
            <div class="metric-value {'amber' if weak_count > 0 else 'green'}">{weak_count} company{'ies' if weak_count != 1 else 'y'}</div>
        </div>""",
            unsafe_allow_html=True,
        )

    # Spacer after metric cards
    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # Quality breakdown table
    st.markdown(
        '<div style="font-size:11px;color:#9aa8b5;text-transform:uppercase;letter-spacing:0.5px;margin:14px 0 6px;">Coverage Details</div>',
    unsafe_allow_html=True,
)
display_cov = cov_df.copy()
display_cov["Start"] = display_cov["Start"].dt.strftime("%d %b %Y")
display_cov["End"] = display_cov["End"].dt.strftime("%d %b %Y")
display_cov["Observations"] = display_cov["Observations"].apply(
    lambda x: f"{x:,}"
)
display_cov["Coverage Days"] = display_cov["Coverage Days"].apply(
    lambda x: f"{x:,}"
)
display_cov["Density %"] = display_cov["Density %"].apply(lambda x: f"{x:.1f}%")

# Add quality badges
def make_badge(q, qc):
    return f'<span class="status-badge {qc}"><span class="dot"></span>{q}</span>'

display_cov["Quality Badge"] = display_cov.apply(
    lambda r: make_badge(r["Quality"], r["qclass"]), axis=1
)
display_cov = display_cov[
    ["Ticker", "Start", "End", "Observations", "Coverage Days", "Density %", "Quality Badge"]
]

st.markdown(display_cov.to_html(escape=False, index=False), unsafe_allow_html=True)

st.markdown(
    '<div class="data-note">Coverage length does not always mean completeness. A company may have data spanning many years but with sparse observations (low density). The quality rating considers both the time span and the observation density.</div>',
    unsafe_allow_html=True,
)

with st.expander("How to read this section"):
    st.markdown(
        """
    <div class="interpretation-box" style="margin-top:0;">
        <strong>Data Coverage & Quality</strong> shows how much historical data is available for each company.
        <br><br>
        • The <strong>coverage timeline</strong> chart shows each company's data span as a horizontal bar. <span class="highlight-green">Green</span> = good density, <span class="highlight-amber">Amber</span> = moderate, <span class="highlight-red">Red</span> = weak.
        <br>
        • <strong>Coverage Days</strong> = the total time span from first to last observation.
        <br>
        • <strong>Density %</strong> = what fraction of those days have actual price observations. A company with 10 years of data but only 20% density has many gaps.
        <br>
        • The <strong>quality rating</strong> combines both time span and density:
        <br>
        &nbsp;&nbsp;• <span class="status-badge good"><span class="dot"></span>Good</span> = 60%+ density
        <br>
        &nbsp;&nbsp;• <span class="status-badge warn"><span class="dot"></span>Moderate</span> = 30-60% density
        <br>
        &nbsp;&nbsp;• <span class="status-badge bad"><span class="dot"></span>Weak</span> = below 30% density
        <br><br>
        <strong>Tip:</strong> Use this section to assess which companies have reliable data for analysis.
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# ABOUT THE ANALYST & FOOTER
# ──────────────────────────────────────────────
st.markdown(
    """
<div style="background:#151b23;border:1px solid #2a3441;padding:24px 22px;margin-bottom:18px;">
<div style="font-size:13px;color:#9aa8b5;margin-bottom:2px;">Built by <strong style="color:#e6edf3;">Richard Daka</strong> as a data analytics portfolio project.</div>
<div style="font-size:12px;color:#6ea8ff;margin-bottom:16px;font-style:italic;">Banking & Finance Professional | Data Analytics Portfolio Project</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 20px;margin-bottom:16px;">
<div style="display:flex;align-items:center;gap:8px;">
<span style="color:#74d99f;font-size:12px;">▸</span>
<span style="color:#9aa8b5;font-size:12px;">BSc Banking & Finance</span>
</div>
<div style="display:flex;align-items:center;gap:8px;">
<span style="color:#74d99f;font-size:12px;">▸</span>
<span style="color:#9aa8b5;font-size:12px;">MBA Finance</span>
</div>
<div style="display:flex;align-items:center;gap:8px;">
<span style="color:#74d99f;font-size:12px;">▸</span>
<span style="color:#9aa8b5;font-size:12px;">Google Data Analytics Professional Certificate</span>
</div>
<div style="display:flex;align-items:center;gap:8px;">
<span style="color:#74d99f;font-size:12px;">▸</span>
<span style="color:#9aa8b5;font-size:12px;">10 Years Banking Industry Experience</span>
</div>
<div style="display:flex;align-items:center;gap:8px;grid-column:1 / -1;">
<span style="color:#74d99f;font-size:12px;">▸</span>
<span style="color:#9aa8b5;font-size:12px;">Developer of the Kakuleta Application</span>
</div>
</div>

<div style="font-size:12px;color:#6a7a8a;line-height:1.7;margin-bottom:16px;padding:12px 14px;background:#111820;border-left:3px solid #2a3441;">
This dashboard analyses Zambia's capital markets using LuSE company prices, index data, trading activity, and macroeconomic indicators. It was created to demonstrate practical skills in financial data analysis, data cleaning, visualization, dashboard development, and market storytelling.
</div>

<div style="display:flex;flex-wrap:wrap;gap:6px;">
<span style="display:inline-block;padding:3px 10px;font-size:11px;font-weight:600;color:#6ea8ff;background:#0a1a33;border:1px solid #1f4a8a;">Python</span>
<span style="display:inline-block;padding:3px 10px;font-size:11px;font-weight:600;color:#74d99f;background:#102219;border:1px solid #26734c;">Pandas</span>
<span style="display:inline-block;padding:3px 10px;font-size:11px;font-weight:600;color:#ff8b8b;background:#2a1212;border:1px solid #7a2f2f;">Streamlit</span>
<span style="display:inline-block;padding:3px 10px;font-size:11px;font-weight:600;color:#f0b86a;background:#1f1a0e;border:1px solid #7a5f1a;">Plotly</span>
<span style="display:inline-block;padding:3px 10px;font-size:11px;font-weight:600;color:#6ea8ff;background:#0a1a33;border:1px solid #1f4a8a;">SQL/Supabase</span>
<span style="display:inline-block;padding:3px 10px;font-size:11px;font-weight:600;color:#9aa8b5;background:#111820;border:1px solid #2a3441;">Financial Data Analysis</span>
</div>
</div>

<div style="text-align:center;padding:10px 0 10px;font-size:12px;color:#2a3441;">
LuSE Portfolio Analytics Dashboard &mdash; Data sourced from LuSE & Zambian Capital Markets Analysis
</div>
""",
    unsafe_allow_html=True,
)

