"""
🚀 Batch Analytics Narrative Intelligence Dashboard
Advanced ML-Powered Geospatial & Sentiment Analysis Platform
- Batch Data Analysis (1000+ Articles)
- HDBSCAN Adaptive Clustering
- Sentence Transformers Embeddings  
- Real-Time Geospatial Analysis
- Advanced Temporal Lifecycle Tracking
- Interactive Network Graphs
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import warnings
import folium
from streamlit_folium import st_folium
import spacy
from sentence_transformers import SentenceTransformer
import hdbscan
from sklearn.cluster import KMeans
import umap
import torch
import subprocess
import time
import sys
import os

warnings.filterwarnings('ignore')

# Configuration
ES_URL = "http://localhost:9200"
ES_INDEX = "news_articles_batch" # Batch index

# ============= HELPER FUNCTIONS =============

@st.cache_resource
def load_ml_models():
    """Load all ML models once and cache them"""
    try:
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        nlp = spacy.load('en_core_web_sm')
        return embedder, nlp
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None, None

def get_elasticsearch_data(size=1000):
    """Fetch data from Elasticsearch"""
    try:
        query = {
            "size": size,
            "sort": [{"published_at": {"order": "desc"}}], # Sort by publication date
            "query": {"match_all": {}}
        }
        response = requests.get(f"{ES_URL}/{ES_INDEX}/_search", json=query, timeout=10)
        if response.status_code == 200:
            hits = response.json()['hits']['hits']
            data = [hit['_source'] for hit in hits]
            df = pd.DataFrame(data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['published_at'], errors='coerce')
                # Ensure entities/locations are lists (ES can sometimes return single values)
                for col in ['entities', 'locations']:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: x if isinstance(x, list) else ([x] if x else []))
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Elasticsearch error: {e}")
        return pd.DataFrame()

# ============= VISUALIZATION FUNCTIONS (Copied & Adapted) =============
# ... (Reusing logic from original dashboard but streamlined) ...

def create_cluster_scatter_plot(embeddings_2d, cluster_labels, df_clustered):
    if embeddings_2d is None or cluster_labels is None: return None
    plot_df = pd.DataFrame({
        'x': embeddings_2d[:, 0], 'y': embeddings_2d[:, 1],
        'cluster': cluster_labels,
        'title': df_clustered['title'].values[:len(embeddings_2d)]
    })
    fig = px.scatter(
        plot_df, x='x', y='y', color='cluster', hover_data=['title'],
        title='Narrative Clusters (UMAP Projection)',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(template='plotly_white', height=500)
    return fig

def create_location_map(df):
    """Create map from dataframe locations"""
    location_coords = {
        'Mumbai': (19.07, 72.87), 'Delhi': (28.70, 77.10), 'Bengaluru': (12.97, 77.59),
        'Hyderabad': (17.38, 78.47), 'Chennai': (13.08, 80.27), 'Kolkata': (22.57, 88.36),
        'Pune': (18.52, 73.85), 'Ahmedabad': (23.02, 72.57),
        'India': (20.59, 78.96)
    }
    
    # Count locations
    all_locs = [loc for sublist in df['locations'] for loc in sublist]
    loc_counts = pd.Series(all_locs).value_counts()
    
    m = folium.Map(location=[20.59, 78.96], zoom_start=4, tiles='CartoDB positron')
    
    for loc, count in loc_counts.items():
        if loc in location_coords:
            folium.CircleMarker(
                location=location_coords[loc],
                radius=min(count, 30), # Scale radius
                popup=f"{loc}: {count} articles",
                color='#667eea', fill=True, fillOpacity=0.6
            ).add_to(m)
    return m

# ============= MAIN DASHBOARD =============

st.set_page_config(page_title="Batch Narrative Intelligence", page_icon="📊", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; }
    h1 { color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# Application Header
st.markdown("""
    <h1 style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    padding: 20px; border-radius: 10px; color: white;'>
    📊 Batch Narrative Intelligence Platform
    </h1>
""", unsafe_allow_html=True)

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Simulation Controls")
    
    if st.button("🔄 Run Batch Simulation", help="Generates 1000 new articles and analyzes them."):
        with st.status("🚀 Running Simulation...", expanded=True) as status:
            st.write("1️⃣ Generating Synthetic Data...")
            # Run the generator script
            try:
                # Use sys.executable to ensure we use the same python environment
                script_path = os.path.join(os.path.dirname(__file__), "generate_batch_data.py")
                cmd = [sys.executable, script_path, "--count", "1000"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                st.write("✅ Generation Complete!")
                st.code(result.stdout)
                
                st.write("2️⃣ Refreshing Dashboard Data...")
                time.sleep(1) # Give ES a moment to index
                st.cache_data.clear() # Clear cache to fetch new data
                status.update(label="✅ Simulation Complete!", state="complete", expanded=False)
                st.rerun() # Rerun to load new data
                
            except subprocess.CalledProcessError as e:
                st.error(f"❌ Generation Failed: {e.stderr}")
                status.update(label="❌ Failed", state="error")
    
    st.markdown("---")
    st.info("ℹ️ This dashboard analyzes a static batch of 1,000 synthetic articles. Click 'Run Batch Simulation' to regenerate the dataset.")

# Load Models
embedder, nlp = load_ml_models()

# Fetch Data
with st.spinner("Loading Analyzed Data..."):
    df = get_elasticsearch_data(size=1500)

if df.empty:
    st.warning("⚠️ No data found. Please click 'Run Batch Simulation' in the sidebar.")
else:
    # --- Top Metrics ---
    st.markdown("### 📈 Executive Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Articles", len(df))
    with col2: st.metric("Avg Sentiment", f"{df['sentiment_score'].mean():.2f}")
    with col3: st.metric("Factual Articles", len(df[df['factual_density'] > 0.5]))
    with col4: st.metric("Clickbait Detected", len(df[df['sensationalism_score'] > 0.6]), delta_color="inverse")

    # --- Maps & Locations ---
    st.markdown("### 🗺️ Geographic & Temporal Analysis")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Narrative Hotspots")
        map_chart = create_location_map(df)
        st_folium(map_chart, height=400, use_container_width=True)
    with c2:
        st.subheader("Publishing Timeline")
        daily_counts = df.set_index('timestamp')['id'].resample('D').count()
        st.line_chart(daily_counts)

    # --- Clustering & Topics ---
    st.markdown("### 🧩 Narrative Clustering (Semantic Analysis)")
    
    # Generate/Retrieve Embeddings (They are in ES, but we need them as numpy array for UMAP)
    # Note: Retrieving dense vectors from ES source is easy
    if 'embedding_vector' in df.columns and not df['embedding_vector'].isnull().all():
        embeddings = np.stack(df['embedding_vector'].values)
        
        # UMAP Reduction
        reducer = umap.UMAP(n_components=2, random_state=42)
        embeddings_2d = reducer.fit_transform(embeddings)
        
        # KMeans
        kmeans = KMeans(n_clusters=6, random_state=42)
        clusters = kmeans.fit_predict(embeddings)
        
        fig_clusters = create_cluster_scatter_plot(embeddings_2d, clusters, df)
        st.plotly_chart(fig_clusters, use_container_width=True)
    else:
        st.info("Generating embeddings for visualization...")
        # Fallback if no embeddings (shouldn't happen with new generator)
        embeddings = embedder.encode(df['content'].tolist())
        reducer = umap.UMAP(n_components=2)
        embeddings_2d = reducer.fit_transform(embeddings)
        kmeans = KMeans(n_clusters=6)
        clusters = kmeans.fit_predict(embeddings)
        fig_clusters = create_cluster_scatter_plot(embeddings_2d, clusters, df)
        st.plotly_chart(fig_clusters, use_container_width=True)

    # --- Data Grid ---
    st.markdown("### 📝 Detailed Articles")
    st.dataframe(
        df[['timestamp', 'title', 'category', 'sentiment', 'sensationalism_score']],
        use_container_width=True
    )
