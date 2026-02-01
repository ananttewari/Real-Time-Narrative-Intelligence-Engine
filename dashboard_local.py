"""
🚀 Real-Time Narrative Intelligence Dashboard (Local Lite Mode)
Reads from local JSONL file instead of Elasticsearch to bypass Docker requirements.
"""

import streamlit as st
import pandas as pd
import json
import time
import os
import plotly.express as px
import spacy
from collections import Counter
import warnings

warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATA_FILE = os.path.join(DATA_DIR, 'live_feed.jsonl')

# Load simplified NLP model
@st.cache_resource
def load_nlp():
    try:
        return spacy.load('en_core_web_sm')
    except:
        return None

nlp = load_nlp()

def load_data():
    """Load data from local JSONL file"""
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()
    
    data = []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except: pass
    except Exception as e:
        st.error(f"Error reading file: {e}")
        
    if not data:
        return pd.DataFrame()
        
    df = pd.DataFrame(data)
    df['ingested_at'] = pd.to_datetime(df['ingested_at'])
    return df.sort_values('ingested_at', ascending=False)

# Page config
st.set_page_config(page_title="Narrative Intelligence (Local)", page_icon="🌐", layout="wide")

# Header
st.title("🌐 Real-Time Narrative Intelligence (Live Feed)")
st.caption("🚀 Running in No-Docker Mode • Reading from local live feed")

# Sidebar
with st.sidebar:
    st.header("Controls")
    auto_refresh = st.toggle("🔴 Auto-Refresh", value=True)
    if st.button("🔄 Refresh Now"):
        st.rerun()
    
    st.divider()
    st.info(f"Reading from:\n{DATA_FILE}")

# Main content
df = load_data()

if df.empty:
    st.warning("waiting for data... Run `python src/ingestion/local_producer.py`")
    if auto_refresh:
        time.sleep(2)
        st.rerun()
else:
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Articles", len(df))
    col2.metric("Latest Source", df.iloc[0]['source'])
    col3.metric("Last Update", df.iloc[0]['ingested_at'].strftime('%H:%M:%S'))

    # Live Feed
    st.subheader("📰 Live Ingestion Stream")
    for i, row in df.head(5).iterrows():
        with st.expander(f"{row['ingested_at'].strftime('%H:%M:%S')} | {row['source']} | {row['title']}"):
            st.write(row['description'])
            st.caption(f"Category: {row.get('category', 'General')}")

    # Analytics (Simple)
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📊 Source Distribution")
        source_counts = df['source'].value_counts()
        st.bar_chart(source_counts)

    with col_b:
        st.subheader("🏷️ Top Keywords")
        if nlp:
            text_blob = " ".join(df['title'].tolist())
            doc = nlp(text_blob)
            words = [token.text for token in doc if not token.is_stop and token.is_alpha]
            word_freq = Counter(words).most_common(10)
            st.bar_chart(pd.DataFrame(word_freq, columns=['word', 'count']).set_index('word'))
        else:
            st.warning("spaCy not loaded")

    if auto_refresh:
        time.sleep(5)
        st.rerun()
