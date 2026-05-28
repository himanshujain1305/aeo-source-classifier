import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="AEO Source Classifier",
    page_icon="🔎",
    layout="wide"
)

SAMPLE_PATH = Path("sample_data/customgpt_source_inventory.csv")

SOURCE_TYPE_LABELS = {
    "vendor_blog": "Vendor blog",
    "vendor_product_page": "Vendor product page",
    "comparison_list": "Comparison list",
    "video": "Video",
    "vendor_explainer": "Vendor explainer",
    "official_help_doc": "Official help doc",
    "community_thread": "Community thread",
    "professional_network": "Professional network",
    "implementation_guide": "Implementation guide",
}

CONTENT_SHAPE_LABELS = {
    "knowledge_base_chatbot": "Knowledge-base chatbot",
    "enterprise_search": "Enterprise search",
    "rag_internal_docs": "RAG / internal docs",
    "internal_knowledge_search": "Internal knowledge search",
    "enterprise_chatbot": "Enterprise chatbot",
}

st.title("🔎 AEO Source Classifier + Visibility Tracker")

st.markdown(
    """
    Analyze AI-search cited sources for a target query.  
    This tool helps identify which source types, content shapes, and domains answer engines repeatedly cite.
    """
)

@st.cache_data
def load_csv(file):
    return pd.read_csv(file, dtype=str)

def clean_columns(df):
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

def ensure_required_columns(df):
    required = [
        "date",
        "query",
        "source_title",
        "source_url",
        "domain",
        "source_type",
        "content_shape",
        "buyer_intent_angle",
        "repeated_or_once",
        "notes",
    ]
    return [col for col in required if col not in df.columns]

def label_values(series, mapping):
    return series.map(mapping).fillna(series)

def generate_recommendations(df):
    source_type_counts = df["source_type"].value_counts()
    content_shape_counts = df["content_shape"].value_counts()

    repeated_domains = (
        df[df["repeated_or_once"].astype(str).str.contains("repeated", case=False, na=False)]
        ["domain"]
        .value_counts()
    )

    top_source_type = source_type_counts.index[0] if not source_type_counts.empty else "unknown"
    top_content_shape = content_shape_counts.index[0] if not content_shape_counts.empty else "unknown"

    recommendations = []

    if "vendor_product_page" in source_type_counts.index:
        recommendations.append(
            "Build a dedicated owned product/use-case page. Persistent citations favored pages that directly matched the query intent."
        )

    if "vendor_blog" in source_type_counts.index:
        recommendations.append(
            "Create educational vendor-owned explainers that define the category while naturally connecting to the product."
        )

    if "knowledge_base_chatbot" in content_shape_counts.index:
        recommendations.append(
            "Prioritize a knowledge-base chatbot page with customer proof, citations, permissions, and internal-doc examples."
        )

    if "rag_internal_docs" in content_shape_counts.index:
        recommendations.append(
            "Add implementation-style content around RAG, internal docs, source-backed answers, permissions, freshness, and analytics."
        )

    if not repeated_domains.empty:
        recommendations.append(
            f"Study persistent domains like {', '.join(repeated_domains.head(3).index.astype(str))}. Repeated domains reveal what the answer engine may trust across reruns."
        )

    recommendations.append(
        "Do not optimize only for one citation. Optimize for repeated presence across a buyer-intent query cluster."
    )

    return top_source_type, top_content_shape, recommendations

st.sidebar.header("Data input")
use_sample = st.sidebar.checkbox("Use sample CustomGPT.ai dataset", value=True)
uploaded_file = st.sidebar.file_uploader("Or upload source inventory CSV", type=["csv"])

if uploaded_file is not None:
    df = load_csv(uploaded_file)
elif use_sample and SAMPLE_PATH.exists():
    df = load_csv(SAMPLE_PATH)
else:
    st.warning("Upload a CSV or add the sample dataset to sample_data/customgpt_source_inventory.csv")
    st.stop()

df = clean_columns(df)
missing_cols = ensure_required_columns(df)

if missing_cols:
    st.error(f"Missing required columns: {missing_cols}")
    st.stop()

df["date"] = df["date"].astype(str)

st.sidebar.divider()
st.sidebar.caption("Built for AEO / AI-search source analysis")

st.subheader("Executive summary")

total_citations = len(df)
unique_domains = df["domain"].nunique()
source_types = df["source_type"].nunique()
content_shapes = df["content_shape"].nunique()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total citations", total_citations)
col2.metric("Unique domains", unique_domains)
col3.metric("Source types", source_types)
col4.metric("Content shapes", content_shapes)

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Dashboard", "🔁 Persistence", "🧠 Recommendations", "📄 Data"]
)

with tab1:
    left, right = st.columns(2)

    with left:
        source_type_counts = df["source_type"].value_counts().reset_index()
        source_type_counts.columns = ["source_type", "count"]
        source_type_counts["source_type_label"] = label_values(
            source_type_counts["source_type"], SOURCE_TYPE_LABELS
        )

        fig = px.bar(
            source_type_counts,
            x="source_type_label",
            y="count",
            text="count",
            title="Citations by source type"
        )
        fig.update_layout(
            xaxis_title="",
            yaxis_title="Citations",
            xaxis_tickangle=-25,
            margin=dict(l=20, r=20, t=60, b=120),
            height=430
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        content_shape_counts = df["content_shape"].value_counts().reset_index()
        content_shape_counts.columns = ["content_shape", "count"]
        content_shape_counts["content_shape_label"] = label_values(
            content_shape_counts["content_shape"], CONTENT_SHAPE_LABELS
        )

        fig = px.bar(
            content_shape_counts,
            x="content_shape_label",
            y="count",
            text="count",
            title="Citations by content shape"
        )
        fig.update_layout(
            xaxis_title="",
            yaxis_title="Citations",
            xaxis_tickangle=-25,
            margin=dict(l=20, r=20, t=60, b=120),
            height=430
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top domains")
    domain_counts = df["domain"].value_counts().reset_index()
    domain_counts.columns = ["domain", "count"]
    st.dataframe(domain_counts.head(15), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Repeated / persistent sources")

    repeated_df = df[
        df["repeated_or_once"].astype(str).str.contains("repeated", case=False, na=False)
    ].copy()

    if repeated_df.empty:
        st.info("No repeated sources found.")
    else:
        display_cols = [
            "date",
            "source_title",
            "domain",
            "source_type",
            "content_shape",
            "repeated_or_once",
        ]
        st.dataframe(repeated_df[display_cols], use_container_width=True, hide_index=True)

    st.markdown(
        """
        **Interpretation:**  
        If the exact URLs change but the source shapes stay similar, the brand should not chase one-off mentions.
        The stronger strategy is to build the kind of owned and third-party assets the answer engine repeatedly trusts.
        """
    )

with tab3:
    top_source_type, top_content_shape, recommendations = generate_recommendations(df)

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"Most common source type: **{SOURCE_TYPE_LABELS.get(top_source_type, top_source_type)}**")

    with col2:
        st.info(f"Most common content shape: **{CONTENT_SHAPE_LABELS.get(top_content_shape, top_content_shape)}**")

    st.markdown("### Recommended next moves")
    for rec in recommendations:
        st.markdown(f"- {rec}")

    action_plan = f"""
# AEO Action Plan

## Diagnosis
The cited source pool shows that answer engines are rewarding **{SOURCE_TYPE_LABELS.get(top_source_type, top_source_type)}** and **{CONTENT_SHAPE_LABELS.get(top_content_shape, top_content_shape)}** content most often.

## Recommended next move
Build query-shaped owned content that matches the source patterns already appearing in the citation pool.

## Action items
{chr(10).join([f"- {rec}" for rec in recommendations])}
"""

    st.download_button(
        label="Download markdown action plan",
        data=action_plan,
        file_name="aeo_action_plan.md",
        mime="text/markdown"
    )

with tab4:
    st.subheader("Dataset preview")
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download cleaned CSV",
        data=csv,
        file_name="aeo_source_inventory_cleaned.csv",
        mime="text/csv"
    )

st.caption("Built by Himanshu Jain — AEO + AI Marketing Portfolio Project")
