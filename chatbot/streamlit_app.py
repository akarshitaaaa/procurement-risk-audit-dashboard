import os
from pathlib import Path

import pandas as pd
import chromadb
import streamlit as st
from chromadb.utils import embedding_functions
from groq import Groq

BASE_DIR = Path(__file__).parent
COLLECTION_NAME = "procurement_risk"
GROQ_MODEL = "openai/gpt-oss-120b"
TOP_K = 5

CSV_FILES = [
    "1_vendor_concentration.csv",
    "8_defect_rate_by_supplier.csv",
    "10_delivery_delay_by_supplier.csv",
    "2_price_variance.csv",
    "3_maverick_noncompliant.csv",
    "5_split_po_pattern.csv",
]

SYSTEM_PROMPT = (
    "You are a procurement risk analysis assistant. Answer the user's question "
    "using ONLY the information contained in the provided context chunks. "
    "If the context does not contain enough information to answer, say so clearly "
    "instead of guessing. Do not invent suppliers, numbers, or facts that are not "
    "present in the context."
)


def load_csv(name):
    return pd.read_csv(BASE_DIR / name)


def row_to_text(source, row):
    if source == "1_vendor_concentration.csv":
        return (
            f"Vendor concentration: {row['Supplier']} accounts for "
            f"{row['pct_of_total_spend']}% of total procurement spend, "
            f"totaling ${row['total_spend']:,.2f}."
        )
    if source == "8_defect_rate_by_supplier.csv":
        return (
            f"Defect rate: {row['Supplier']} had {row['total_defective_units']} "
            f"defective units out of {row['total_quantity']} total units, "
            f"a defect rate of {row['defect_rate_pct']}%."
        )
    if source == "10_delivery_delay_by_supplier.csv":
        return (
            f"Delivery performance: {row['Supplier']} averaged "
            f"{row['avg_delivery_days']} days delivery time across "
            f"{row['delivered_po_count']} delivered purchase orders."
        )
    if source == "2_price_variance.csv":
        return (
            f"Price variance: PO {row['PO_ID']} from {row['Supplier']} for "
            f"{row['Item_Category']} was priced at ${row['Unit_Price']} per unit, "
            f"{row['pct_above_avg']}% above the category average price of "
            f"${row['avg_price']:.2f}."
        )
    if source == "3_maverick_noncompliant.csv":
        return (
            f"Maverick/non-compliant purchase: PO {row['PO_ID']} from "
            f"{row['Supplier']} for {row['Item_Category']}, quantity "
            f"{row['Quantity']}, negotiated price ${row['Negotiated_Price']}, "
            f"total PO value ${row['po_value']}, order status {row['Order_Status']}."
        )
    if source == "5_split_po_pattern.csv":
        return (
            f"Split PO pattern: {row['Supplier']} placed "
            f"{row['po_count_in_window']} purchase orders for "
            f"{row['Item_Category']} between {row['window_start']} and "
            f"{row['window_end']}, combined value ${row['combined_value']}, "
            f"suggesting possible order splitting to avoid approval thresholds."
        )
    raise ValueError(f"Unknown source file: {source}")


def build_summary_chunks():
    chunks = []

    conc_df = load_csv("1_vendor_concentration.csv")
    top_share = conc_df.loc[conc_df["pct_of_total_spend"].idxmax()]
    chunks.append(
        f"Vendor concentration summary: {top_share['Supplier']} has the highest "
        f"spend share at {top_share['pct_of_total_spend']}% of total procurement "
        f"spend. Overall vendor concentration is healthy, as no single vendor "
        f"exceeds approximately 22% of total spend."
    )

    defect_df = load_csv("8_defect_rate_by_supplier.csv")
    best_quality = defect_df.loc[defect_df["defect_rate_pct"].idxmin()]
    worst_quality = defect_df.loc[defect_df["defect_rate_pct"].idxmax()]
    chunks.append(
        f"Overall quality performance summary: {best_quality['Supplier']} has the "
        f"best (lowest) defect rate at {best_quality['defect_rate_pct']}%, while "
        f"{worst_quality['Supplier']} has the worst (highest) defect rate at "
        f"{worst_quality['defect_rate_pct']}%. {worst_quality['Supplier']} is the "
        f"top vendor risk concern."
    )

    delivery_df = load_csv("10_delivery_delay_by_supplier.csv")
    fastest = delivery_df.loc[delivery_df["avg_delivery_days"].idxmin()]
    slowest = delivery_df.loc[delivery_df["avg_delivery_days"].idxmax()]
    chunks.append(
        f"Overall delivery performance summary: {fastest['Supplier']} is the "
        f"fastest vendor on average, delivering in {fastest['avg_delivery_days']} "
        f"days, while {slowest['Supplier']} is the slowest, averaging "
        f"{slowest['avg_delivery_days']} days."
    )

    price_df = load_csv("2_price_variance.csv")
    chunks.append(
        f"Price variance summary: {len(price_df)} purchase orders were flagged "
        f"for significant price variance above the category average price."
    )

    maverick_df = load_csv("3_maverick_noncompliant.csv")
    chunks.append(
        f"Non-compliance summary: {len(maverick_df)} purchase orders were flagged "
        f"as maverick or non-compliant purchases."
    )

    split_df = load_csv("5_split_po_pattern.csv")
    chunks.append(
        f"Split PO summary: {len(split_df)} split purchase order clusters were "
        f"detected, where multiple purchase orders to the same vendor within a "
        f"short time window may indicate attempts to avoid approval thresholds."
    )

    chunks.append(
        f"Overall vendor recommendation: {worst_quality['Supplier']} should be "
        f"placed under formal review due to its high defect rate of "
        f"{worst_quality['defect_rate_pct']}%, making it the top quality risk "
        f"among all vendors."
    )

    return chunks


def build_chunks():
    chunks, ids = [], []
    for source in CSV_FILES:
        df = load_csv(source)
        for i, row in df.iterrows():
            chunks.append(row_to_text(source, row))
            ids.append(f"{source}::{i}")
    for i, chunk in enumerate(build_summary_chunks()):
        chunks.append(chunk)
        ids.append(f"summary::{i}")
    return chunks, ids


@st.cache_resource(show_spinner="Building the knowledge base...")
def get_collection():
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(
        COLLECTION_NAME,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
    )
    chunks, ids = build_chunks()
    collection.add(documents=chunks, ids=ids)
    return collection


@st.cache_resource
def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY is not set. Add it in the app's Secrets settings.")
        st.stop()
    return Groq(api_key=api_key)


def retrieve(collection, query, top_k=TOP_K):
    results = collection.query(query_texts=[query], n_results=top_k)
    return results["documents"][0]


def generate_answer(client, query, context_chunks):
    context = "\n".join(f"- {chunk}" for chunk in context_chunks)
    user_prompt = (
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the context above."
    )
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


st.set_page_config(page_title="Procurement Risk Analysis Chatbot", page_icon="📊")
st.title("Procurement Risk Analysis Chatbot")
st.caption(
    "Ask questions about vendor concentration, price variance, maverick spend, "
    "split POs, defect rates, and delivery delays."
)

collection = get_collection()
groq_client = get_groq_client()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about the procurement analysis"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving and analysing..."):
            chunks = retrieve(collection, prompt)
            if not chunks:
                answer = "No relevant procurement data was found for this question."
            else:
                answer = generate_answer(groq_client, prompt, chunks)
        st.markdown(answer)
        with st.expander("Retrieved context"):
            for chunk in chunks:
                st.markdown(f"- {chunk}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
