import streamlit as st
import json
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import io
import sys

# ─────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit command)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CDN Logs Dashboard · EPL Edition",
    layout="wide",
    page_icon="⚽"
)

# ─────────────────────────────────────────────
# EPL COLOUR PALETTE
# ─────────────────────────────────────────────
EPL_PURPLE   = "#37003C"   # EPL dark purple
EPL_PINK     = "#FF2882"   # EPL vibrant pink/magenta
EPL_TEAL     = "#00FF85"   # EPL neon green/teal
EPL_LIGHT    = "#F8F8F8"
EPL_CARD     = "#FFFFFF"
EPL_TEXT     = "#1A1A2E"
EPL_SUBTEXT  = "#555577"
EPL_GOLD     = "#FFD700"

# Plotly colour sequences derived from the EPL brand
EPL_SEQ   = [EPL_PINK, "#C300FF", "#FF6B35", EPL_TEAL, "#00BFFF", "#FF2882", "#9B59B6"]
EPL_SCALE = [[0.0, EPL_PURPLE], [0.5, EPL_PINK], [1.0, EPL_TEAL]]

# ─────────────────────────────────────────────
# GLOBAL CSS  – EPL theme
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Root & Background ── */
html, body, [data-testid="stAppViewContainer"] {{
    background: {EPL_PURPLE} !important;
    color: {EPL_LIGHT} !important;
    font-family: 'Segoe UI', sans-serif;
}}

[data-testid="stHeader"] {{
    background: {EPL_PURPLE} !important;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] > div:first-child {{
    background: linear-gradient(180deg, #2a0030 0%, #1a001f 100%) !important;
    border-right: 2px solid {EPL_PINK};
}}
[data-testid="stSidebar"] * {{
    color: {EPL_LIGHT} !important;
}}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] h1, h2, h3 {{
    color: {EPL_TEAL} !important;
}}

/* ── Block Container ── */
.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}}

/* ── Metric cards ── */
[data-testid="stMetricValue"] {{
    color: {EPL_TEAL} !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricLabel"] {{
    color: {EPL_PINK} !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    font-size: 0.7rem !important;
    letter-spacing: 1px;
}}
[data-testid="metric-container"] {{
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,40,130,0.3);
    border-radius: 14px;
    padding: 1rem !important;
    box-shadow: 0 4px 20px rgba(255,40,130,0.15);
}}
[data-testid="stMetricDelta"] {{
    color: {EPL_TEAL} !important;
}}

/* ── Buttons ── */
.stButton > button {{
    background: linear-gradient(135deg, {EPL_PINK} 0%, #C300FF 100%);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 0.5rem 1.5rem;
    box-shadow: 0 4px 15px rgba(255,40,130,0.4);
    transition: all 0.2s ease;
}}
.stButton > button:hover {{
    background: linear-gradient(135deg, #C300FF 0%, {EPL_PINK} 100%);
    box-shadow: 0 6px 20px rgba(195,0,255,0.5);
    transform: translateY(-1px);
}}

/* ── Inputs / Selects ── */
.stTextInput > div > input, .stSelectbox > div {{
    background: rgba(255,255,255,0.07) !important;
    color: {EPL_LIGHT} !important;
    border: 1px solid rgba(255,40,130,0.4) !important;
    border-radius: 10px !important;
}}
.stTextInput > div > input:focus {{
    border-color: {EPL_TEAL} !important;
    box-shadow: 0 0 0 2px rgba(0,255,133,0.3) !important;
}}

/* ── Expander ── */
details summary {{
    color: {EPL_TEAL} !important;
    font-weight: 600;
}}
/* Expander arrow icon */
details summary svg {{
    fill: {EPL_PINK} !important;
    stroke: {EPL_PINK} !important;
    opacity: 1 !important;
}}
[data-testid="stSidebar"] details summary {{
    background: rgba(255,40,130,0.08);
    border: 1px solid rgba(255,40,130,0.3);
    border-radius: 8px;
    padding: 0.4rem 0.6rem;
}}
[data-testid="stSidebar"] details summary svg {{
    fill: {EPL_TEAL} !important;
    stroke: {EPL_TEAL} !important;
}}

/* ── File uploader — fix white button & text ── */
[data-testid="stFileUploader"] {{
    border: 2px dashed rgba(255,40,130,0.4) !important;
    border-radius: 12px !important;
    background: rgba(255,255,255,0.03) !important;
}}
[data-testid="stFileUploader"] button {{
    background: linear-gradient(135deg, {EPL_PINK} 0%, #C300FF 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}
[data-testid="stFileUploader"] button:hover {{
    background: linear-gradient(135deg, #C300FF 0%, {EPL_PINK} 100%) !important;
}}
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small {{
    color: {EPL_LIGHT} !important;
}}

/* ── Sidebar selectbox & multiselect — fix dropdown text visibility ── */
[data-testid="stSidebar"] [data-baseweb="select"] {{
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,40,130,0.4) !important;
    border-radius: 8px !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] * {{
    background: #2a0030 !important;
    color: {EPL_LIGHT} !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"] {{
    background: rgba(255,40,130,0.25) !important;
    border: 1px solid {EPL_PINK} !important;
    border-radius: 20px !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"] span {{
    color: {EPL_LIGHT} !important;
}}
/* Dropdown menu list */
[data-baseweb="popover"] [data-baseweb="menu"] {{
    background: #2a0030 !important;
    border: 1px solid rgba(255,40,130,0.4) !important;
    border-radius: 10px !important;
}}
[data-baseweb="popover"] [role="option"] {{
    background: #2a0030 !important;
    color: {EPL_LIGHT} !important;
}}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [aria-selected="true"] {{
    background: rgba(255,40,130,0.2) !important;
    color: {EPL_TEAL} !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border: 1px solid rgba(255,40,130,0.3);
    border-radius: 12px;
    overflow: hidden;
}}

/* ── Divider ── */
hr {{
    border-color: rgba(255,40,130,0.2) !important;
    margin: 1.5rem 0 !important;
}}

/* ── Info / Success / Error boxes ── */
[data-testid="stAlert"] {{
    border-radius: 12px !important;
    border: none !important;
}}
[data-baseweb="notification"] {{
    background: rgba(0,255,133,0.1) !important;
    border-left: 4px solid {EPL_TEAL} !important;
    color: {EPL_LIGHT} !important;
    border-radius: 10px !important;
}}

/* ── Chat bubbles ── */
.bot-msg {{
    background: linear-gradient(135deg, rgba(255,40,130,0.15), rgba(195,0,255,0.10));
    border-left: 4px solid {EPL_PINK};
    border-radius: 0 14px 14px 14px;
    padding: 0.9rem 1.2rem;
    margin: 0.4rem 0 0.8rem 0;
    color: {EPL_LIGHT};
    font-size: 0.95rem;
    line-height: 1.6;
}}
.user-msg {{
    background: rgba(0,255,133,0.08);
    border-right: 4px solid {EPL_TEAL};
    border-radius: 14px 0 14px 14px;
    padding: 0.7rem 1.2rem;
    margin: 0.4rem 0 0.4rem 3rem;
    color: {EPL_LIGHT};
    font-size: 0.9rem;
    text-align: right;
}}

/* ── Subheaders ── */
h2, h3, .stSubheader {{
    color: {EPL_LIGHT} !important;
    border-bottom: 1px solid rgba(255,40,130,0.2);
    padding-bottom: 6px;
    margin-bottom: 0.8rem !important;
}}

/* ── Radio ── */
.stRadio > div {{ gap: 0.5rem; }}
.stRadio label {{ color: {EPL_LIGHT} !important; }}

/* ── File uploader ── */
[data-testid="stFileUploader"] {{
    border: 2px dashed rgba(255,40,130,0.4) !important;
    border-radius: 12px !important;
    background: rgba(255,255,255,0.03) !important;
}}

/* ── Section header badge ── */
.section-badge {{
    display: inline-block;
    background: linear-gradient(90deg, {EPL_PINK}, #C300FF);
    color: white;
    font-weight: 700;
    font-size: 0.75rem;
    letter-spacing: 1.5px;
    padding: 2px 12px;
    border-radius: 20px;
    text-transform: uppercase;
    margin-bottom: 8px;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PLOTLY CHART THEME  (applied to every figure)
# ─────────────────────────────────────────────
CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Segoe UI", color=EPL_LIGHT, size=12),
    legend=dict(
        bgcolor="rgba(255,255,255,0.05)",
        bordercolor=EPL_PINK,
        borderwidth=1,
        font=dict(color=EPL_LIGHT),
    ),
    hoverlabel=dict(
        bgcolor=EPL_PURPLE,
        font=dict(color=EPL_LIGHT, family="Segoe UI"),
        bordercolor=EPL_PINK,
    ),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.06)",
        zerolinecolor="rgba(255,255,255,0.1)",
        tickfont=dict(color=EPL_SUBTEXT),
        title=dict(font=dict(color=EPL_LIGHT)),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.06)",
        zerolinecolor="rgba(255,255,255,0.1)",
        tickfont=dict(color=EPL_SUBTEXT),
        title=dict(font=dict(color=EPL_LIGHT)),
    ),
    margin=dict(t=40, b=50, l=60, r=20),
    height=350,
)


def apply_theme(fig, **overrides):
    """Merge global chart layout + any per-chart overrides."""
    layout = {**CHART_LAYOUT, **overrides}
    fig.update_layout(**layout)
    return fig


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def load_logs():
    base_path = get_base_path()
    data_dir = base_path / "mock_data"
    logs = []
    for fname in ["cdn_logs_day1.json", "cdn_logs_day2.json", "cdn_logs_day3.json"]:
        file_path = data_dir / fname
        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            logs.extend(json.load(f))
    return pd.DataFrame(logs)


# ─────────────────────────────────────────────
# CHATBOT LOGIC
# ─────────────────────────────────────────────
def handle_question(q: str, filtered: pd.DataFrame) -> str:
    q = q.lower().strip()
    total = len(filtered)

    if not total:
        return "⚠️ No data matches the current filters. Please broaden your selection."

    # ── HELP ──
    if q in ("help", "?", "commands", "what can you do"):
        return (
            "⚽ **I can answer questions about your CDN logs. Try:**\n\n"
            "• `latency` · `average latency` · `p95 latency` · `latency variance`\n"
            "• `cache hit rate` · `cache miss %` · `cache summary`\n"
            "• `best datacenter` · `worst datacenter` · `datacenter performance`\n"
            "• `top isp` · `isp latency` · `isp performance`\n"
            "• `error rate` · `5xx errors` · `4xx errors` · `success rate`\n"
            "• `top city` · `slowest city` · `city performance`\n"
            "• `top backend` · `backend performance`\n"
            "• `average rtt` · `min rtt` · `max rtt`\n"
            "• `summary` · `overview`\n"
            "• `bandwidth` · `total response size`"
        )

    # ── SUMMARY / OVERVIEW ──
    if any(w in q for w in ["summary", "overview", "stats", "total", "dashboard"]):
        avg_lat = filtered['time_elapsed'].mean()
        hit_pct = (filtered['response_state'] == 'HIT').sum() / total * 100
        err_pct = (filtered['response_status'] >= 400).sum() / total * 100
        bandwidth_gb = filtered['response_body_size'].sum() / 1e9
        return (
            f"📊 **Dashboard Summary**\n\n"
            f"| Metric | Value |\n|---|---|\n"
            f"| Total Requests | **{total:,}** |\n"
            f"| Unique IPs | **{filtered['client_ip'].nunique():,}** |\n"
            f"| Cities Covered | **{filtered['geo_city'].nunique()}** |\n"
            f"| Datacenters | **{filtered['server_datacenter'].nunique()}** |\n"
            f"| Avg Latency | **{avg_lat:.3f}s** |\n"
            f"| Cache Hit Rate | **{hit_pct:.1f}%** |\n"
            f"| Error Rate | **{err_pct:.2f}%** |\n"
            f"| Bandwidth Served | **{bandwidth_gb:.2f} GB** |"
        )

    # ── BANDWIDTH ──
    if any(w in q for w in ["bandwidth", "data transferred", "total size", "response size"]):
        total_bytes = filtered['response_body_size'].sum()
        avg_bytes = filtered['response_body_size'].mean()
        gb = total_bytes / 1e9
        mb = total_bytes / 1e6
        size_str = f"{gb:.2f} GB" if gb >= 1 else f"{mb:.2f} MB"
        return (
            f"💾 **Bandwidth Stats**\n\n"
            f"- Total transferred: **{size_str}**\n"
            f"- Avg response size: **{avg_bytes/1024:.1f} KB**"
        )

    # ── LATENCY ──
    if any(w in q for w in ["latency", "lag", "response time", "slow"]):
        col = 'time_elapsed'
        if any(w in q for w in ["average", "avg", "mean"]) or q.strip() == "latency":
            return f"📊 Average latency: **{filtered[col].mean():.3f}s**"
        if "min" in q:
            return f"⚡ Minimum latency: **{filtered[col].min():.3f}s**"
        if "max" in q:
            return f"🐌 Maximum latency: **{filtered[col].max():.3f}s**"
        if any(w in q for w in ["variance", "std", "deviation", "distribution"]):
            std = filtered[col].std()
            mean = filtered[col].mean()
            return (
                f"📈 **Latency Distribution**\n\n"
                f"- Mean: **{mean:.3f}s**\n"
                f"- Std Dev: **{std:.3f}s**\n"
                f"- Variance: **{std**2:.6f}**"
            )
        if any(w in q for w in ["percentile", "p99", "p95", "p90", "p75", "p50"]):
            p50 = filtered[col].quantile(0.50)
            p90 = filtered[col].quantile(0.90)
            p95 = filtered[col].quantile(0.95)
            p99 = filtered[col].quantile(0.99)
            return (
                f"📊 **Latency Percentiles**\n\n"
                f"| Percentile | Value |\n|---|---|\n"
                f"| P50 (median) | **{p50:.3f}s** |\n"
                f"| P90 | **{p90:.3f}s** |\n"
                f"| P95 | **{p95:.3f}s** |\n"
                f"| P99 | **{p99:.3f}s** |"
            )
        return "Try: `average latency`, `min latency`, `latency variance`, `p95 latency`"

    # ── CACHE ──
    if any(w in q for w in ["cache", "hit", "miss"]):
        hits  = (filtered['response_state'] == 'HIT').sum()
        misses = (filtered['response_state'] == 'MISS').sum()
        hit_pct  = hits / total * 100
        miss_pct = misses / total * 100
        if "miss" in q and "hit" not in q:
            return f"❌ Cache MISS rate: **{miss_pct:.1f}%** ({misses:,} / {total:,} requests)"
        if "hit" in q and "miss" not in q:
            return f"✅ Cache HIT rate: **{hit_pct:.1f}%** ({hits:,} / {total:,} requests)"
        return (
            f"📊 **Cache Performance**\n\n"
            f"| State | Count | Rate |\n|---|---|---|\n"
            f"| ✅ HIT | **{hits:,}** | **{hit_pct:.1f}%** |\n"
            f"| ❌ MISS | **{misses:,}** | **{miss_pct:.1f}%** |"
        )

    # ── DATACENTER ──
    if any(w in q for w in ["datacenter", "data center", "pop", "pops", "dc"]):
        dc = filtered.groupby('server_datacenter').agg(
            requests=('client_ip', 'count'),
            avg_latency=('time_elapsed', 'mean'),
            avg_rtt=('client_socket_tcpi_rtt', 'mean')
        ).sort_values('requests', ascending=False)
        if any(w in q for w in ["best", "top", "most"]):
            top = dc.index[0]
            return f"🏆 Best datacenter by traffic: **{top}** ({int(dc.iloc[0]['requests']):,} requests, {dc.iloc[0]['avg_latency']:.3f}s avg latency)"
        if any(w in q for w in ["worst", "slowest", "high latency"]):
            dc_lat = dc.sort_values('avg_latency', ascending=False)
            worst = dc_lat.index[0]
            return f"⚠️ Slowest datacenter: **{worst}** (avg latency: {dc_lat.iloc[0]['avg_latency']:.3f}s)"
        rows = "\n".join([
            f"| {name} | {int(r['requests']):,} | {r['avg_latency']:.3f}s | {r['avg_rtt']:.0f}ms |"
            for name, r in dc.iterrows()
        ])
        return (
            f"📊 **Datacenter Performance**\n\n"
            f"| DC | Requests | Latency | RTT |\n|---|---|---|---|\n{rows}"
        )

    # ── ISP ──
    if any(w in q for w in ["isp", "internet service", "provider", "autonomous"]):
        isp = filtered.groupby('client_as_name').agg(
            requests=('client_ip', 'count'),
            avg_latency=('time_elapsed', 'mean'),
            avg_rtt=('client_socket_tcpi_rtt', 'mean')
        ).sort_values('requests', ascending=False)
        if any(w in q for w in ["top", "best", "most"]) and "latency" not in q:
            top = isp.index[0]
            return f"🏆 Top ISP by requests: **{top}** ({int(isp.iloc[0]['requests']):,} requests)"
        if any(w in q for w in ["lowest latency", "fastest", "best latency"]):
            best = isp.sort_values('avg_latency')
            return f"⚡ Fastest ISP: **{best.index[0]}** ({best.iloc[0]['avg_latency']:.3f}s avg latency)"
        if "rtt" in q:
            best = isp.sort_values('avg_rtt')
            return f"⚡ Best RTT ISP: **{best.index[0]}** ({best.iloc[0]['avg_rtt']:.0f}ms)"
        rows = "\n".join([
            f"| {name} | {int(r['requests']):,} | {r['avg_latency']:.3f}s | {r['avg_rtt']:.0f}ms |"
            for name, r in isp.head(10).iterrows()
        ])
        return (
            f"📊 **ISP Performance (Top 10)**\n\n"
            f"| ISP | Requests | Latency | RTT |\n|---|---|---|---|\n{rows}"
        )

    # ── HTTP STATUS ──
    if any(w in q for w in ["status", "error", "5xx", "4xx", "2xx", "http"]):
        if "5xx" in q or ("error" in q and "server" in q):
            n = (filtered['response_status'] >= 500).sum()
            return f"🔴 5xx Server Errors: **{n:,}** ({n/total*100:.2f}%)"
        if "4xx" in q or ("error" in q and "client" in q):
            n = ((filtered['response_status'] >= 400) & (filtered['response_status'] < 500)).sum()
            return f"🟠 4xx Client Errors: **{n:,}** ({n/total*100:.2f}%)"
        if "2xx" in q or "success" in q:
            n = ((filtered['response_status'] >= 200) & (filtered['response_status'] < 300)).sum()
            return f"✅ 2xx Successes: **{n:,}** ({n/total*100:.2f}%)"
        if "error rate" in q or "errors" in q:
            n = (filtered['response_status'] >= 400).sum()
            return f"📊 Overall Error Rate: **{n/total*100:.2f}%** ({n:,} / {total:,})"
        # breakdown table
        sc = filtered['response_status'].value_counts().sort_index()
        rows = "\n".join([f"| {code} | {cnt:,} | {cnt/total*100:.1f}% |" for code, cnt in sc.items()])
        return f"📊 **HTTP Status Breakdown**\n\n| Code | Count | % |\n|---|---|---|\n{rows}"

    # ── GEO / CITY ──
    if any(w in q for w in ["city", "cities", "location", "geo", "geography"]):
        geo = filtered.groupby('geo_city').agg(
            requests=('client_ip', 'count'),
            avg_latency=('time_elapsed', 'mean')
        ).sort_values('requests', ascending=False)
        if "slowest" in q:
            s = geo.sort_values('avg_latency', ascending=False)
            return f"🐌 Slowest city: **{s.index[0]}** (avg {s.iloc[0]['avg_latency']:.3f}s latency)"
        if "fastest" in q:
            s = geo.sort_values('avg_latency')
            return f"⚡ Fastest city: **{s.index[0]}** (avg {s.iloc[0]['avg_latency']:.3f}s latency)"
        if any(w in q for w in ["top", "most", "highest"]):
            return f"📍 Top city: **{geo.index[0]}** ({int(geo.iloc[0]['requests']):,} requests)"
        rows = "\n".join([
            f"| {city} | {int(r['requests']):,} | {r['avg_latency']:.3f}s |"
            for city, r in geo.head(10).iterrows()
        ])
        return (
            f"📊 **City Performance (Top 10)**\n\n"
            f"| City | Requests | Avg Latency |\n|---|---|---|\n{rows}"
        )

    # ── BACKEND ──
    if any(w in q for w in ["backend", "endpoint", "server name"]):
        be = filtered.groupby('req.backend.name').agg(
            requests=('client_ip', 'count'),
            avg_latency=('time_elapsed', 'mean')
        ).sort_values('requests', ascending=False)
        if any(w in q for w in ["top", "most", "best"]):
            return f"🏆 Most used backend: **{be.index[0]}** ({int(be.iloc[0]['requests']):,} requests)"
        rows = "\n".join([
            f"| {name} | {int(r['requests']):,} | {r['avg_latency']:.3f}s |"
            for name, r in be.iterrows()
        ])
        return f"📊 **Backend Performance**\n\n| Backend | Requests | Latency |\n|---|---|---|\n{rows}"

    # ── RTT ──
    if any(w in q for w in ["rtt", "round trip"]):
        col = 'client_socket_tcpi_rtt'
        if "average" in q or "avg" in q or "mean" in q or q.strip() == "rtt":
            return f"📊 Average RTT: **{filtered[col].mean():.0f} ms**"
        if "min" in q:
            return f"⚡ Minimum RTT: **{filtered[col].min():.0f} ms**"
        if "max" in q:
            return f"🐌 Maximum RTT: **{filtered[col].max():.0f} ms**"
        p95 = filtered[col].quantile(0.95)
        return (
            f"📊 **RTT Stats**\n\n"
            f"- Avg: **{filtered[col].mean():.0f} ms**\n"
            f"- Min: **{filtered[col].min():.0f} ms**\n"
            f"- Max: **{filtered[col].max():.0f} ms**\n"
            f"- P95: **{p95:.0f} ms**"
        )

    # ── UNKNOWN ──
    return (
        "🤔 I didn't quite catch that. Type **`help`** to see everything I can answer, "
        "or try: `latency`, `cache hit rate`, `error rate`, `top datacenter`, `summary`."
    )


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def main():

    # ── HERO HEADER ──
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {EPL_PURPLE} 0%, #5a0070 50%, {EPL_PURPLE} 100%);
        border: 1px solid rgba(255,40,130,0.3);
        border-radius: 20px;
        padding: 2rem 2.5rem 1.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 40px rgba(255,40,130,0.2);
    ">
        <div style="font-size: 2.8rem; margin-bottom: 0.2rem;">⚽</div>
        <h1 style="
            color: white;
            font-size: 2.4rem;
            font-weight: 800;
            margin: 0 0 0.3rem;
            letter-spacing: -0.5px;
        ">CDN Logs Dashboard</h1>
        <p style="
            color: {EPL_PINK};
            font-size: 1rem;
            font-weight: 600;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin: 0;
        ">Premier League · Network Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # ── LOAD DATA ──
    try:
        if 'df' not in st.session_state:
            st.session_state.df = load_logs()
        if 'original_df' not in st.session_state:
            st.session_state.original_df = st.session_state.df.copy()
        df = st.session_state.df.copy()
    except Exception as e:
        st.error(f"Failed to load log data: {e}")
        st.stop()

    if df.empty:
        st.warning("No log data available to display.")
        st.stop()

    # ── INIT CHAT HISTORY ──
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding: 0.5rem 0 1.2rem;">
            <div style="font-size:2rem;">⚽</div>
            <div style="color:{EPL_PINK}; font-weight:700; letter-spacing:2px; font-size:0.8rem; text-transform:uppercase;">
                CDN · EPL Edition
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<span class='section-badge'>🔎 Filter Logs</span>", unsafe_allow_html=True)

        # Upload section
        with st.expander("📂 Upload Logs (JSON/CSV)", expanded=False):
            upload_mode = st.radio("Upload Mode", ("Replace data", "Append data"), index=0, key="upload_mode")
            uploaded_files = st.file_uploader(
                "Upload JSON/CSV log files",
                type=['json', 'csv'],
                accept_multiple_files=True,
                key="log_uploader"
            )

            if uploaded_files:
                new_logs = []
                for uf in uploaded_files:
                    try:
                        raw = uf.read()
                        text = raw.decode('utf-8') if isinstance(raw, (bytes, bytearray)) else str(raw)
                        if uf.name.lower().endswith('.json'):
                            try:
                                obj = json.loads(text)
                                new_logs.extend(obj if isinstance(obj, list) else [obj])
                            except Exception:
                                for line in text.splitlines():
                                    line = line.strip()
                                    if line:
                                        try:
                                            new_logs.append(json.loads(line))
                                        except Exception:
                                            st.error(f"Bad JSON line in {uf.name}")
                        elif uf.name.lower().endswith('.csv'):
                            try:
                                df_csv = pd.read_csv(io.StringIO(text))
                                new_logs.extend(df_csv.to_dict(orient='records'))
                            except Exception:
                                st.error(f"Failed to parse {uf.name} as CSV")
                    except Exception as ex:
                        st.error(f"Failed to read {uf.name}: {ex}")

                if new_logs:
                    new_df = pd.DataFrame(new_logs)
                    st.markdown("**Preview (first 10 rows)**")
                    st.dataframe(new_df.head(10))

                    expected_cols = [
                        'client_ip', 'client_as_name', 'geo_city', 'geo_country',
                        'server_datacenter', 'response_status', 'response_state',
                        'req.backend.name', 'client_socket_tcpi_rtt',
                        'time_elapsed', 'response_body_size'
                    ]
                    st.markdown("**Column Mapping (optional)**")
                    col_map = {}
                    opts = ["-- none --"] + list(new_df.columns)
                    for ec in expected_cols:
                        sel = st.selectbox(f"'{ec}'", opts, index=0, key=f"map_{ec}")
                        if sel and sel != "-- none --":
                            col_map[ec] = sel

                    col_apply, col_undo = st.columns(2)
                    apply_col_map = col_apply.button("✅ Apply", key="apply_upload")
                    undo_btn = col_undo.button("↩️ Undo", key="undo_upload")

                    if undo_btn:
                        if 'original_df' in st.session_state:
                            st.session_state.df = st.session_state.original_df.copy()
                            df = st.session_state.df.copy()
                            st.success("Reverted to original dataset")
                        else:
                            st.warning("Nothing to revert.")

                    if apply_col_map:
                        renamed = new_df.rename(columns={v: k for k, v in col_map.items()})
                        if 'response_status' in renamed.columns:
                            try:
                                renamed['response_status'] = pd.to_numeric(
                                    renamed['response_status'], errors='coerce'
                                ).fillna(0).astype(int)
                            except Exception:
                                pass
                        st.session_state.original_df = st.session_state.df.copy()
                        if upload_mode == "Replace data":
                            st.session_state.df = renamed
                        else:
                            st.session_state.df = pd.concat(
                                [st.session_state.df, renamed], ignore_index=True, sort=False
                            )
                        df = st.session_state.df.copy()
                        st.success(f"{upload_mode} applied ✓")

        st.markdown("---")

        # Always read from session_state so options refresh immediately after upload/append/undo
        _df = st.session_state.df

        st.markdown(f"<span class='section-badge'>🔎 Filter & Compare</span>", unsafe_allow_html=True)

        isp_all        = sorted(_df['client_as_name'].dropna().unique().tolist())
        dc_all         = sorted(_df['server_datacenter'].dropna().unique().tolist())
        city_all       = sorted(_df['geo_city'].dropna().unique().tolist())
        status_all     = sorted(_df['response_status'].dropna().unique().tolist())
        cache_all      = sorted(_df['response_state'].dropna().unique().tolist())
        backend_all    = sorted(_df['req.backend.name'].dropna().unique().tolist())

        isp_sel        = st.multiselect("📡 ISP (multi-select)", isp_all, default=[], key="f_isp",
                                         placeholder="All ISPs")
        datacenter_sel = st.multiselect("🏟️ Datacenter (multi-select)", dc_all, default=[], key="f_dc",
                                         placeholder="All Datacenters")
        city           = st.selectbox("📍 City",        ["All"] + city_all,                    key="f_city")
        status         = st.selectbox("🔢 HTTP Status", ["All"] + [str(s) for s in status_all], key="f_status")
        cache_state    = st.selectbox("⚡ Cache State", ["All"] + cache_all,                   key="f_cache")
        backend        = st.selectbox("⚙️ Backend",     ["All"] + backend_all,                 key="f_backend")

        _preview = _df.copy()
        if isp_sel:        _preview = _preview[_preview['client_as_name'].isin(isp_sel)]
        if datacenter_sel: _preview = _preview[_preview['server_datacenter'].isin(datacenter_sel)]
        st.caption(f"📋 {len(_preview):,} records match current ISP/DC selection")

        if st.button("🔄 Reset All Filters", key="reset_filters"):
            for k in ["f_isp", "f_dc", "f_city", "f_status", "f_cache", "f_backend"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    # ── APPLY FILTERS (outside sidebar, reads live session_state.df) ──
    df = st.session_state.df.copy()
    filtered = df.copy()
    if isp_sel:            filtered = filtered[filtered['client_as_name'].isin(isp_sel)]
    if datacenter_sel:     filtered = filtered[filtered['server_datacenter'].isin(datacenter_sel)]
    if city != "All":      filtered = filtered[filtered['geo_city'] == city]
    if status != "All":    filtered = filtered[filtered['response_status'] == int(status)]
    if cache_state != "All": filtered = filtered[filtered['response_state'] == cache_state]
    if backend != "All":   filtered = filtered[filtered['req.backend.name'] == backend]

    n = len(filtered)
    if n == 0:
        st.warning("⚠️ No data matches the current filters.")
        st.stop()

    # ─────────────────────────────────────────
    # KPI METRICS ROW
    # ─────────────────────────────────────────
    st.markdown(f"<span class='section-badge'>📊 Key Metrics</span>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Requests",   f"{n:,}")
    c2.metric("Unique IPs",        f"{filtered['client_ip'].nunique():,}")
    c3.metric("Cities",            filtered['geo_city'].nunique())
    c4.metric("Datacenters",       filtered['server_datacenter'].nunique())
    c5.metric("Avg RTT (ms)",      f"{filtered['client_socket_tcpi_rtt'].mean():.0f}")
    c6.metric("Avg Latency (s)",   f"{filtered['time_elapsed'].mean():.3f}")

    st.markdown("---")

    # ─────────────────────────────────────────
    # ROW 1: DC · Cache · HTTP Status
    # ─────────────────────────────────────────
    st.markdown(f"<span class='section-badge'>🏟️ Traffic Breakdown</span>", unsafe_allow_html=True)
    r1c1, r1c2, r1c3 = st.columns(3)

    # Datacenter Distribution
    with r1c1:
        st.subheader("Datacenter Distribution")
        dc_counts = (
            filtered['server_datacenter']
            .value_counts().rename_axis('Datacenter').reset_index(name='Requests')
        )
        fig1 = go.Figure(go.Bar(
            x=dc_counts['Datacenter'], y=dc_counts['Requests'],
            marker=dict(
                color=dc_counts['Requests'],
                colorscale=EPL_SCALE,
                showscale=False,
                line=dict(color="rgba(255,255,255,0.1)", width=0.5)
            ),
            hovertemplate="<b>%{x}</b><br>Requests: %{y:,}<extra></extra>",
        ))
        apply_theme(fig1, xaxis_title="Datacenter", yaxis_title="Requests")
        st.plotly_chart(fig1, use_container_width=True)

    # Cache State
    with r1c2:
        st.subheader("Cache HIT / MISS")
        cache_counts = (
            filtered['response_state']
            .value_counts().rename_axis('State').reset_index(name='Requests')
        )
        COLOR_MAP = {'HIT': EPL_TEAL, 'MISS': EPL_PINK}
        cache_counts['color'] = cache_counts['State'].map(COLOR_MAP).fillna("#888")
        fig2 = go.Figure(go.Pie(
            labels=cache_counts['State'],
            values=cache_counts['Requests'],
            marker=dict(colors=cache_counts['color'].tolist(),
                        line=dict(color=EPL_PURPLE, width=3)),
            hole=0.55,
            textinfo='label+percent',
            textfont=dict(color=EPL_LIGHT, size=13),
            hovertemplate="<b>%{label}</b><br>%{value:,} requests<br>%{percent}<extra></extra>",
        ))
        apply_theme(fig2, showlegend=False,
                    annotations=[dict(text="Cache", x=0.5, y=0.5,
                                      font=dict(size=16, color=EPL_LIGHT),
                                      showarrow=False)])
        st.plotly_chart(fig2, use_container_width=True)

    # HTTP Status
    with r1c3:
        st.subheader("HTTP Status Codes")
        sc = (
            filtered['response_status']
            .value_counts().rename_axis('Status').reset_index(name='Requests')
            .sort_values('Status')
        )
        def status_color(code):
            if code < 300: return EPL_TEAL
            if code < 400: return EPL_GOLD
            if code < 500: return "#FF6B35"
            return EPL_PINK
        sc['color'] = sc['Status'].apply(status_color)
        fig3 = go.Figure(go.Bar(
            x=sc['Status'].astype(str), y=sc['Requests'],
            marker=dict(color=sc['color'],
                        line=dict(color="rgba(255,255,255,0.1)", width=0.5)),
            hovertemplate="<b>HTTP %{x}</b><br>%{y:,} requests<extra></extra>",
        ))
        apply_theme(fig3, xaxis_title="Status Code", yaxis_title="Requests")
        st.plotly_chart(fig3, use_container_width=True)

    # ─────────────────────────────────────────
    # ROW 2: RTT · Latency · Geo
    # ─────────────────────────────────────────
    st.markdown(f"<span class='section-badge'>📡 Network Performance</span>", unsafe_allow_html=True)
    r2c1, r2c2, r2c3 = st.columns(3)

    SAMPLE = min(500, n)

    # RTT Trend
    with r2c1:
        st.subheader("Client RTT (ms)")
        sample = filtered.sample(SAMPLE, random_state=42).sort_index() if n > SAMPLE else filtered
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=list(range(len(sample))), y=sample['client_socket_tcpi_rtt'],
            mode='lines', name='RTT',
            line=dict(color=EPL_TEAL, width=1.5, shape='spline'),
            fill='tozeroy', fillcolor=f"rgba(0,255,133,0.08)",
            hovertemplate="Index: %{x}<br>RTT: %{y:.0f} ms<extra></extra>",
        ))
        apply_theme(fig4, xaxis_title="Request Index", yaxis_title="RTT (ms)")
        st.plotly_chart(fig4, use_container_width=True)

    # Latency Trend
    with r2c2:
        st.subheader("Request Latency (s)")
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(
            x=list(range(len(sample))), y=sample['time_elapsed'],
            mode='lines', name='Latency',
            line=dict(color=EPL_PINK, width=1.5, shape='spline'),
            fill='tozeroy', fillcolor=f"rgba(255,40,130,0.08)",
            hovertemplate="Index: %{x}<br>Latency: %{y:.3f}s<extra></extra>",
        ))
        apply_theme(fig5, xaxis_title="Request Index", yaxis_title="Latency (s)")
        st.plotly_chart(fig5, use_container_width=True)

    # Top Cities (horizontal)
    with r2c3:
        st.subheader("Top Cities by Traffic")
        geo = (
            filtered['geo_city'].value_counts().head(10)
            .rename_axis('City').reset_index(name='Requests')
        )
        fig6 = go.Figure(go.Bar(
            y=geo['City'], x=geo['Requests'],
            orientation='h',
            marker=dict(
                color=geo['Requests'],
                colorscale=EPL_SCALE,
                showscale=False,
                line=dict(color="rgba(255,255,255,0.1)", width=0.5)
            ),
            hovertemplate="<b>%{y}</b><br>%{x:,} requests<extra></extra>",
        ))
        apply_theme(fig6, xaxis_title="Requests", yaxis_title="", height=350,
                    margin=dict(t=40, b=50, l=120, r=20))
        st.plotly_chart(fig6, use_container_width=True)

    # ─────────────────────────────────────────
    # ISP PERFORMANCE
    # ─────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"<span class='section-badge'>📡 ISP Intelligence</span>", unsafe_allow_html=True)
    st.subheader("ISP Performance by Latency")
    isp_perf = (
        filtered.groupby('client_as_name').agg(
            requests=('client_ip', 'count'),
            avg_rtt=('client_socket_tcpi_rtt', 'mean'),
            avg_latency=('time_elapsed', 'mean')
        ).sort_values('avg_latency').head(15)
    )
    fig_isp = go.Figure()
    fig_isp.add_trace(go.Bar(
        y=isp_perf.index, x=isp_perf['avg_latency'],
        orientation='h', name='Avg Latency',
        marker=dict(
            color=isp_perf['avg_latency'],
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title=dict(text="Latency (s)", font=dict(color=EPL_LIGHT)), tickfont=dict(color=EPL_LIGHT)),
            line=dict(color="rgba(255,255,255,0.1)", width=0.5)
        ),
        hovertemplate="<b>%{y}</b><br>Avg Latency: %{x:.3f}s<extra></extra>",
    ))
    apply_theme(fig_isp, xaxis_title="Average Latency (s)", yaxis_title="",
                height=420, margin=dict(t=40, b=50, l=180, r=80))
    st.plotly_chart(fig_isp, use_container_width=True)

    # ─────────────────────────────────────────
    # CUSTOM CHART PANEL
    # ─────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"<span class='section-badge'>🎨 Custom Explorer</span>", unsafe_allow_html=True)
    st.subheader("Build Your Own Chart")

    label_options = {
        "Datacenter": "server_datacenter",
        "City": "geo_city",
        "ISP": "client_as_name",
        "HTTP Status": "response_status",
        "Cache State": "response_state",
        "Backend": "req.backend.name",
    }
    metric_options = {
        "Number of Requests": ("count", None),
        "Average RTT (ms)": ("mean", "client_socket_tcpi_rtt"),
        "Average Latency (s)": ("mean", "time_elapsed"),
        "Average Response Size (bytes)": ("mean", "response_body_size"),
    }
    chart_types = ["Bar", "Horizontal Bar", "Scatter"]

    colx, coly, colz = st.columns(3)
    with colx:
        label_choice = st.selectbox("X Axis (Label)", list(label_options.keys()), key="custom_label")
    with coly:
        metric_choice = st.selectbox("Y Axis (Metric)", list(metric_options.keys()), key="custom_metric")
    with colz:
        chart_type = st.selectbox("Chart Type", chart_types, key="custom_chart_type")

    group_field = label_options[label_choice]
    agg_func, metric_field = metric_options[metric_choice]

    if agg_func == "count":
        chart_data = (
            filtered[group_field].value_counts()
            .rename_axis(label_choice).reset_index(name='Value').head(15)
        )
        y_col, y_label = 'Value', 'Number of Requests'
    else:
        chart_data = (
            filtered.groupby(group_field)[metric_field].mean()
            .rename_axis(label_choice).reset_index(name='Value').head(15)
        )
        y_col, y_label = 'Value', metric_choice

    fig_custom = go.Figure()
    if chart_type == "Bar":
        fig_custom.add_trace(go.Bar(
            x=chart_data[label_choice], y=chart_data[y_col],
            marker=dict(color=chart_data[y_col], colorscale=EPL_SCALE, showscale=True),
            hovertemplate=f"<b>%{{x}}</b><br>{y_label}: %{{y}}<extra></extra>",
        ))
        apply_theme(fig_custom, xaxis_title=label_choice, yaxis_title=y_label, height=420)
    elif chart_type == "Horizontal Bar":
        fig_custom.add_trace(go.Bar(
            y=chart_data[label_choice], x=chart_data[y_col],
            orientation='h',
            marker=dict(color=chart_data[y_col], colorscale=EPL_SCALE, showscale=True),
            hovertemplate=f"<b>%{{y}}</b><br>{y_label}: %{{x}}<extra></extra>",
        ))
        apply_theme(fig_custom, xaxis_title=y_label, yaxis_title=label_choice,
                    height=420, margin=dict(t=40, b=50, l=150, r=80))
    elif chart_type == "Scatter":
        fig_custom.add_trace(go.Scatter(
            x=list(range(len(chart_data))), y=chart_data[y_col],
            mode='markers',
            marker=dict(size=12, color=chart_data[y_col],
                        colorscale=EPL_SCALE, showscale=True,
                        line=dict(color=EPL_PURPLE, width=1)),
            hovertemplate=f"<b>%{{text}}</b><br>{y_label}: %{{y}}<extra></extra>",
        ))
        apply_theme(fig_custom, xaxis_title="", yaxis_title=y_label, height=420)

    st.plotly_chart(fig_custom, use_container_width=True)

    # ─────────────────────────────────────────
    # CHATBOT  (multi-turn with history)
    # ─────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"<span class='section-badge'>🤖 Log Intelligence Bot</span>", unsafe_allow_html=True)
    st.subheader("Ask the Log Bot")

    with st.expander("💬 Chat with your data", expanded=True):
        # Quick-fire suggestion buttons
        st.markdown("**Quick questions:**")
        q_cols = st.columns(4)
        suggestions = [
            "Summary", "Cache hit rate", "Error rate",
            "Best datacenter", "P95 latency", "Top ISP",
            "Top city", "Bandwidth",
        ]
        for i, sug in enumerate(suggestions):
            if q_cols[i % 4].button(sug, key=f"sug_{i}"):
                st.session_state.chat_history.append(("user", sug))
                st.session_state.chat_history.append(
                    ("bot", handle_question(sug, filtered))
                )

        st.markdown("---")

        # Render chat history
        for role, msg in st.session_state.chat_history:
            css_class = "user-msg" if role == "user" else "bot-msg"
            prefix = "👤" if role == "user" else "⚽"
            st.markdown(
                f'<div class="{css_class}">{prefix} {msg}</div>',
                unsafe_allow_html=True
            )

        # Input row
        inp_col, btn_col, clr_col = st.columns([5, 1, 1])
        with inp_col:
            user_q = st.text_input(
                "Your question",
                label_visibility="collapsed",
                placeholder="e.g.  p99 latency · cache hit % · top datacenter · help",
                key="chat_input"
            )
        with btn_col:
            send = st.button("Send ➤", key="chat_send", use_container_width=True)
        with clr_col:
            if st.button("Clear", key="chat_clear", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        if send and user_q.strip():
            answer = handle_question(user_q, filtered)
            st.session_state.chat_history.append(("user", user_q))
            st.session_state.chat_history.append(("bot", answer))
            st.rerun()

    # ─────────────────────────────────────────
    # RAW LOG TABLE
    # ─────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"<span class='section-badge'>📋 Raw Logs</span>", unsafe_allow_html=True)
    st.subheader(f"Log Table — showing {min(30, n):,} of {n:,} records")
    st.dataframe(
        filtered.head(30),
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()
