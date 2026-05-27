
import streamlit as st
import json
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import io
import sys

# IMPORTANT: page config must be first Streamlit command
st.set_page_config(
    page_title="CDN Logs Dashboard",
    layout="wide",
    page_icon="📈"
)

# Pleasant light theme and modern UI polish
st.markdown(
    """
    <style>
    body, .stApp {
        background: #f7fafc;
        color: #222;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stMetric, .stDataFrame, .stTable, .stMarkdown, .stHeader, .stSubheader {
        background: #fff !important;
        border-radius: 12px;
        box-shadow: 0 2px 12px #e2e8f0;
        color: #222 !important;
    }
    .stMetric label, .stMetric div {
        color: #2b6cb0 !important;
        font-weight: 600;
    }    .stButton>button {
        background: linear-gradient(90deg, #90cdf4 0%, #f6e05e 100%);
        color: #222;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 1px 4px #e2e8f0;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #f6e05e 0%, #90cdf4 100%);
    }

    .stRadio > div {
        padding: 0.25rem 0;
    }

    .stRadio label {
        cursor: pointer !important;
    }
    .stSidebar {
        background: #e3f2fd !important;
    }
    .stCaption, .stMarkdown p, .stDataFrame, .stTable {
        color: #444 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def load_logs():

    data_dir = Path(__file__).parent / "mock_data"

    logs = []

    for fname in [
        "cdn_logs_day1.json",
        "cdn_logs_day2.json",
        "cdn_logs_day3.json"
    ]:

        with open(data_dir / fname, "r", encoding="utf-8") as f:
            logs.extend(json.load(f))

    return pd.DataFrame(logs)


def main():
    st.markdown("""
        <h1 style='text-align: center; color: #2b6cb0; font-size: 2.8rem; margin-bottom: 0.5em;'>
            <span style='color:#2b6cb0;'>CDN Logs Dashboard</span>
        </h1>
    """, unsafe_allow_html=True)

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

    # --- FILTERS + UPLOAD ---
    with st.sidebar:
        st.header("🔎 Filter Logs")
        st.markdown("**Upload logs (JSON/CSV)**")
        upload_mode = st.radio("Upload Mode", ("Replace data", "Append data"), index=0, key="upload_mode")
        uploaded_files = st.file_uploader("Upload JSON/CSV log files", type=['json','csv'], accept_multiple_files=True, key="log_uploader")

        if uploaded_files:
            # parse uploaded files into a single DataFrame (new_df)
            new_logs = []
            for uf in uploaded_files:
                try:
                    raw = uf.read()
                    text = raw.decode('utf-8') if isinstance(raw, (bytes, bytearray)) else str(raw)
                    if uf.name.lower().endswith('.json'):
                        try:
                            obj = json.loads(text)
                            if isinstance(obj, list):
                                new_logs.extend(obj)
                            else:
                                new_logs.append(obj)
                        except Exception:
                            # try newline-delimited json
                            for line in text.splitlines():
                                line = line.strip()
                                if line:
                                    try:
                                        new_logs.append(json.loads(line))
                                    except Exception:
                                        st.error(f"Failed to parse a line in {uf.name} as JSON")
                    elif uf.name.lower().endswith('.csv'):
                        try:
                            df_csv = pd.read_csv(io.StringIO(text))
                            new_logs.extend(df_csv.to_dict(orient='records'))
                        except Exception:
                            st.error(f"Failed to parse {uf.name} as CSV")
                except Exception as e:
                    st.error(f"Failed to read {uf.name}: {e}")

            if new_logs:
                new_df = pd.DataFrame(new_logs)

                # save original for undo
                if 'original_df' not in st.session_state:
                    st.session_state['original_df'] = df.copy()

                st.markdown("**Preview of uploaded data (first 10 rows)**")
                st.dataframe(new_df.head(10))

                # column mapping UI
                expected_cols = [
                    'client_ip','client_as_name','geo_city','geo_country','server_datacenter',
                    'response_status','response_state','req.backend.name','client_socket_tcpi_rtt',
                    'time_elapsed','response_body_size'
                ]
                st.markdown("**Map uploaded columns to expected fields (optional)**")
                col_map = {}
                uploaded_cols = list(new_df.columns)
                uploaded_cols_options = ["-- none --"] + uploaded_cols
                for ec in expected_cols:
                    sel = st.selectbox(f"Map '{ec}' to", uploaded_cols_options, index=0, key=f"map_{ec}")
                    if sel and sel != "-- none --":
                        col_map[ec] = sel

                apply_col_map = st.button("Apply upload", key="apply_upload")
                undo_btn = st.button("Undo upload (revert)", key="undo_upload")

                if undo_btn:
                    if 'original_df' in st.session_state:
                        st.session_state.df = st.session_state.original_df.copy()
                        df = st.session_state.df.copy()
                        st.success("Reverted to original dataset")
                    else:
                        st.warning("No previous dataset to revert to.")

                if apply_col_map:
                    # rename columns according to mapping
                    renamed = new_df.copy()
                    rename_dict = {v: k for k, v in col_map.items()}

                    if rename_dict:
                        renamed = renamed.rename(columns=rename_dict)

                    # coerce expected types where possible
                    if 'response_status' in renamed.columns:
                        try:
                            renamed['response_status'] = pd.to_numeric(
                                renamed['response_status'],
                                errors='coerce'
                            ).fillna(0).astype(int)
                        except Exception:
                            pass

                    # save current dataset before changes
                    st.session_state.original_df = st.session_state.df.copy()

                    # FIXED upload mode handling
                    if upload_mode == "Replace data":
                        st.session_state.df = renamed
                    else:
                        st.session_state.df = pd.concat(
                            [st.session_state.df, renamed],
                            ignore_index=True,
                            sort=False
                        )

                    df = st.session_state.df.copy()

                    st.success(f"{upload_mode} applied successfully")

        def pretty_options(label, options):
            return ["All"] + [f"{label}: {str(o)}" for o in sorted(options)]

        city_options = df['geo_city'].unique().tolist()
        datacenter_options = df['server_datacenter'].unique().tolist()
        status_options = df['response_status'].unique().tolist()
        cache_state_options = df['response_state'].unique().tolist()
        backend_options = df['req.backend.name'].unique().tolist()
        isp_options = df['client_as_name'].unique().tolist()

        city = st.selectbox("City", pretty_options("City", city_options), key="filter_city")
        datacenter = st.selectbox("Datacenter", pretty_options("DC", datacenter_options), key="filter_dc")
        status = st.selectbox("HTTP Status", pretty_options("Status", status_options), key="filter_status")
        cache_state = st.selectbox("Cache State", pretty_options("State", cache_state_options), key="filter_cache")
        backend = st.selectbox("Backend Name", pretty_options("Backend", backend_options), key="filter_backend")
        isp = st.selectbox("ISP", pretty_options("ISP", isp_options), key="filter_isp")

        filtered = df.copy()
        if city != "All":
            city_val = city.split(": ",1)[1]
            filtered = filtered[filtered['geo_city'] == city_val]
        if datacenter != "All":
            dc_val = datacenter.split(": ",1)[1]
            filtered = filtered[filtered['server_datacenter'] == dc_val]
        if status != "All":
            status_val = status.split(": ",1)[1]
            filtered = filtered[filtered['response_status'] == int(status_val)]
        if cache_state != "All":
            state_val = cache_state.split(": ",1)[1]
            filtered = filtered[filtered['response_state'] == state_val]
        if backend != "All":
            backend_val = backend.split(": ",1)[1]
            filtered = filtered[filtered['req.backend.name'] == backend_val]
        if isp != "All":
            isp_val = isp.split(": ",1)[1]
            filtered = filtered[filtered['client_as_name'] == isp_val]

    # --- SUMMARY METRICS ---
    st.markdown("---")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Requests", len(filtered))
    col2.metric("Unique IPs", filtered['client_ip'].nunique())
    col3.metric("Cities", filtered['geo_city'].nunique())
    col4.metric("Datacenters", filtered['server_datacenter'].nunique())
    col5.metric("Avg. RTT (ms)", f"{filtered['client_socket_tcpi_rtt'].mean():.0f}")
    col6.metric("Avg. Latency (s)", f"{filtered['time_elapsed'].mean():.3f}")

    # --- PANELS ---
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Datacenter Distribution")
        dc_counts = filtered['server_datacenter'].value_counts().rename_axis('Datacenter').reset_index(name='Requests')
        fig1 = go.Figure(data=[go.Bar(x=dc_counts['Datacenter'], y=dc_counts['Requests'], marker=dict(color=dc_counts['Requests'], colorscale='Blues', showscale=False), text=dc_counts['Requests'], textposition='auto')])
        fig1.update_layout(xaxis_title='Datacenter', yaxis_title='Requests', hovermode='x unified', plot_bgcolor='rgba(240, 245, 250, 0.5)', paper_bgcolor='white', height=350, margin=dict(b=50))
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.subheader("Cache State (HIT/MISS)")
        cache_counts = filtered['response_state'].value_counts().rename_axis('State').reset_index(name='Requests')
        colors = {'HIT': '#2ecc71', 'MISS': '#e74c3c'}
        cache_counts['color'] = cache_counts['State'].map(colors)
        fig2 = go.Figure(data=[go.Bar(x=cache_counts['State'], y=cache_counts['Requests'], marker=dict(color=cache_counts['color']), text=cache_counts['Requests'], textposition='auto')])
        fig2.update_layout(xaxis_title='Cache State', yaxis_title='Requests', hovermode='x unified', plot_bgcolor='rgba(240, 245, 250, 0.5)', paper_bgcolor='white', height=350, margin=dict(b=50), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    with c3:
        st.subheader("HTTP Status Codes")
        status_counts = filtered['response_status'].value_counts().rename_axis('Status').reset_index(name='Requests').sort_values('Status')
        fig3 = go.Figure(data=[go.Bar(x=status_counts['Status'], y=status_counts['Requests'], marker=dict(color=status_counts['Requests'], colorscale='Viridis', showscale=False), text=status_counts['Requests'], textposition='auto')])
        fig3.update_layout(xaxis_title='HTTP Status Code', yaxis_title='Requests', hovermode='x unified', plot_bgcolor='rgba(240, 245, 250, 0.5)', paper_bgcolor='white', height=350, margin=dict(b=50))
        st.plotly_chart(fig3, use_container_width=True)

    c4, c5, c6 = st.columns(3)
    with c4:
        st.subheader("Client RTT (ms)")
        if not filtered.empty:
            fig4 = go.Figure(data=[go.Scatter(x=list(range(len(filtered))), y=filtered['client_socket_tcpi_rtt'], mode='lines+markers', name='RTT', line=dict(color='#3498db', width=2), marker=dict(size=4))])
            fig4.update_layout(xaxis_title='Log Index', yaxis_title='RTT (ms)', hovermode='x unified', plot_bgcolor='rgba(240, 245, 250, 0.5)', paper_bgcolor='white', height=350, margin=dict(b=50))
            st.plotly_chart(fig4, use_container_width=True)

    with c5:
        st.subheader("Request Latency (s)")
        if not filtered.empty:
            fig5 = go.Figure(data=[go.Scatter(x=list(range(len(filtered))), y=filtered['time_elapsed'], mode='lines+markers', name='Latency', line=dict(color='#e67e22', width=2), marker=dict(size=4))])
            fig5.update_layout(xaxis_title='Log Index', yaxis_title='Latency (s)', hovermode='x unified', plot_bgcolor='rgba(240, 245, 250, 0.5)', paper_bgcolor='white', height=350, margin=dict(b=50))
            st.plotly_chart(fig5, use_container_width=True)

    with c6:
        st.subheader("Geo Location (City)")
        geo_counts = filtered['geo_city'].value_counts().head(10).rename_axis('City').reset_index(name='Requests')
        fig6 = go.Figure(data=[go.Bar(y=geo_counts['City'], x=geo_counts['Requests'], orientation='h', marker=dict(color=geo_counts['Requests'], colorscale='Teal', showscale=False), text=geo_counts['Requests'], textposition='auto')])
        fig6.update_layout(xaxis_title='Requests', yaxis_title='City', hovermode='y unified', plot_bgcolor='rgba(240, 245, 250, 0.5)', paper_bgcolor='white', height=350, margin=dict(l=100))
        st.plotly_chart(fig6, use_container_width=True)

    st.markdown("---")
    st.subheader("ISP Performance by Latency 📊")
    if not filtered.empty:
        isp_perf = filtered.groupby('client_as_name').agg(
            requests=('client_ip', 'count'),
            avg_rtt=('client_socket_tcpi_rtt', 'mean'),
            avg_latency=('time_elapsed', 'mean')
        ).sort_values('avg_latency', ascending=True).head(15)
        
        fig_isp = go.Figure()
        fig_isp.add_trace(go.Bar(y=isp_perf.index, x=isp_perf['avg_latency'], name='Avg Latency (s)', orientation='h', marker=dict(color=isp_perf['avg_latency'], colorscale='RdYlGn_r', showscale=True, colorbar=dict(title="Latency (s)"))))
        fig_isp.update_layout(xaxis_title='Average Latency (seconds)', yaxis_title='ISP', hovermode='y unified', plot_bgcolor='rgba(240, 245, 250, 0.5)', paper_bgcolor='white', height=400, margin=dict(l=150))
        st.plotly_chart(fig_isp, use_container_width=True)

    # --- CUSTOM CHART PANEL ---
    st.markdown("---")
    st.subheader("Custom Chart Panel 🎨")
    label_options = {
        "Datacenter": "server_datacenter",
        "City": "geo_city",
        "ISP": "client_as_name",
        "HTTP Status": "response_status",
        "Cache State": "response_state",
        "Backend": "req.backend.name"
    }
    metric_options = {
        "Number of Requests": ("count", None),
        "Average RTT (ms)": ("mean", "client_socket_tcpi_rtt"),
        "Average Latency (s)": ("mean", "time_elapsed"),
        "Average Response Size": ("mean", "response_body_size")
    }
    colx, coly = st.columns(2)
    with colx:
        label_choice = st.selectbox("Select X (Label)", list(label_options.keys()), index=0, key="custom_label")
    with coly:
        metric_choice = st.selectbox("Select Y (Metric)", list(metric_options.keys()), index=0, key="custom_metric")

    group_field = label_options[label_choice]
    agg_func, metric_field = metric_options[metric_choice]
    chart_data = None
    
    if agg_func == "count":
        chart_data = filtered[group_field].value_counts().rename_axis(label_choice).reset_index(name='Requests').head(15)
        fig_custom = go.Figure(data=[go.Bar(x=chart_data[label_choice], y=chart_data['Requests'], marker=dict(color=chart_data['Requests'], colorscale='Plasma', showscale=True), text=chart_data['Requests'], textposition='auto')])
        fig_custom.update_layout(xaxis_title=label_choice, yaxis_title='Number of Requests', hovermode='x unified', plot_bgcolor='rgba(240, 245, 250, 0.5)', paper_bgcolor='white', height=400)
        st.plotly_chart(fig_custom, use_container_width=True)
    elif agg_func == "mean" and metric_field:
        chart_data = filtered.groupby(group_field)[metric_field].mean().rename_axis(label_choice).reset_index(name=metric_choice).head(15)
        fig_custom = go.Figure(data=[go.Bar(x=chart_data[label_choice], y=chart_data[metric_choice], marker=dict(color=chart_data[metric_choice], colorscale='Inferno', showscale=True), text=chart_data[metric_choice].round(2), textposition='auto')])
        fig_custom.update_layout(xaxis_title=label_choice, yaxis_title=metric_choice, hovermode='x unified', plot_bgcolor='rgba(240, 245, 250, 0.5)', paper_bgcolor='white', height=400)
        st.plotly_chart(fig_custom, use_container_width=True)

    # --- LOG BOT (CHATBOT) ---
    st.markdown("---")
    st.subheader("Ask the Log Bot 🤖")
    with st.expander("Ask a question about your logs!"):
        st.markdown("**Examples you can ask:**")
        st.write("""
        - **Latency**: Average latency? | Min/max latency? | Latency variance?
        - **Cache**: Cache hit/miss %? | Cache performance?
        - **Datacenter**: Best datacenter? | Worst datacenter? | Datacenter performance?
        - **ISP**: Top ISP? | ISP with lowest latency? | List all ISPs?
        - **Status Codes**: Error rate? | 5xx errors? | 4xx errors?
        - **Performance**: Slowest city? | Fastest city? | City performance?
        - **Insights**: Top backend? | Most used endpoint? | Traffic summary?
        """)
        user_q = st.text_input("Type your question (or pick an example)")
        if user_q:
            answer = ""
            q = user_q.lower()
            
            # === LATENCY ANALYTICS ===
            if any(word in q for word in ["latency", "lag", "response time"]):
                if "average" in q or "avg" in q or "mean" in q or q.strip() == "latency":
                    avg_lat = filtered['time_elapsed'].mean()
                    answer = f"📊 Average request latency: **{avg_lat:.3f}s**"
                elif "min" in q:
                    min_lat = filtered['time_elapsed'].min()
                    answer = f"⚡ Minimum latency: **{min_lat:.3f}s**"
                elif "max" in q:
                    max_lat = filtered['time_elapsed'].max()
                    answer = f"🐌 Maximum latency: **{max_lat:.3f}s**"
                elif "variance" in q or "std" in q or "distribution" in q:
                    std_lat = filtered['time_elapsed'].std()
                    mean_lat = filtered['time_elapsed'].mean()
                    answer = f"📈 Latency Stats: Mean={mean_lat:.3f}s, StdDev={std_lat:.3f}s, Variance={std_lat**2:.6f}"
                elif "percentile" in q or "p99" in q or "p95" in q or "p90" in q:
                    p99 = filtered['time_elapsed'].quantile(0.99)
                    p95 = filtered['time_elapsed'].quantile(0.95)
                    p90 = filtered['time_elapsed'].quantile(0.90)
                    answer = f"📊 Latency Percentiles: P90={p90:.3f}s, P95={p95:.3f}s, P99={p99:.3f}s"
                else:
                    answer = "Try: 'Average latency', 'Min/max latency', 'Latency variance', 'Latency percentiles'"
            
            # === CACHE ANALYTICS ===
            elif "cache" in q or "hit" in q or "miss" in q:
                total = len(filtered)
                if "miss" in q or ("cache" in q and "miss" in q):
                    miss = (filtered['response_state'] == 'MISS').sum()
                    pct = (miss/total*100) if total else 0
                    answer = f"📊 Cache MISS Rate: **{pct:.1f}%** ({miss}/{total} requests)"
                elif "hit" in q or ("cache" in q and "hit" in q):
                    hit = (filtered['response_state'] == 'HIT').sum()
                    pct = (hit/total*100) if total else 0
                    answer = f"✅ Cache HIT Rate: **{pct:.1f}%** ({hit}/{total} requests)"
                elif "performance" in q or "summary" in q:
                    hit = (filtered['response_state'] == 'HIT').sum()
                    miss = (filtered['response_state'] == 'MISS').sum()
                    hit_pct = (hit/total*100) if total else 0
                    miss_pct = (miss/total*100) if total else 0
                    answer = f"📊 Cache Performance: HIT={hit_pct:.1f}% | MISS={miss_pct:.1f}%"
                else:
                    answer = "Try: 'Cache hit %?', 'Cache miss %?', 'Cache performance summary?'"
            
            # === DATACENTER ANALYTICS ===
            elif "datacenter" in q or "data center" in q or "pops" in q or "pop" in q:
                if "best" in q or "top" in q:
                    dc_perf = filtered.groupby('server_datacenter').agg(
                        requests=('client_ip', 'count'),
                        avg_latency=('time_elapsed', 'mean')
                    ).sort_values('requests', ascending=False)
                    best_dc = dc_perf.index[0]
                    best_count = dc_perf.iloc[0]['requests']
                    answer = f"🏆 Best datacenter by traffic: **{best_dc}** ({best_count} requests)"
                elif "worst" in q or "slowest" in q or "high latency" in q:
                    dc_perf = filtered.groupby('server_datacenter').agg(avg_latency=('time_elapsed', 'mean')).sort_values('avg_latency', ascending=False)
                    worst_dc = dc_perf.index[0]
                    worst_lat = dc_perf.iloc[0]['avg_latency']
                    answer = f"⚠️ Slowest datacenter: **{worst_dc}** (avg latency: {worst_lat:.3f}s)"
                elif "performance" in q or "all" in q or "list" in q:
                    dc_perf = filtered.groupby('server_datacenter').agg(
                        requests=('client_ip', 'count'),
                        avg_latency=('time_elapsed', 'mean'),
                        avg_rtt=('client_socket_tcpi_rtt', 'mean')
                    ).sort_values('requests', ascending=False)
                    answer = "📊 Datacenter Performance:\n" + "\n".join([f"**{dc}**: {int(row['requests'])} req | {row['avg_latency']:.3f}s latency | {row['avg_rtt']:.0f}ms RTT" for dc, row in dc_perf.iterrows()])
                else:
                    answer = "Try: 'Best datacenter?', 'Worst datacenter?', 'Datacenter performance summary?'"
            
            # === ISP ANALYTICS ===
            elif "isp" in q or "internet service" in q or "provider" in q or "as" in q:
                if "top" in q or "best" in q or ("most" in q and "request" in q):
                    top_isp = filtered['client_as_name'].value_counts().idxmax()
                    top_count = filtered['client_as_name'].value_counts().max()
                    answer = f"🏆 Top ISP by requests: **{top_isp}** ({top_count} requests)"
                elif "lowest latency" in q or "fastest" in q or ("best" in q and "latency" in q):
                    isp_perf = filtered.groupby('client_as_name').agg(avg_latency=('time_elapsed','mean'))
                    best_isp = isp_perf['avg_latency'].idxmin()
                    best_lat = isp_perf['avg_latency'].min()
                    answer = f"⚡ ISP with lowest latency: **{best_isp}** ({best_lat:.3f}s)"
                elif "lowest rtt" in q or "best rtt" in q:
                    isp_perf = filtered.groupby('client_as_name').agg(avg_rtt=('client_socket_tcpi_rtt','mean'))
                    best_isp = isp_perf['avg_rtt'].idxmin()
                    best_rtt = isp_perf['avg_rtt'].min()
                    answer = f"⚡ ISP with lowest RTT: **{best_isp}** ({best_rtt:.0f}ms)"
                elif "list" in q or "all" in q:
                    isps = filtered['client_as_name'].value_counts()
                    answer = "📊 ISPs and request counts:\n" + "\n".join([f"**{i}**: {c} requests" for i,c in isps.items()])
                elif "performance" in q:
                    isp_perf = filtered.groupby('client_as_name').agg(
                        requests=('client_ip', 'count'),
                        avg_latency=('time_elapsed', 'mean'),
                        avg_rtt=('client_socket_tcpi_rtt', 'mean')
                    ).sort_values('requests', ascending=False)
                    answer = "📊 ISP Performance Ranking:\n" + "\n".join([f"**{isp}**: {int(row['requests'])} req | {row['avg_latency']:.3f}s latency | {row['avg_rtt']:.0f}ms RTT" for isp, row in isp_perf.head(10).iterrows()])
                else:
                    answer = "Try: 'Top ISP?', 'ISP with lowest latency?', 'ISP performance?', 'List all ISPs?'"
            
            # === HTTP STATUS ANALYTICS ===
            elif "status" in q or "error" in q or "5xx" in q or "4xx" in q or "2xx" in q:
                if "5xx" in q or ("error" in q and "5" in q):
                    errors_5xx = (filtered['response_status'] >= 500).sum()
                    pct = (errors_5xx/len(filtered)*100) if len(filtered) else 0
                    answer = f"⚠️ 5xx Server Errors: **{errors_5xx}** ({pct:.2f}%)"
                elif "4xx" in q or ("error" in q and "4" in q):
                    errors_4xx = (filtered['response_status'] >= 400) & (filtered['response_status'] < 500)
                    errors_4xx = errors_4xx.sum()
                    pct = (errors_4xx/len(filtered)*100) if len(filtered) else 0
                    answer = f"⚠️ 4xx Client Errors: **{errors_4xx}** ({pct:.2f}%)"
                elif "2xx" in q or "success" in q:
                    success = (filtered['response_status'] >= 200) & (filtered['response_status'] < 300)
                    success = success.sum()
                    pct = (success/len(filtered)*100) if len(filtered) else 0
                    answer = f"✅ 2xx Success: **{success}** ({pct:.2f}%)"
                elif "error rate" in q or "errors" in q:
                    errors = (filtered['response_status'] >= 400).sum()
                    pct = (errors/len(filtered)*100) if len(filtered) else 0
                    answer = f"📊 Overall Error Rate: **{pct:.2f}%** ({errors}/{len(filtered)} requests)"
                elif "most common" in q or "top" in q:
                    top_status = filtered['response_status'].value_counts().idxmax()
                    top_count = filtered['response_status'].value_counts().max()
                    answer = f"📊 Most common HTTP status: **{top_status}** ({top_count} occurrences)"
                else:
                    answer = "Try: 'Error rate?', '5xx errors?', '4xx errors?', 'Most common status code?'"
            
            # === GEOGRAPHIC ANALYTICS ===
            elif "city" in q or "location" in q or "geo" in q:
                if "top" in q or "most" in q or "slowest" in q:
                    if "slowest" in q:
                        city_perf = filtered.groupby('geo_city').agg(avg_latency=('time_elapsed', 'mean')).sort_values('avg_latency', ascending=False)
                        top_city = city_perf.index[0]
                        top_lat = city_perf.iloc[0]['avg_latency']
                        answer = f"🐌 Slowest city: **{top_city}** (avg latency: {top_lat:.3f}s)"
                    elif "fastest" in q:
                        city_perf = filtered.groupby('geo_city').agg(avg_latency=('time_elapsed', 'mean')).sort_values('avg_latency', ascending=True)
                        top_city = city_perf.index[0]
                        top_lat = city_perf.iloc[0]['avg_latency']
                        answer = f"⚡ Fastest city: **{top_city}** (avg latency: {top_lat:.3f}s)"
                    else:
                        city_counts = filtered['geo_city'].value_counts()
                        top_city = city_counts.idxmax()
                        top_count = city_counts.max()
                        answer = f"📍 Top city by traffic: **{top_city}** ({top_count} requests)"
                elif "performance" in q or "all" in q or "list" in q:
                    city_perf = filtered.groupby('geo_city').agg(
                        requests=('client_ip', 'count'),
                        avg_latency=('time_elapsed', 'mean')
                    ).sort_values('requests', ascending=False)
                    answer = "📊 City Performance:\n" + "\n".join([f"**{city}**: {int(row['requests'])} req | {row['avg_latency']:.3f}s latency" for city, row in city_perf.head(10).iterrows()])
                else:
                    answer = "Try: 'Top city?', 'Slowest city?', 'Fastest city?', 'City performance?'"
            
            # === BACKEND ANALYTICS ===
            elif "backend" in q or "server" in q or "endpoint" in q:
                if "top" in q or "most" in q or "best" in q:
                    backend_perf = filtered.groupby('req.backend.name').agg(
                        requests=('client_ip', 'count'),
                        avg_latency=('time_elapsed', 'mean')
                    ).sort_values('requests', ascending=False)
                    top_backend = backend_perf.index[0]
                    top_count = backend_perf.iloc[0]['requests']
                    answer = f"🏆 Most used backend: **{top_backend}** ({int(top_count)} requests)"
                elif "performance" in q or "all" in q:
                    backend_perf = filtered.groupby('req.backend.name').agg(
                        requests=('client_ip', 'count'),
                        avg_latency=('time_elapsed', 'mean')
                    ).sort_values('requests', ascending=False)
                    answer = "📊 Backend Performance:\n" + "\n".join([f"**{b}**: {int(row['requests'])} req | {row['avg_latency']:.3f}s latency" for b, row in backend_perf.iterrows()])
                else:
                    answer = "Try: 'Top backend?', 'Backend performance?'"
            
            # === RTT ANALYTICS ===
            elif "rtt" in q or "round trip time" in q:
                if "average" in q or "avg" in q or "mean" in q or q.strip() == "rtt":
                    avg_rtt = filtered['client_socket_tcpi_rtt'].mean()
                    answer = f"📊 Average RTT: **{avg_rtt:.0f} ms**"
                elif "min" in q:
                    min_rtt = filtered['client_socket_tcpi_rtt'].min()
                    answer = f"⚡ Minimum RTT: **{min_rtt:.0f} ms**"
                elif "max" in q:
                    max_rtt = filtered['client_socket_tcpi_rtt'].max()
                    answer = f"🐌 Maximum RTT: **{max_rtt:.0f} ms**"
                else:
                    answer = "Try: 'Average RTT?', 'Min/max RTT?'"
            
            # === GENERAL STATS ===
            elif "summary" in q or "overview" in q or "stats" in q or "total" in q:
                total_reqs = len(filtered)
                unique_ips = filtered['client_ip'].nunique()
                unique_cities = filtered['geo_city'].nunique()
                unique_dcs = filtered['server_datacenter'].nunique()
                avg_lat = filtered['time_elapsed'].mean()
                cache_hit_rate = ((filtered['response_state'] == 'HIT').sum() / total_reqs * 100) if total_reqs else 0
                answer = f"""📊 **Data Summary:**
- Total Requests: **{total_reqs}**
- Unique IPs: **{unique_ips}**
- Cities: **{unique_cities}**
- Datacenters: **{unique_dcs}**
- Avg Latency: **{avg_lat:.3f}s**
- Cache Hit Rate: **{cache_hit_rate:.1f}%**"""
            
            else:
                answer = "🤔 Sorry, I couldn't understand that. Try asking about: **Latency**, **Cache**, **Datacenter**, **ISP**, **Status Codes**, **Cities**, or **Backend Performance**"
            
            st.info(answer)

    # --- RAW LOG TABLE ---
    st.markdown("---")
    st.subheader("Raw Log Table (Sample)")
    st.dataframe(filtered.head(30))

if __name__ == "__main__":
    main()
