"""
Talking Rabbitt — MVP
Conversational AI for Instant Business Insights
Upload a CSV, ask questions in plain English, get text answers + charts.
"""

import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from openai import OpenAI
import json
import re

# ─────────────────────────────────────────────
# PAGE CONFIG & THEME
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Talking Rabbitt 🐇",
    page_icon="🐇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS — dark brown text, light-blue background
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #D6EAF8;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #AED6F1;
    }
    /* All text dark brown */
    html, body, [class*="css"], .stMarkdown, .stText, label,
    .stSelectbox label, .stTextInput label, .stTextArea label {
        color: black !important;
        font-family: 'Calibri', 'Segoe UI', sans-serif;
    }
    /* Headers */
    h1, h2, h3, h4 {
        color: #3B1F0E !important;
        font-family: Georgia, serif;
    }
    /* Chat bubble — user */
    .user-bubble {
        background-color: #B85042;
        color: #FFFFFF !important;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0 8px 15%;
        font-size: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.12);
    }
    /* Chat bubble — assistant */
    .assistant-bubble {
        background-color: #FFFFFF;
        color: #3B1F0E !important;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 15% 8px 0;
        font-size: 14px;
        border: 1.5px solid #AED6F1;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    /* Input box */
    .stTextInput > div > div > input, .stTextArea textarea {
        background-color: #FFFFFF;
        color: #3B1F0E !important;
        border: 1.5px solid #7A9E7E;
        border-radius: 8px;
    }
    /* Buttons */
    .stButton > button {
        background-color: #B85042;
        color: #FFFFFF !important;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 8px 20px;
    }
    .stButton > button:hover {
        background-color: #7A4F3A;
    }
    /* Data table */
    .stDataFrame {
        border: 1px solid #AED6F1;
        border-radius: 8px;
    }
    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #AED6F1;
        border-radius: 8px;
        padding: 8px;
    }
    /* Expander */
    .streamlit-expanderHeader {
        color: #3B1F0E !important;
        background-color: #EBF5FB;
    }
    /* Success / info boxes */
    .stSuccess { background-color: #D5F5E3; color: #1E8449 !important; }
    .stInfo    { background-color: #EBF5FB; color: #1A5276 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# OPENAI CLIENT (secure key from env/secrets)
# ─────────────────────────────────────────────
@st.cache_resource
def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


# ─────────────────────────────────────────────
# SAMPLE DATA GENERATOR
# ─────────────────────────────────────────────
def get_sample_data() -> pd.DataFrame:
    import numpy as np
    np.random.seed(42)
    regions  = ["North", "South", "East", "West", "Central"]
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    products = ["AlphaWidget", "BetaGadget", "GammaKit", "DeltaTool"]

    rows = []
    for region in regions:
        for quarter in quarters:
            for product in products:
                revenue    = int(np.random.normal(120_000, 30_000))
                units_sold = int(np.random.normal(850, 200))
                rows.append({
                    "region": region,
                    "quarter": quarter,
                    "product": product,
                    "revenue": max(revenue, 10_000),
                    "units_sold": max(units_sold, 50),
                })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# LLM QUERY ENGINE
# ─────────────────────────────────────────────
def build_system_prompt(df: pd.DataFrame) -> str:
    sample = df.head(5).to_csv(index=False)
    schema = df.dtypes.to_string()
    return f"""You are Talking Rabbitt — a concise, friendly data analyst AI.

The user has uploaded a CSV with the following schema:
{schema}

Sample rows:
{sample}

The full dataset has {len(df)} rows.

When answering:
1. Give a SHORT, clear natural-language answer (2-4 sentences max).
2. Then output a JSON block (fenced with ```json ... ```) describing a chart to visualize the answer.

The JSON must follow EXACTLY this format:
{{
  "chart_type": "bar" | "line" | "pie",
  "title": "Chart title",
  "x_label": "X axis label",
  "y_label": "Y axis label",
  "data": {{
    "labels": ["label1", "label2", ...],
    "values": [num1, num2, ...]
  }}
}}

If no chart is appropriate (e.g. the question is just definitional), set chart_type to null and omit data.
Never hallucinate numbers — only use data that can be derived from the schema and sample provided.
Keep your tone warm, insightful, and non-technical.
"""


def query_llm(client, df: pd.DataFrame, question: str) -> dict:
    """Send question to OpenAI and return {text, chart_json}"""
    system_prompt = build_system_prompt(df)

    # Build a mini-aggregated summary for better accuracy
    summary_lines = []
    if "quarter" in df.columns and "revenue" in df.columns:
        qr = df.groupby("quarter")["revenue"].sum().to_dict()
        summary_lines.append("Revenue by quarter: " + str(qr))
    if "region" in df.columns and "revenue" in df.columns:
        rr = df.groupby("region")["revenue"].sum().to_dict()
        summary_lines.append("Revenue by region: " + str(rr))
    if "product" in df.columns and "units_sold" in df.columns:
        pu = df.groupby("product")["units_sold"].sum().to_dict()
        summary_lines.append("Units sold by product: " + str(pu))
    if "quarter" in df.columns and "product" in df.columns and "units_sold" in df.columns:
        q3 = df[df["quarter"] == "Q3"].groupby("product")["units_sold"].sum().to_dict()
        summary_lines.append("Q3 units by product: " + str(q3))

    augmented_q = question
    if summary_lines:
        augmented_q = question + "\n\nHere is pre-computed data to use:\n" + "\n".join(summary_lines)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": augmented_q},
        ],
        temperature=0.2,
        max_tokens=800,
    )

    content = response.choices[0].message.content

    # Extract text + JSON
    json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    chart_json = None
    text_answer = content

    if json_match:
        try:
            chart_json = json.loads(json_match.group(1))
        except Exception:
            chart_json = None
        text_answer = content[:json_match.start()].strip()

    return {"text": text_answer, "chart": chart_json}


# ─────────────────────────────────────────────
# CHART RENDERER
# ─────────────────────────────────────────────
BRAND_COLORS = ["#B85042", "#7A4F3A", "#7A9E7E", "#C9883E", "#3B1F0E",
                "#AED6F1", "#EDD5C0", "#2C5F2D", "#F5EFE6", "#065A82"]

def render_chart(chart_json: dict):
    if not chart_json or chart_json.get("chart_type") is None:
        return
    if "data" not in chart_json:
        return

    labels = chart_json["data"].get("labels", [])
    values = chart_json["data"].get("values", [])
    if not labels or not values:
        return

    fig, ax = plt.subplots(figsize=(9, 4.2))
    fig.patch.set_facecolor("#D6EAF8")
    ax.set_facecolor("#EBF5FB")

    ctype = chart_json.get("chart_type", "bar")

    if ctype == "bar":
        colors = BRAND_COLORS[:len(labels)]
        bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=0.8)
        ax.bar_label(bars, fmt=lambda v: f"${v/1000:.0f}K" if max(values) > 10000 else str(int(v)),
                     padding=4, color="#3B1F0E", fontsize=10, fontweight="bold")
        ax.set_xlabel(chart_json.get("x_label", ""), color="#3B1F0E", fontsize=11)
        ax.set_ylabel(chart_json.get("y_label", ""), color="#3B1F0E", fontsize=11)
        plt.xticks(rotation=15 if len(labels) > 5 else 0, color="#3B1F0E", fontsize=10)
        plt.yticks(color="#3B1F0E", fontsize=9)

    elif ctype == "line":
        ax.plot(labels, values, color="#B85042", linewidth=2.5, marker="o",
                markersize=7, markerfacecolor="#C9883E", markeredgewidth=1.5, markeredgecolor="#3B1F0E")
        ax.fill_between(range(len(labels)), values, alpha=0.12, color="#B85042")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=15 if len(labels) > 5 else 0, color="#3B1F0E", fontsize=10)
        ax.set_xlabel(chart_json.get("x_label", ""), color="#3B1F0E", fontsize=11)
        ax.set_ylabel(chart_json.get("y_label", ""), color="#3B1F0E", fontsize=11)
        plt.yticks(color="#3B1F0E", fontsize=9)

    elif ctype == "pie":
        wedge_colors = BRAND_COLORS[:len(labels)]
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=wedge_colors,
            autopct="%1.1f%%", startangle=140,
            wedgeprops=dict(edgecolor="white", linewidth=1.5)
        )
        for t in texts:
            t.set_color("#3B1F0E")
            t.set_fontsize(10)
        for at in autotexts:
            at.set_color("white")
            at.set_fontsize(9)
            at.set_fontweight("bold")

    ax.set_title(chart_json.get("title", ""), color="#3B1F0E", fontsize=13,
                 fontweight="bold", fontfamily="Georgia", pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#AED6F1")
    ax.spines["bottom"].set_color("#AED6F1")
    ax.yaxis.grid(True, color="#AED6F1", linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ─────────────────────────────────────────────
# DEMO QUERY HANDLER (no API key required)
# ─────────────────────────────────────────────
def handle_demo_query(df: pd.DataFrame, question: str) -> dict:
    """Rule-based fallback for demo mode (no API key needed)."""
    q = question.lower()

    if "highest revenue" in q and "q1" in q:
        subset = df[df["quarter"] == "Q1"].groupby("region")["revenue"].sum()
        top = subset.idxmax()
        val = subset.max()
        return {
            "text": f"🏆 **{top}** had the highest revenue in Q1 with **${val:,.0f}**. This region outperformed all others in Q1, driven by strong AlphaWidget and GammaKit sales.",
            "chart": {
                "chart_type": "bar",
                "title": "Q1 Revenue by Region",
                "x_label": "Region",
                "y_label": "Revenue ($)",
                "data": {
                    "labels": list(subset.index),
                    "values": [int(v) for v in subset.values],
                }
            }
        }

    elif ("most units" in q or "most sold" in q) and "q3" in q:
        subset = df[df["quarter"] == "Q3"].groupby("product")["units_sold"].sum()
        top = subset.idxmax()
        val = subset.max()
        return {
            "text": f"🎯 **{top}** sold the most units in Q3 with **{val:,} units**. It significantly outpaced other products during the summer quarter.",
            "chart": {
                "chart_type": "bar",
                "title": "Q3 Units Sold by Product",
                "x_label": "Product",
                "y_label": "Units Sold",
                "data": {
                    "labels": list(subset.index),
                    "values": [int(v) for v in subset.values],
                }
            }
        }

    elif "revenue trend" in q or "trends by quarter" in q:
        subset = df.groupby("quarter")["revenue"].sum().reindex(["Q1","Q2","Q3","Q4"])
        return {
            "text": f"📈 Revenue shows a steady upward trend across the year, growing from **${subset['Q1']:,.0f}** in Q1 to **${subset['Q4']:,.0f}** in Q4 — a strong indicator of accelerating market traction.",
            "chart": {
                "chart_type": "line",
                "title": "Revenue Trend by Quarter",
                "x_label": "Quarter",
                "y_label": "Total Revenue ($)",
                "data": {
                    "labels": list(subset.index),
                    "values": [int(v) for v in subset.values],
                }
            }
        }

    elif "region" in q and "revenue" in q:
        subset = df.groupby("region")["revenue"].sum()
        return {
            "text": f"💡 Revenue is fairly distributed across regions, with the highest performer at **${subset.max():,.0f}** and lowest at **${subset.min():,.0f}**.",
            "chart": {
                "chart_type": "pie",
                "title": "Revenue Share by Region",
                "x_label": "",
                "y_label": "",
                "data": {
                    "labels": list(subset.index),
                    "values": [int(v) for v in subset.values],
                }
            }
        }

    else:
        # Generic fallback
        subset = df.groupby("quarter")["revenue"].sum().reindex(["Q1","Q2","Q3","Q4"])
        return {
            "text": "I couldn't find a specific answer for that query in demo mode. Here's the overall revenue by quarter. Add your OpenAI API key in the sidebar for full natural-language support!",
            "chart": {
                "chart_type": "bar",
                "title": "Revenue by Quarter (Overview)",
                "x_label": "Quarter",
                "y_label": "Revenue ($)",
                "data": {
                    "labels": list(subset.index),
                    "values": [int(v) for v in subset.values],
                }
            }
        }


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🐇 Talking Rabbitt")
    st.markdown("*Conversational AI for Instant Business Insights*")
    st.divider()

    # API Key input
    st.markdown("### 🔐 OpenAI API Key")
    api_key_input = st.text_input(
        "Paste your key (stored in session only)",
        type="password",
        placeholder="sk-...",
        help="Your key is never stored permanently. It lives only in this browser session."
    )
    if api_key_input:
        os.environ["OPENAI_API_KEY"] = api_key_input
        st.success("✅ Key set for this session")

    st.divider()
    st.markdown("### 📂 Upload Data")
    uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])

    use_sample = st.checkbox("Use sample sales data", value=True)

    st.divider()
    st.markdown("### 💡 Demo Queries")
    demo_queries = [
        "Which region had the highest revenue in Q1?",
        "Which product sold the most units in Q3?",
        "Show me revenue trends by quarter.",
        "Compare revenue share by region.",
    ]
    for dq in demo_queries:
        if st.button(dq, key=f"dq_{dq[:20]}"):
            st.session_state["pending_query"] = dq

    st.divider()
    st.caption("v0.1.0 · Seed Stage · talkingrabbitt.io")


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
df = None
data_source = None

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        data_source = f"📄 {uploaded_file.name}"
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
elif use_sample:
    df = get_sample_data()
    data_source = "🎲 Sample Sales Dataset (5 regions × 4 quarters × 4 products)"


# ─────────────────────────────────────────────
# MAIN INTERFACE
# ─────────────────────────────────────────────
st.markdown("# 🐇 Talking Rabbitt")
st.markdown("### *Upload Data. Ask Questions. Get Answers.*")

if df is None:
    st.info("👈 Upload a CSV file or enable the sample dataset in the sidebar to get started.")
    st.stop()

# Data summary row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows", f"{len(df):,}")
col2.metric("Columns", len(df.columns))
col3.metric("Data Source", "Uploaded" if uploaded_file else "Sample")
col4.metric("Mode", "AI" if os.environ.get("OPENAI_API_KEY") else "Demo")

with st.expander(f"📊 Data Preview — {data_source}", expanded=False):
    st.dataframe(df.head(10), use_container_width=True)
    st.caption(f"Showing first 10 of {len(df):,} rows · Columns: {', '.join(df.columns.tolist())}")

st.divider()

# ── Chat history ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Render existing messages
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-bubble">🐇 {msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("chart"):
            render_chart(msg["chart"])

# ── Input row ─────────────────────────────────
st.markdown("### 💬 Ask your data anything")
input_col, btn_col = st.columns([5, 1])

with input_col:
    user_query = st.text_input(
        "Your question",
        key="query_input",
        value=st.session_state.pop("pending_query", ""),
        placeholder="e.g. Which region had the highest revenue in Q1?",
        label_visibility="collapsed",
    )

with btn_col:
    ask_btn = st.button("Ask 🐇", use_container_width=True)

# ── Process query ──────────────────────────────
if ask_btn:
    query_to_run = user_query.strip()
    if not query_to_run:
        st.warning("Please enter a question first.")
    else:
        st.session_state["messages"].append({"role": "user", "content": query_to_run})
        st.markdown(f'<div class="user-bubble">👤 {query_to_run}</div>', unsafe_allow_html=True)

        with st.spinner("🐇 Rabbitt is thinking…"):
            client = get_openai_client()

            if client:
                result = query_llm(client, df, query_to_run)
            else:
                result = handle_demo_query(df, query_to_run)
                if os.environ.get("OPENAI_API_KEY") is None:
                    result["text"] += "\n\n*💡 Demo mode active — add your OpenAI API key in the sidebar for full AI capabilities.*"

        st.session_state["messages"].append({
            "role": "assistant",
            "content": result["text"],
            "chart": result.get("chart"),
        })
        st.rerun()

# Clear chat
if st.session_state.get("messages"):
    if st.button("🗑️ Clear chat history"):
        st.session_state["messages"] = []
        st.rerun()