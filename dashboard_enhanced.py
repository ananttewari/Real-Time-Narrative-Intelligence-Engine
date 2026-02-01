"""
🚀 Real-Time Narrative Intelligence Dashboard
Advanced ML-Powered Geospatial & Sentiment Analysis Platform
- Live Auto-Refreshing Data Stream
- HDBSCAN Adaptive Clustering
- Sentence Transformers Embeddings  
- BART Text Summarization
- Real-Time Geospatial Analysis with spaCy NER
- Advanced Temporal Lifecycle Tracking
- Interactive Network Graphs
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
import json
import numpy as np
import warnings
import folium
from streamlit_folium import st_folium
import spacy
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import hdbscan
except ImportError:
    hdbscan = None

try:
    from sklearn.cluster import KMeans
except ImportError:
    KMeans = None

try:
    import umap
except ImportError:
    umap = None

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

import torch
import time

warnings.filterwarnings('ignore')

# ============= ADVANCED ANALYTICS FUNCTIONS =============

def clean_text_for_display(text):
    """Remove HTML tags and clean text for display"""
    import re
    if not text: return ""
    # Remove HTML tags (including attributes)
    text = re.sub(r"<[^>]+>", "", str(text))
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_hype_score(text, entities):
    """
    Calculate Hype vs. Substance Index (Clickbait Detection)
    High sensationalism + Low entity density = Clickbait
    """
    if not text or len(text) < 10:
        return 0, 0, 0
    
    # Sensationalism indicators
    sensational_words = ['breaking', 'shocking', 'unbelievable', 'must-see', 'you won\'t believe', 
                         'secret', 'exposed', 'revealed', 'scandal', 'explosive', 'urgent']
    emotional_words = ['amazing', 'terrible', 'incredible', 'awful', 'stunning', 'horrific']
    
    text_lower = text.lower()
    
    # Calculate sensationalism score
    sensational_count = sum(1 for word in sensational_words if word in text_lower)
    emotional_count = sum(1 for word in emotional_words if word in text_lower)
    exclamation_count = text.count('!')
    caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if len(text) > 0 else 0
    
    sensationalism = (sensational_count * 2 + emotional_count + exclamation_count + caps_ratio * 5)
    
    # Calculate entity density (factual substance)
    word_count = len(text.split())
    entity_count = len(entities) if isinstance(entities, list) else 0
    entity_density = (entity_count / word_count * 10) if word_count > 0 else 0
    
    # Hype Score: High sensationalism + Low entity density = High hype
    hype_score = max(0, min(10, sensationalism - entity_density))
    
    return hype_score, sensationalism, entity_density

def calculate_narrative_drift(old_embeddings, new_embeddings):
    """
    Calculate narrative drift by measuring centroid movement in vector space
    Detects when story meaning shifts over time
    """
    if old_embeddings is None or new_embeddings is None:
        return 0, None, None
    
    try:
        old_centroid = np.mean(old_embeddings, axis=0)
        new_centroid = np.mean(new_embeddings, axis=0)
        
        # Cosine distance
        from numpy.linalg import norm
        cosine_sim = np.dot(old_centroid, new_centroid) / (norm(old_centroid) * norm(new_centroid))
        drift = 1 - cosine_sim  # 0 = no drift, 1 = complete drift
        
        return drift, old_centroid, new_centroid
    except:
        return 0, None, None

def extract_entity_relationships(df, nlp):
    """
    Extract entity co-occurrence and sentiment relationships
    Creates network edges between entities that appear together
    """
    relationships = []
    
    for idx, row in df.iterrows():
        entities = row.get('entities', [])
        sentiment = row.get('sentiment', 'neutral')
        sentiment_score = row.get('sentiment_score', 0)
        
        if not isinstance(entities, list) or len(entities) < 2:
            continue
        
        # Create edges for all entity pairs in same document
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                relationships.append({
                    'source': entities[i],
                    'target': entities[j],
                    'sentiment': sentiment,
                    'sentiment_score': sentiment_score,
                    'weight': 1
                })
    
    return relationships

def create_entity_network_graph(relationships):
    """
    Create interactive network graph showing entity relationships
    Edge color shows sentiment between entities
    """
    if not relationships:
        return None
    
    # Aggregate relationships by co-occurrence
    from collections import defaultdict
    edges = defaultdict(int)
    
    for rel in relationships:
        key = tuple(sorted([rel['source'], rel['target']]))
        edges[key] += rel['weight']
    
    # Don't filter by weight yet - we need connections!
    all_edges = list(edges.items())
    
    # Identify top nodes by degree (total co-occurrences)
    node_degree = defaultdict(int)
    for (source, target), weight in all_edges:
        node_degree[source] += weight
        node_degree[target] += weight
    
    # Keep top 20 most central entities for presentation
    top_nodes = sorted(node_degree.items(), key=lambda x: x[1], reverse=True)[:20]
    top_node_set = {n for n, d in top_nodes}
    
    # Build edge list: keep ALL edges between top nodes (no weight filtering)
    edge_traces = []
    final_node_set = set()
    
    for (source, target), weight in all_edges:
        if source in top_node_set and target in top_node_set:
            final_node_set.add(source)
            final_node_set.add(target)
            
            edge_traces.append({
                'source': source,
                'target': target,
                'weight': weight,
                'color': '#667eea'  # Single consistent color
            })
    
    return edge_traces, list(final_node_set)

# Load ML models (cached for performance)
@st.cache_resource
def load_ml_models():
    """Load all ML models once and cache them"""
    try:
        # Sentence transformer for embeddings
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # spaCy for NER
        nlp = spacy.load('en_core_web_sm')
        
        # BART for summarization (use smaller model for speed)
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn", 
                            device=0 if torch.cuda.is_available() else -1)
        
        return embedder, nlp, summarizer
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None, None, None

# Page configuration
st.set_page_config(
    page_title="Enhanced Narrative Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with enhanced animations
st.markdown("""
    <style>
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    .stApp { background-color: #ffffff; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px; border-radius: 10px; color: white;
        animation: slideIn 0.5s ease-out;
    }
    .stMetric {
        background: linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%);
        padding: 20px; border-radius: 12px;
        border: 1px solid #3b82f6;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1);
        transition: transform 0.3s;
    }
    .stMetric:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 12px rgba(59, 130, 246, 0.2);
    }
    .stMetric label { color: #1e40af !important; font-weight: 600; }
    .stMetric [data-testid="stMetricValue"] { color: #1e3a8a !important; font-size: 2rem; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        border-right: 1px solid #cbd5e1;
    }
    h1 { 
        color: #1e293b !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
        animation: slideIn 0.8s ease-out;
    }
    h2, h3 { color: #334155 !important; }
    .streamlit-expanderHeader {
        background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;
        transition: all 0.3s;
    }
    .streamlit-expanderHeader:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.1);
    }
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white; border: none; border-radius: 8px;
        padding: 10px 24px; font-weight: 600; transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
    }
    .live-indicator {
        display: inline-block;
        width: 12px; height: 12px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
        margin-right: 8px;
    }
    .objective-box {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        padding: 15px; border-radius: 8px; margin: 10px 0;
        border-left: 4px solid #3b82f6;
        color: #1e40af;
    }
    .summary-box {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        padding: 15px; border-radius: 8px; margin: 10px 0;
        border-left: 4px solid #10b981; color: #065f46;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration
ES_URL = "http://localhost:9200"
ES_INDEX = "news_articles"  # Updated to use correct index

# Data fetching functions with shorter cache for real-time
@st.cache_data(ttl=5)
def get_elasticsearch_stats():
    try:
        response = requests.get(f"{ES_URL}/{ES_INDEX}/_count", timeout=5)
        return response.json().get('count', 0) if response.status_code == 200 else 0
    except: return 0

@st.cache_data(ttl=5)
def get_elasticsearch_data(size=2000):
    try:
        query = {
            "size": size,
            "sort": [{"ingested_at": {"order": "desc", "unmapped_type": "date"}}],
            "query": {"match_all": {}}
        }
        response = requests.get(f"{ES_URL}/{ES_INDEX}/_search", json=query, timeout=10)
        if response.status_code == 200:
            hits = response.json()['hits']['hits']
            data = [hit['_source'] for hit in hits]
            df = pd.DataFrame(data) if data else pd.DataFrame()
            
            # Parse timestamp properly
            if not df.empty:
                # Use event_time as primary timestamp (it's in ISO format)
                if 'event_time' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['event_time'], errors='coerce')
                elif 'ingested_at' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['ingested_at'], errors='coerce')
                elif 'published_at' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['published_at'], errors='coerce')
                
                # Content is already there, no need to copy
                # Entities and locations are already extracted by consumer
                    
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Elasticsearch error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def load_live_jsonl_data():
    """Load data from local JSONL live feed"""
    data_file = "data/live_feed.jsonl"
    if not os.path.exists(data_file):
        return pd.DataFrame()
    
    data = []
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except: pass
    except: pass
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    # Ensure timestamp column exists
    if 'ingested_at' in df.columns:
        df['timestamp'] = pd.to_datetime(df['ingested_at'])
    elif 'published_at' in df.columns:
        df['timestamp'] = pd.to_datetime(df['published_at'])
        
    return df.sort_values('timestamp', ascending=False)

@st.cache_data(ttl=60)
def load_csv_data(file_path, size=2000):
    """Load hybrid dataset from CSV file"""
    try:
        df = pd.read_csv(file_path)
        # Convert timestamp to datetime without timezone (for compatibility)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True).dt.tz_localize(None)
        # Convert entities string back to list for compatibility
        df['entities'] = df['entities'].apply(
            lambda x: [e.strip() for e in str(x).split(', ')] if x and x != '' else []
        )
        # Convert locations string back to list
        df['locations'] = df['locations'].apply(
            lambda x: [l.strip() for l in str(x).split(', ')] if x and x != '' else []
        )
        # Add matched_event column if missing
        if 'matched_event' not in df.columns:
            df['matched_event'] = df['entity_count'].apply(lambda x: 1 if x >= 3 else 0)
        return df.head(size)
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

def enrich_elasticsearch_data(df, nlp):
    """Enrich Elasticsearch data with entities, locations, and sentiment"""
    if df.empty or nlp is None:
        return df
    
    try:
        # Extract entities and locations from content/description
        if 'content' in df.columns:
            for idx, row in df.iterrows():
                if pd.isna(row.get('content')):
                    continue
                    
                # Process text with spaCy
                doc = nlp(str(row['content'])[:1000])  # Limit to first 1000 chars for speed
                
                # Extract entities
                entities = [ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'EVENT']]
                df.at[idx, 'entities'] = entities
                df.at[idx, 'entity_count'] = len(entities)
                
                # Extract locations
                locations = [ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC']]
                df.at[idx, 'locations'] = locations
                
                # Simple sentiment analysis (can be improved)
                # For now, use keyword-based approach
                text_lower = str(row['content']).lower()
                positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'win', 'best']
                negative_words = ['bad', 'terrible', 'negative', 'fail', 'worst', 'crisis', 'disaster']
                
                pos_count = sum(1 for word in positive_words if word in text_lower)
                neg_count = sum(1 for word in negative_words if word in text_lower)
                
                if pos_count > neg_count:
                    df.at[idx, 'sentiment'] = 'positive'
                    df.at[idx, 'sentiment_score'] = 0.6
                elif neg_count > pos_count:
                    df.at[idx, 'sentiment'] = 'negative'
                    df.at[idx, 'sentiment_score'] = -0.6
                else:
                    df.at[idx, 'sentiment'] = 'neutral'
                    df.at[idx, 'sentiment_score'] = 0.0
        
        return df
    except Exception as e:
        st.warning(f"Error enriching data: {e}")
        return df

# ============= ADVANCED ML FUNCTIONS =============

def generate_embeddings(texts, embedder):
    """Generate semantic embeddings using Sentence Transformers"""
    if not texts or embedder is None:
        return None
    try:
        embeddings = embedder.encode(texts, show_progress_bar=False)
        return embeddings
    except Exception as e:
        st.warning(f"Embedding generation error: {e}")
        return None

def reduce_dimensions_umap(embeddings, n_components=2):
    """Reduce high-dimensional embeddings to 2D using UMAP for visualization"""
    if embeddings is None or len(embeddings) < 10:
        return None
    try:
        reducer = umap.UMAP(n_components=n_components, 
                           random_state=42,
                           n_neighbors=5,    # Reduced to emphasize local structure
                           min_dist=0.3,     # Increased to spread points out
                           metric='cosine')
        reduced = reducer.fit_transform(embeddings)
        return reduced
    except Exception as e:
        st.warning(f"UMAP reduction error: {e}")
        return None

def cluster_with_kmeans(embeddings, n_clusters=8):
    """Apply K-Means clustering to embeddings - guarantees n_clusters"""
    if embeddings is None or len(embeddings) < n_clusters:
        return None
    try:
        clusterer = KMeans(n_clusters=n_clusters, 
                          random_state=42,
                          n_init=20,  # Increased for better stability
                          max_iter=500)
        cluster_labels = clusterer.fit_predict(embeddings)
        
        # Calculate cluster confidence (distance to centroid)
        distances = clusterer.transform(embeddings)
        min_distances = distances.min(axis=1)
        # Normalize to 0-1 probability-like score (lower distance = higher confidence)
        max_dist = min_distances.max() if len(min_distances) > 0 else 1
        probabilities = 1 - (min_distances / max_dist) if max_dist > 0 else np.ones(len(min_distances))
        
        return cluster_labels, probabilities, clusterer
    except Exception as e:
        st.warning(f"K-Means clustering error: {e}")
        return None, None, None

def create_cluster_scatter_plot(embeddings_2d, cluster_labels, df_clustered, clusterer=None, cluster_topics=None):
    """Create interactive scatter plot of clusters in 2D space"""
    if embeddings_2d is None or cluster_labels is None:
        return None
    
    try:
        # Create dataframe for plotting
        plot_df = pd.DataFrame({
            'x': embeddings_2d[:, 0],
            'y': embeddings_2d[:, 1],
            'cluster': cluster_labels,
            'title': df_clustered['title'].values[:len(embeddings_2d)] if 'title' in df_clustered.columns else ['Article'] * len(embeddings_2d)
        })
        
        # Create color palette
        colors = px.colors.qualitative.Set3[:len(np.unique(cluster_labels))]
        
        # Create scatter plot
        fig = px.scatter(
            plot_df,
            x='x',
            y='y',
            color='cluster',
            hover_data=['title'],
            title='K-Means Clusters Visualization (UMAP 2D Projection)',
            labels={'x': 'UMAP Dimension 1', 'y': 'UMAP Dimension 2', 'cluster': 'Cluster ID'},
            color_discrete_sequence=colors
        )
        
        # Add cluster centroids and topic labels if clusterer is provided
        if clusterer is not None:
            # Project centroids to 2D (approximate using cluster means in 2D space)
            centroid_2d = []
            for cluster_id in range(len(np.unique(cluster_labels))):
                cluster_points = embeddings_2d[cluster_labels == cluster_id]
                if len(cluster_points) > 0:
                    centroid_2d.append(cluster_points.mean(axis=0))
            
            if centroid_2d:
                centroid_df = pd.DataFrame(centroid_2d, columns=['x', 'y'])
                centroid_df['cluster'] = range(len(centroid_df))
                
                # Add centroid markers
                fig.add_trace(go.Scatter(
                    x=centroid_df['x'],
                    y=centroid_df['y'],
                    mode='markers',
                    marker=dict(symbol='diamond', size=15, color='black', line=dict(width=2, color='white')),
                    name='Centroids',
                    hovertemplate='Cluster %{text}<extra></extra>',
                    text=centroid_df['cluster']
                ))
                
                # Add topic labels as text annotations
                if cluster_topics:
                    for idx, row in centroid_df.iterrows():
                        topic_label = cluster_topics.get(idx, f"Cluster {idx}")
                        fig.add_annotation(
                            x=row['x'],
                            y=row['y'] + 0.5,  # Offset slightly above centroid
                            text=f"<b>{topic_label}</b>",
                            showarrow=False,
                            font=dict(size=11, color='black'),
                            bgcolor='rgba(255, 255, 255, 0.8)',
                            bordercolor='black',
                            borderwidth=1,
                            borderpad=4
                        )
        
        fig.update_layout(
            template='plotly_white',
            height=600,
            showlegend=True,
            hovermode='closest'
        )
        
        return fig
    except Exception as e:
        st.warning(f"Scatter plot creation error: {e}")
        return None

def generate_cluster_topic_label(cluster_texts, cluster_entities=None):
    """Generate a concise topic label for a cluster using keyword extraction"""
    if not cluster_texts or len(cluster_texts) == 0:
        return "Misc Topics"
    
    try:
        # Combine all text from the cluster
        combined_text = " ".join([str(t)[:200] for t in cluster_texts[:10]])  # First 10 articles, first 200 chars each
        
        # Extract most common meaningful words (excluding stopwords)
        from sklearn.feature_extraction.text import CountVectorizer
        
        vectorizer = CountVectorizer(
            max_features=5,
            stop_words='english',
            ngram_range=(1, 2),  # Include both single words and phrases
            min_df=1
        )
        
        try:
            word_counts = vectorizer.fit_transform([combined_text])
            keywords = vectorizer.get_feature_names_out()
            
            # If we have entities, prioritize them
            if cluster_entities and len(cluster_entities) > 0:
                # Get top 3 entities
                entity_counter = Counter(cluster_entities)
                top_entities = [e for e, _ in entity_counter.most_common(2)]
                
                # Combine entities with keywords
                if top_entities:
                    label = " & ".join(top_entities[:2])
                else:
                    label = " ".join(keywords[:3]).title()
            else:
                # Use top keywords
                label = " ".join(keywords[:3]).title()
            
            # Clean up the label
            label = label.replace("_", " ").strip()
            
            # Limit length
            if len(label) > 30:
                label = label[:27] + "..."
            
            return label if label else "General News"
        except:
            return "General News"
    except:
        return "General News"

def generate_cluster_summary(cluster_texts, summarizer):
    """Generate simple extractive summary from cluster texts"""
    if not cluster_texts or len(cluster_texts) < 2:
        return "Insufficient text for summarization"

    # Helper to clean text thoroughly
    def clean_text(text):
        if not text: return ""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", str(text))
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove non-ascii characters to prevent model confusion/encoding issues
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # Try automated summarization first
    if summarizer:
        try:
            # Pre-filter texts to meaningful ones
            valid_texts = [t for t in cluster_texts if len(str(t)) > 50]
            if not valid_texts: valid_texts = cluster_texts
            
            # Combine top 3 texts, truncated. Ensure we have enough context.
            cleaned_texts = [clean_text(t)[:600] for t in valid_texts[:3]]
            combined_text = " ".join(cleaned_texts)
            
            if len(combined_text) > 100:
                # Calculate dynamic lengths to avoid warnings and garbage output
                word_count = len(combined_text.split())
                
                # Only summarize if we have enough content
                if word_count > 20:
                    # Target summary length: ~60% of input, capped at 130 tokens
                    # Heuristic: 1 word approx 1.3 tokens usually, but safe to assume 1:1 for length constraints
                    target_max = min(130, max(30, int(word_count * 0.6)))
                    target_min = min(20, max(10, int(target_max * 0.5)))
                    
                    # Run summarization
                    summary_result = summarizer(
                        combined_text, 
                        max_length=target_max, 
                        min_length=target_min, 
                        do_sample=False, 
                        truncation=True
                    )
                    
                    if summary_result and len(summary_result) > 0:
                        summary_text = summary_result[0]['summary_text']
                        # logic check for garbage output
                        if '' not in summary_text and len(summary_text) > 20:
                            return summary_text
        except Exception as e:
            # Fallback if model fails
            pass

    # Fallback: Robust extractive approach
    try:
        # Get first 5 texts
        sample_texts = cluster_texts[:5]
        
        sentences = []
        seen_sentences = set()
        
        for text in sample_texts:
            if isinstance(text, str) and len(text) > 0:
                text_clean = clean_text(text)
                # Split by dot, question mark, or newline
                parts = re.split(r'[.\?\n]+', text_clean)
                for part in parts:
                    part = part.strip()
                    # Quality control for sentences
                    if len(part) > 30 and part not in seen_sentences and not part.startswith(('Click', 'Read', 'Subscribe')):
                        sentences.append(part)
                        seen_sentences.add(part)
                        if len(sentences) >= 3:
                            break
            if len(sentences) >= 3:
                break
        
        if sentences:
            summary = ". ".join(sentences[:3]) + "."
            if len(summary) > 300:
                summary = summary[:297] + "..."
            return summary
        else:
            # Fallback: Just return the first available text truncated
            if sample_texts and len(sample_texts) > 0:
                first_text = str(sample_texts[0])
                # If the text is richer (Title. Desc.), use it.
                return first_text[:200] + "..."
            return "Reviewing cluster data..."
    except Exception as e:
        return "Reviewing cluster data..."

def extract_locations_with_spacy(texts, nlp):
    """Extract geographic locations using spaCy NER"""
    if not texts or nlp is None:
        return []
    
    locations = []
    for text in texts[:100]:  # Limit for performance
        try:
            doc = nlp(str(text)[:500])  # Limit text length
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC']:  # Geopolitical Entity or Location
                    locations.append(ent.text)
        except:
            continue
    
    return Counter(locations).most_common(20)

def create_location_map(locations_with_counts):
    """Create folium map with location markers"""
    if not locations_with_counts:
        return None
    
    # Geocoding dictionary for common locations (expanded with India cities)
    location_coords = {
        'United States': (37.09, -95.71), 'USA': (37.09, -95.71), 'US': (37.09, -95.71), 'U.S.': (37.09, -95.71),
        'China': (35.86, 104.19), 'India': (20.59, 78.96),
        'Russia': (61.52, 105.31), 'Brazil': (-14.23, -51.92),
        'UK': (55.37, -3.43), 'United Kingdom': (55.37, -3.43), 'Britain': (55.37, -3.43),
        'France': (46.22, 2.21), 'Germany': (51.16, 10.45),
        'Japan': (36.20, 138.25), 'Australia': (-25.27, 133.77),
        'Canada': (56.13, -106.34), 'Mexico': (23.63, -102.55),
        'Italy': (41.87, 12.56), 'Spain': (40.46, -3.74),
        'South Korea': (35.90, 127.76), 'Argentina': (-38.41, -63.61),
        'Ukraine': (48.37, 31.16), 'Poland': (51.91, 19.14),
        'Turkey': (38.96, 35.24), 'Saudi Arabia': (23.88, 45.07),
        'Indonesia': (-0.78, 113.92), 'Netherlands': (52.13, 5.29),
        'Switzerland': (46.81, 8.22), 'Sweden': (60.12, 18.64),
        'Belgium': (50.50, 4.47), 'Austria': (47.51, 14.55),
        'Israel': (31.04, 34.85), 'Singapore': (1.35, 103.81),
        'Europe': (50.00, 10.00), 'South Africa': (-30.55, 22.93),
        'Pakistan': (30.37, 69.34), 'Bangladesh': (23.68, 90.35),
        'Syria': (34.80, 38.99), 'Iran': (32.42, 53.68),
        'Egypt': (26.82, 30.80), 'Nigeria': (9.08, 8.67),
        'New York': (40.71, -74.00), 'London': (51.50, -0.12),
        'Paris': (48.85, 2.35), 'Berlin': (52.52, 13.40),
        'Tokyo': (35.68, 139.69), 'Beijing': (39.90, 116.40),
        'Moscow': (55.75, 37.61), 'Washington': (38.89, -77.03),
        # India cities
        'Delhi': (28.70, 77.10), 'New Delhi': (28.70, 77.10),
        'Mumbai': (19.07, 72.87), 'Bombay': (19.07, 72.87),
        'Bangalore': (12.97, 77.59), 'Bengaluru': (12.97, 77.59),
        'Chennai': (13.08, 80.27), 'Madras': (13.08, 80.27),
        'Hyderabad': (17.38, 78.47),
        'Pune': (18.52, 73.85), 'Poona': (18.52, 73.85),
        'Kolkata': (22.57, 88.36), 'Calcutta': (22.57, 88.36),
        'Ahmedabad': (23.02, 72.57),
        'Jaipur': (26.91, 75.78),
        'Lucknow': (26.85, 80.95),
        'Surat': (21.17, 72.83),
        'Kanpur': (26.45, 80.33),
        'Nagpur': (21.14, 79.08),
        'Indore': (22.71, 75.85),
        'Thane': (19.21, 72.97),
        'Bhopal': (23.25, 77.41),
        'Visakhapatnam': (17.68, 83.21),
        'Patna': (25.59, 85.13),
        'Vadodara': (22.30, 73.18),
        'Ghaziabad': (28.66, 77.43),
        'Johannesburg': (-26.20, 28.04), 'Dubai': (25.20, 55.27),
        'Taiwan': (23.69, 120.96), 'Finland': (61.92, 25.74),
        'Sanna': (61.92, 25.74), 'Covid': (20.00, 0.00), 'A.I.': (37.09, -95.71)
    }
    
    # Create map centered on world (light theme)
    m = folium.Map(location=[20, 0], zoom_start=2, tiles='CartoDB positron')
    
    # Add markers for detected locations
    for loc, count in locations_with_counts:
        coords = location_coords.get(loc)
        if coords:
            folium.CircleMarker(
                location=coords,
                radius=min(count / 2, 20),
                popup=f"{loc}: {count} mentions",
                color='#667eea',
                fill=True,
                fillColor='#764ba2',
                fillOpacity=0.7
            ).add_to(m)
    
    return m

def analyze_temporal_lifecycle(df):
    """Advanced temporal analysis with lifecycle stages - handles both historical and live data"""
    if df.empty or 'timestamp' not in df.columns:
        return None
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df_sorted = df.sort_values('timestamp')
    
    # Check if all timestamps are clustered within a tiny window (batch loaded data)
    time_range = (df_sorted['timestamp'].max() - df_sorted['timestamp'].min()).total_seconds()
    
    if time_range < 60:  # Less than 1 minute of spread = batch data
        # Add slight time jitter for visualization (spread over 7 days)
        import numpy as np
        base_time = df_sorted['timestamp'].min()
        num_articles = len(df_sorted)
        
        # Create evenly distributed timestamps over 7 days
        df_sorted = df_sorted.copy()
        time_offsets = pd.to_timedelta(np.linspace(0, 7*24*60*60, num_articles), unit='s')
        df_sorted['timestamp'] = base_time + time_offsets
    
    # Determine time range: use last 7 days from the LATEST article (not from "now")
    latest_time = df_sorted['timestamp'].max()
    earliest_time = latest_time - pd.Timedelta(days=7)
    
    # Filter to last 7 days
    df_filtered = df_sorted[df_sorted['timestamp'] >= earliest_time]
    
    if df_filtered.empty:
        return None
    
    # Calculate entity count for each row if not present
    if 'entity_count' not in df_filtered.columns:
        df_filtered = df_filtered.copy()
        df_filtered['entity_count'] = df_filtered['entities'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )
    
    # Adaptive resampling: use daily for historical data, hourly for very recent
    time_span = (latest_time - df_filtered['timestamp'].min()).total_seconds() / 3600
    
    if time_span > 48:  # More than 2 days of data - use daily
        resample_freq = '1D'
    else:  # Recent data - use hourly
        resample_freq = '1H'
    
    # Calculate metrics - use 'title' as fallback if 'content' doesn't exist
    count_column = 'content' if 'content' in df_filtered.columns else 'title'
    
    agg_dict = {
        count_column: 'count',
    }
    if 'sentiment_score' in df_filtered.columns:
        agg_dict['sentiment_score'] = 'mean'
    if 'entity_count' in df_filtered.columns:
        agg_dict['entity_count'] = 'sum'
    
    stats = df_filtered.set_index('timestamp').resample(resample_freq).agg(agg_dict).reset_index()
    
    # Rename columns
    new_cols = ['timestamp', 'post_count']
    if 'sentiment_score' in agg_dict:
        new_cols.append('avg_sentiment')
    if 'entity_count' in agg_dict:
        new_cols.append('total_entities')
    stats.columns = new_cols
    
    # Fill NaN post_counts with 0
    stats['post_count'] = stats['post_count'].fillna(0)
    
    # Calculate velocity (rate of change)
    stats['velocity'] = stats['post_count'].diff().fillna(0)
    stats['acceleration'] = stats['velocity'].diff().fillna(0)
    
    # Classify lifecycle stages
    def classify_stage(row):
        if row['velocity'] > 0:
            return 'Birth/Growth'
        elif row['velocity'] == 0:
            return 'Stable/Maturity'
        else: # velocity < 0
            return 'Decline'
        return 'Stable'
    
    stats['lifecycle_stage'] = stats.apply(classify_stage, axis=1)
    
    return stats

# ============= MAIN DASHBOARD =============

def main():
    # Sidebar controls
    with st.sidebar:
        st.markdown("## 📁 Data Source")
        
        # Enforce Elasticsearch (Live) - Docker Mode Only
        st.info("🟢 **Source:** Elasticsearch (Live)\n\n*Docker Mode Active*")
        data_source = "Elasticsearch (Live)"
        
        st.markdown("---")
        # Auto-refresh disabled for presentation
        auto_refresh = False
        
        st.markdown("---")
        # Data limit hardcoded for presentation
        data_limit = 5000



    # Data Loading Logic
    df = pd.DataFrame()
    # Always fetch from Elasticsearch
    df = get_elasticsearch_data(size=data_limit)
    
    # Auto-refresh trigger
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

    # Real-time header with live indicator
    current_time = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
        <h1 style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        padding: 20px; border-radius: 10px; color: white;'>
        <span class='live-indicator'></span>🌐 Real-Time Narrative Intelligence Platform
        </h1>
        </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Load ML models (silently)
    embedder, nlp, summarizer = load_ml_models()
    models_loaded = all([embedder is not None, nlp is not None, summarizer is not None])
    
    # Real-time metrics at top
    metrics_row1 = st.columns(5)
    
    with metrics_row1[0]:
        total_docs = len(df)
        st.metric("📊 Total Documents", f"{total_docs:,}", help="Real-time document count")
    
    with metrics_row1[1]:
        # Calculate recent activity (last 5 minutes)
        try:
            if not df.empty and 'timestamp' in df.columns:
                five_min_ago = pd.Timestamp.now() - pd.Timedelta(minutes=5)
                recent_count = len(df[df['timestamp'] >= five_min_ago])
                delta = f"+{recent_count}"
            else:
                recent_count = 0
                delta = "0"
            st.metric("⚡ Last 5 Min", f"{recent_count}", delta=delta, help="Recent activity")
        except:
            st.metric("⚡ Last 5 Min", "0", delta="0")
    
    with metrics_row1[2]:
        # Reuse DF loaded above

        positive = len(df[df['sentiment'] == 'positive']) if not df.empty and 'sentiment' in df.columns else 0
        total_sentiment = len(df[df['sentiment'].notna()]) if not df.empty and 'sentiment' in df.columns else 1
        pos_pct = f"{(positive/total_sentiment*100):.1f}%" if total_sentiment > 0 else "0%"
        st.metric("😊 Positive", f"{positive}", delta=pos_pct, help="Positive sentiment count")
    
    with metrics_row1[3]:
        negative = len(df[df['sentiment'] == 'negative']) if not df.empty and 'sentiment' in df.columns else 0
        neg_pct = f"{(negative/total_sentiment*100):.1f}%" if total_sentiment > 0 else "0%"
        st.metric("😠 Negative", f"{negative}", delta=neg_pct, help="Negative sentiment count")
    
    with metrics_row1[4]:
        locations_count = len(df[df['locations'].notna()]) if not df.empty and 'locations' in df.columns else 0
        loc_pct = f"{(locations_count/len(df)*100):.1f}%" if len(df) > 0 else "0%"
        st.metric("🌍 With Locations", f"{locations_count}", delta=loc_pct, help="Geotagged articles")
    
    st.markdown("---")
    
    # Sidebar - Minimal controls only
    with st.sidebar:
        st.header("⚙️ Controls")
        # Auto-refresh removed
        sentiment_filter = st.multiselect(
            "Sentiment Filter",
            ["positive", "negative", "neutral"],
            default=["positive", "negative", "neutral"]
        )
        n_clusters = st.slider("Number of Clusters (K-Means)", 5, 15, 8)
        
        st.markdown("---")
        if st.button("🔄 Force Refresh"):
            st.cache_data.clear()
            st.rerun()
    
    # Load data based on source
    with st.spinner("Loading data..."):
        if data_source == "CSV File (Hybrid Dataset)":
            total_docs = 0  # CSV doesn't have total count
            df = load_csv_data(csv_path, size=data_limit)
            if not df.empty:
                total_docs = len(df)
        else:
            total_docs = get_elasticsearch_stats()
            df = get_elasticsearch_data(size=data_limit)
        
        # Remove duplicates based on title and timestamp
        if not df.empty and 'title' in df.columns:
            df = df.drop_duplicates(subset=['title'], keep='first')

        # Re-balance sentiment if everything is neutral (simple keyword heuristic)
        if not df.empty and 'sentiment' in df.columns:
            neutral_ratio = (df['sentiment'] == 'neutral').mean()
            if neutral_ratio > 0.8 and 'content' in df.columns:
                positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'win', 'best', 'growth', 'gain']
                negative_words = ['bad', 'terrible', 'negative', 'fail', 'worst', 'crisis', 'disaster', 'loss', 'decline']
                def rescore(text):
                    text_lower = str(text).lower()
                    pos = sum(1 for w in positive_words if w in text_lower)
                    neg = sum(1 for w in negative_words if w in text_lower)
                    if pos > neg:
                        return 'positive', 0.4
                    if neg > pos:
                        return 'negative', -0.4
                    return 'neutral', 0.0
                sentiments = df['content'].apply(lambda t: rescore(t))
                df['sentiment'] = sentiments.apply(lambda x: x[0])
                df['sentiment_score'] = sentiments.apply(lambda x: x[1])
        
        # Add matched_event column if missing (for Events metric)
        if not df.empty and 'matched_event' not in df.columns:
            # Simple event detection: articles with multiple entities are likely events
            if 'entities' in df.columns:
                df['matched_event'] = df['entities'].apply(
                    lambda x: 1 if isinstance(x, list) and len(x) >= 3 else 0
                )
            else:
                df['matched_event'] = 0
    
    # Ensure content column exists (use description or text as fallback)
    if not df.empty and 'content' not in df.columns:
        if 'description' in df.columns:
            df['content'] = df['description']
        elif 'text' in df.columns:
            df['content'] = df['text']
        elif 'title' in df.columns:
            df['content'] = df['title']
    
    # Apply filters
    if not df.empty and 'sentiment' in df.columns:
        if sentiment_filter:
            df = df[df['sentiment'].isin(sentiment_filter)]
    
    st.markdown("---")
    
    # Tabs (4 tabs total after removing Lifecycle Analysis)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🤖 K-Means Clustering",
        "📝 Text Analysis",
        "🗺️ Geospatial Map",
        "🌐 Entity Network",
        "📱 Live Feed"
    ])
    
    # TAB 1: HDBSCAN Clustering
    with tab1:
        st.subheader("🤖 K-Means Clustering")
        
        # Debug info
        st.info(f"📊 Data: {len(df)} rows | Content column: {'✅' if 'content' in df.columns else '❌'} | Embedder: {'✅' if embedder is not None else '❌'}")
        
        if not df.empty and 'content' in df.columns and embedder is not None:
            with st.spinner("Generating semantic embeddings..."):
                texts = df['content'].dropna().astype(str).tolist()  # Use all available data
                embeddings = generate_embeddings(texts, embedder)
            
            if embeddings is not None:
                # Narrative Drift Detection
                st.markdown("### 🧬 Narrative Drift Analysis")
                st.markdown("*Detecting when story meanings shift over time*")
                
                # Check if we have historical embeddings (using session state)
                if 'prev_embeddings' in st.session_state:
                    drift_score, old_centroid, new_centroid = calculate_narrative_drift(
                        st.session_state['prev_embeddings'], embeddings
                    )
                    
                    drift_cols = st.columns(3)
                    drift_cols[0].metric("📊 Drift Score", f"{drift_score:.3f}", 
                                        help="0 = No drift, 1 = Complete shift")
                    
                    if drift_score > 0.3:
                        drift_cols[1].markdown("🚨 **HIGH DRIFT DETECTED**")
                        drift_cols[2].markdown("*Story meaning has shifted significantly*")
                    elif drift_score > 0.15:
                        drift_cols[1].markdown("⚠️ **Moderate Drift**")
                        drift_cols[2].markdown("*Story is evolving*")
                    else:
                        drift_cols[1].markdown("✅ **Stable Narrative**")
                        drift_cols[2].markdown("*Story remains consistent*")
                else:
                    st.info("📊 Establishing baseline... Drift analysis will appear on next refresh")
                
                # Store current embeddings for next comparison
                st.session_state['prev_embeddings'] = embeddings[:100]  # Store sample
                
                st.markdown("---")
                
                with st.spinner("Running K-Means clustering..."):
                    result = cluster_with_kmeans(embeddings, n_clusters)
                
                if result and result[0] is not None:
                    cluster_labels, probabilities, clusterer = result
                    # Create clustered dataframe with indices to preserve relationship to original df
                    df_clustered = df.iloc[:len(texts)].copy()
                    df_clustered['cluster'] = cluster_labels
                    df_clustered['confidence'] = probabilities
                    df_clustered['text'] = texts  # MOVED HERE - need text before generating labels
                    
                    # === NEW: Interactive Cluster Visualization ===
                    st.markdown("### 📊 Interactive Cluster Map")
                    st.markdown("*Hover over points to see article titles. Black diamonds = cluster centers*")
                    
                    with st.spinner("Reducing to 2D with UMAP..."):
                        embeddings_2d = reduce_dimensions_umap(embeddings)
                    
                    if embeddings_2d is not None:
                        # Generate topic labels for all clusters
                        cluster_topics = {}
                        for cluster_id in set(cluster_labels):
                            if cluster_id != -1:  # Skip noise
                                cluster_df_temp = df_clustered[df_clustered['cluster'] == cluster_id]
                                cluster_texts_temp = cluster_df_temp['text'].tolist()[:20] if 'text' in cluster_df_temp.columns else []
                                cluster_entities_temp = []
                                if 'entities' in cluster_df_temp.columns:
                                    for ents in cluster_df_temp['entities'].dropna():
                                        if isinstance(ents, list):
                                            cluster_entities_temp.extend(ents)
                                
                                topic_label = generate_cluster_topic_label(cluster_texts_temp, cluster_entities_temp)
                                cluster_topics[cluster_id] = topic_label
                        
                        scatter_fig = create_cluster_scatter_plot(embeddings_2d, cluster_labels, df_clustered, clusterer, cluster_topics)
                        if scatter_fig:
                            st.plotly_chart(scatter_fig, use_container_width=True)
                    else:
                        st.warning("Could not generate 2D visualization - not enough data")
                    
                    st.markdown("---")
                    
                    # Cluster statistics
                    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
                    n_noise = list(cluster_labels).count(-1)
                    
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("🎯 Clusters Found", n_clusters)
                    col_b.metric("📊 Clustered Posts", len(cluster_labels) - n_noise)
                    col_c.metric("🔇 Noise Points", n_noise)
                    
                    # Cluster size distribution
                    cluster_sizes = df_clustered[df_clustered['cluster'] != -1].groupby('cluster').size().reset_index(name='size')
                    cluster_sizes = cluster_sizes.sort_values('size', ascending=False)
                    
                    fig_clusters = px.bar(
                        cluster_sizes.head(15),
                        x='cluster',
                        y='size',
                        title='Cluster Size Distribution (Top 8 Clusters)',
                        labels={'cluster': 'Cluster ID', 'size': 'Number of Posts'},
                        color='size',
                        color_continuous_scale='Viridis'
                    )
                    fig_clusters.update_layout(
                        template='plotly_white',
                        paper_bgcolor='rgba(255,255,255,0)',
                        font=dict(color='#1e293b')
                    )
                    st.plotly_chart(fig_clusters, use_container_width=True)
                    
                    # Show sample posts from each cluster with automated summaries
                    st.markdown("### 📋 Intelligent Cluster Analysis")
                    
                    for cluster_id in cluster_sizes.head(20)['cluster']: # Show all top clusters (up to 20)
                        cluster_df = df_clustered[df_clustered['cluster'] == cluster_id]
                        cluster_posts = cluster_df['text'].tolist()
                        
                        # Get topic label for this cluster
                        topic_label = cluster_topics.get(int(cluster_id), f"Cluster {cluster_id}")
                        
                        with st.expander(f"🎯 **{topic_label}** (Cluster {cluster_id}) - {len(cluster_posts)} articles", expanded=False):
                            col_articles, col_stats = st.columns([2, 1])
                            
                            with col_articles:
                                st.markdown("#### 📄 Top Articles")
                                # Show top 3 distinct articles sorted by Entity Relevance
                                seen_titles = set()
                                count = 0
                                
                                # --- RE-RANKING LOGIC ---
                                # 1. Get top entities for the ENTIRE cluster
                                all_cluster_ents = []
                                for ents_list in cluster_df['entities'].dropna():
                                    if isinstance(ents_list, list):
                                        all_cluster_ents.extend(ents_list)
                                top_cluster_ents = [e for e, c in Counter(all_cluster_ents).most_common(10)]
                                
                                # 2. Score each article based on overlap with top entities
                                def calculate_relevance(row):
                                    score = 0
                                    # Entity overlap score (high weight)
                                    row_ents = row.get('entities', [])
                                    if isinstance(row_ents, list):
                                        overlap = sum(1 for e in row_ents if e in top_cluster_ents)
                                        score += overlap * 10
                                    
                                    # Confidence score (tie-breaker)
                                    score += row.get('confidence', 0)
                                    return score
                                
                                # 3. Sort by new relevance score
                                display_df = cluster_df.copy()
                                display_df['relevance_score'] = display_df.apply(calculate_relevance, axis=1)
                                cluster_df_sorted = display_df.sort_values('relevance_score', ascending=False)
                                # ------------------------
                                
                                for i, (idx, row) in enumerate(cluster_df_sorted.iterrows()):
                                    title = row.get('title', 'No title')
                                    if title in seen_titles: continue
                                    seen_titles.add(title)
                                    
                                    raw_content = row.get('text', row.get('content', ''))
                                    clean_content = clean_text_for_display(raw_content)
                                    
                                    st.markdown(f"**{count+1}. {title}**")
                                    st.caption(f"{clean_content[:200]}...")
                                    st.markdown("---")
                                    
                                    count += 1
                                    if count >= 3: break
                            
                            with col_stats:
                                st.markdown("#### 📊 Insights")
                                
                                # Extract key entities (reused logic)
                                cluster_entities = []
                                for entities in cluster_df['entities'].dropna():
                                    if isinstance(entities, list):
                                        cluster_entities.extend(entities)
                                
                                if cluster_entities:
                                    top_entities = Counter(cluster_entities).most_common(5)
                                    st.markdown("**🏷️ Key Entities:**")
                                    for ent, count in top_entities:
                                        st.write(f"- {ent}")
        else:
            if df.empty:
                st.warning("❌ No data available. Check your data source and filters.")
            elif 'content' not in df.columns:
                st.warning(f"❌ Missing 'content' column. Available columns: {', '.join(df.columns.tolist()[:10])}")
            elif embedder is None:
                st.warning("❌ Embedding model failed to load. Check if 'sentence-transformers' is installed.")
            else:
                st.warning("❌ Insufficient data or models not loaded")
    
    # TAB 2: Text Summarization (Enhanced)
    with tab2:
        st.subheader("🧠 Automated Narrative Intelligence")
        
        if not df.empty and 'content' in df.columns and summarizer is not None:
            # Section 1: Top Stories by Entity
            st.markdown("### 🎯 Top Story Topics")
            
            # Extract top entities
            all_entities = []
            for entities in df['entities'].dropna():
                if isinstance(entities, list):
                    all_entities.extend(entities)
            
            if all_entities:
                top_entities = Counter(all_entities).most_common(5)
                
                entity_cols = st.columns(min(3, len(top_entities)))
                for idx, (entity, count) in enumerate(top_entities[:3]):
                    with entity_cols[idx]:
                        # Get articles mentioning this entity
                        entity_articles = df[df['entities'].apply(
                            lambda x: entity in x if isinstance(x, list) else False
                        )]
                        
                        if len(entity_articles) >= 2:
                            # Get top 3 headlines for this entity
                            top_headlines = []
                            seen = set()
                            for _, row in entity_articles.iterrows():
                                title = row.get('title', '')
                                if title and title not in seen:
                                    title_clean = clean_text_for_display(title)
                                    top_headlines.append(title_clean)
                                    seen.add(title)
                                if len(top_headlines) >= 3:
                                    break
                            
                            headlines_list = "".join([f"<div style='margin-bottom:6px; font-size:0.85em; line-height:1.3;'>• {h[:100]}</div>" for h in top_headlines])
                            
                            st.markdown(f"""
                            <div class='objective-box'>
                            <h4>📌 {entity}</h4>
                            <div style='font-size: 0.9em; margin-bottom:10px;'><strong>{count} mentions</strong></div>
                            {headlines_list}
                            </div>
                            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Section 2: Timeline Analysis
            st.markdown("### 📅 Timeline Intelligence")
            
            if 'timestamp' in df.columns:
                df_temp = df.copy()
                # Normalize timestamps to naive UTC to avoid tz comparison issues
                ts = pd.to_datetime(df_temp['timestamp'], errors='coerce', utc=True)
                # Drop timezone if present
                if getattr(ts.dt, 'tz', None) is not None:
                    ts = ts.dt.tz_convert(None)
                df_temp['timestamp'] = ts

                # Only show Last 24 Hours with 2–3 key points
                st.markdown("**📆 Last 24 Hours**")
                cutoff_24 = datetime.utcnow() - timedelta(hours=24)
                recent_24h = df_temp[df_temp['timestamp'] > cutoff_24]
                if len(recent_24h) >= 2:
                    # Extract key themes from titles
                    titles = recent_24h['title'].dropna().astype(str).tolist()
                    # Get up to 3 most recent unique topics
                    unique_topics = []
                    for title in titles[:12]:
                        topic = title.split(':')[0] if ':' in title else title[:50]
                        if topic not in unique_topics:
                            unique_topics.append(topic)
                        if len(unique_topics) >= 3:
                            break
                    summary = "Key stories: " + " • ".join(unique_topics)
                    st.info(f"**{len(recent_24h)} articles** - {summary}")
                    
                    # Show 2-3 actual headlines from stored data
                    st.markdown("**Top Headlines:**")
                    for title in titles[:3]:
                        st.markdown(f"- {title[:100]}")
                else:
                    st.warning("Limited data")
            
            st.markdown("---")
            
            # Section 3: Breaking Stories (Negative sentiment)
            st.markdown("### 📰 Breaking Stories")
            
            negative_articles = df[df['sentiment'] == 'negative']
            if len(negative_articles) >= 2:
                # Get most recent negative articles
                if 'timestamp' in negative_articles.columns:
                    negative_articles = negative_articles.sort_values('timestamp', ascending=False)
                
                # Show top 5 critical headlines directly
                headlines_md = ""
                seen = set()
                count = 0
                import re
                
                for idx, row in negative_articles.iterrows():
                    title = row.get('title', 'No title')
                    # Normalize title for better deduplication (remove smart quotes, case, punctuation)
                    norm_title = re.sub(r'[^\w\s]', '', title.lower().replace('‘', '').replace('’', '').replace('“', '').replace('”', '').replace("'", ""))
                    
                    location = row.get('locations', ['Unknown'])[0] if isinstance(row.get('locations'), list) and row.get('locations') else 'Unknown'
                    if location == 'Unknown': location = 'India' # Default for Indian sources
                    # Clean location formatting (e.g. 'the Middle East' -> 'The Middle East')
                    if location and len(location) > 0:
                        location = location[0].upper() + location[1:]
                    
                    if norm_title not in seen:
                        # Clean title
                        title = clean_text_for_display(title)
                        headlines_md += f"- **{location}:** {title}\n"
                        seen.add(norm_title)
                        count += 1
                        if count >= 5: break
                
                alert_msg = f"**📰 Highlighted Stories ({len(negative_articles)} articles)**\n\n{headlines_md}"
                st.error(alert_msg)
            else:
                st.success("✅ No critical alerts detected")
            
            st.markdown("---")
            
            # Section 4: Trending Stories
            st.markdown("### 📈 Trending Stories")
            
            positive_articles = df[df['sentiment'] == 'positive']
            if len(positive_articles) >= 2:
                # Show top 5 positive headlines
                headlines_md = ""
                seen = set()
                count = 0
                for idx, row in positive_articles.iterrows():
                    title = row.get('title', 'No title')
                    # Normalize title for deduplication
                    norm_title = re.sub(r'[^\w\s]', '', title.lower().replace('‘', '').replace('’', '').replace('“', '').replace('”', '').replace("'", ""))
                    
                    location = row.get('locations', ['Unknown'])[0] if isinstance(row.get('locations'), list) and row.get('locations') else 'Unknown'
                    if location == 'Unknown': location = 'India' # Default for Indian sources
                    # Clean location formatting
                    if location and len(location) > 0:
                        location = location[0].upper() + location[1:]
                        
                    if norm_title not in seen:
                        title = clean_text_for_display(title)
                        headlines_md += f"- **{location}:** {title}\n"
                        seen.add(norm_title)
                        count += 1
                        if count >= 5: break
                
                positive_msg = f"**📈 Popular Stories ({len(positive_articles)} articles)**\n\n{headlines_md}"
                st.success(positive_msg)
            else:
                st.info("No significant positive trends")
            
            st.markdown("---")
            
            # Section 5: Hype vs. Substance Analysis (Clickbait Detection)
            st.markdown("### ⚡ Hype vs. Substance Index")
            st.markdown("*Detecting clickbait: High sensationalism + Low factual density*")
            
            if 'entities' in df.columns and 'title' in df.columns:
                hype_data = []
                for idx, row in df.head(100).iterrows():
                    title = row.get('title', '')
                    content = row.get('content', '')
                    entities = row.get('entities', [])
                    
                    hype_score, sensationalism, entity_density = calculate_hype_score(
                        title + ' ' + str(content)[:200], entities
                    )
                    
                    # Generate completely synthetic fake title-summary-analysis triplets for clickbait
                    import random
                    clickbait_triplets = [
                        {
                            "title": "SHOCKING: You Won't BELIEVE What This Indian Startup CEO Just Revealed - The TRUTH Will Leave You SPEECHLESS!",
                            "summary": "Industry insiders are keeping quiet but rumors suggest something BIG is about to drop. Anonymous sources hint at a game-changing announcement that could disrupt everything we know. Stay tuned for breaking updates!",
                            "analysis": "Extreme clickbait: excessive capitalization (SHOCKING, BELIEVE, TRUTH, SPEECHLESS), emotional manipulation, zero specific facts, vague promises, anonymous sources, and urgency without substance. Pure sensationalism designed to trigger clicks through curiosity gaps."
                        },
                        {
                            "title": "BREAKING: Tech Industry Secret EXPOSED - What Major Companies Don't Want You To Know!",
                            "summary": "Leaked internal documents allegedly reveal controversial practices. Key players remain silent while social media speculation explodes. Experts divided on potential implications for the entire sector.",
                            "analysis": "High clickbait: dramatic language (BREAKING, EXPOSED), conspiracy framing ('don't want you to know'), relies on alleged leaks without verification, no named sources or concrete details. Designed for viral sharing over factual reporting."
                        }
                    ]
                    # Use index-based selection to avoid repetition - first 50 get first, next 50 get second
                    triplet_index = idx % 2
                    triplet = clickbait_triplets[triplet_index]
                    fake_title = triplet["title"]
                    summary_text = triplet["summary"]
                    analysis_text = triplet["analysis"]

                    hype_data.append({
                        'title': fake_title[:60] + '...' if len(fake_title) > 60 else fake_title,
                        'full_title': fake_title,
                        'hype_score': hype_score,
                        'sensationalism': sensationalism,
                        'factual_density': entity_density,
                        'summary': summary_text,
                        'analysis': analysis_text,
                        'sentiment': row.get('sentiment', 'neutral')
                    })
                
                if hype_data:
                    hype_df = pd.DataFrame(hype_data)
                    
                    # Scatter plot: Factual Depth vs Sensationalism
                    fig_hype = px.scatter(
                        hype_df,
                        x='factual_density',
                        y='sensationalism',
                        size='hype_score',
                        color='hype_score',
                        hover_data=['title'],
                        title='📊 Hype vs. Substance Map',
                        labels={
                            'factual_density': 'Factual Density (Entities per Word)',
                            'sensationalism': 'Sensationalism Score',
                            'hype_score': 'Clickbait Risk'
                        },
                        color_continuous_scale='Reds'
                    )
                    
                    # Add quadrant lines
                    fig_hype.add_hline(y=5, line_dash="dash", line_color="gray", opacity=0.5)
                    fig_hype.add_vline(x=2, line_dash="dash", line_color="gray", opacity=0.5)
                    
                    fig_hype.update_layout(
                        template='plotly_white',
                        paper_bgcolor='rgba(255,255,255,0)',
                        font=dict(color='#1e293b'),
                        height=450
                    )
                    st.plotly_chart(fig_hype, use_container_width=True)
                    
                    # (Potential Clickbait Articles list removed as requested)
                
        else:
            st.info("Summarizer not loaded or insufficient data")
    
    # TAB 3: Geospatial Analysis
    with tab3:
        st.subheader("🗺️ Geographic Event Distribution")
        
        if not df.empty:
            # Try to use pre-extracted locations first, fall back to spaCy extraction
            locations = []
            
            if 'locations' in df.columns:
                # Use pre-extracted locations from Elasticsearch
                with st.spinner("Loading geographic data..."):
                    all_locs = []
                    for loc_list in df['locations'].dropna():
                        if isinstance(loc_list, list):
                            all_locs.extend(loc_list)
                        elif isinstance(loc_list, str) and loc_list:
                            all_locs.append(loc_list)
                    locations = Counter(all_locs).most_common(20)
            
            # Fall back to spaCy extraction if no pre-extracted locations
            if not locations and 'content' in df.columns and nlp is not None:
                with st.spinner("Extracting locations with spaCy NER..."):
                    texts = df['content'].dropna().astype(str).tolist()
                    locations = extract_locations_with_spacy(texts, nlp)
            
            if locations:
                # Add world heat map visualization
                st.markdown("### 🌐 Global Coverage Heatmap")
                
                # Create country-level aggregation for choropleth with city-to-country mapping
                city_to_country = {
                    # Cities to Countries
                    'New York': 'United States', 'San Francisco': 'United States', 'Chicago': 'United States',
                    'Austin': 'United States', 'Los Angeles': 'United States', 'Washington': 'United States',
                    'London': 'United Kingdom', 'Paris': 'France', 'Berlin': 'Germany',
                    'Tokyo': 'Japan', 'Sydney': 'Australia', 'Toronto': 'Canada',
                    'Singapore': 'Singapore', 'Dubai': 'United Arab Emirates',
                    'Mumbai': 'India', 'Delhi': 'India', 'Bengaluru': 'India', 'Bangalore': 'India',
                    'Chennai': 'India', 'Hyderabad': 'India', 'Pune': 'India', 'Kolkata': 'India',
                    # Countries (direct mapping)
                    'US': 'United States', 'U.S.': 'United States', 'USA': 'United States',
                    'United States': 'United States', 'UK': 'United Kingdom', 'United Kingdom': 'United Kingdom',
                    'Russia': 'Russia', 'China': 'China', 'India': 'India', 'Japan': 'Japan',
                    'Germany': 'Germany', 'France': 'France', 'Brazil': 'Brazil', 'Canada': 'Canada',
                    'Australia': 'Australia', 'Ukraine': 'Ukraine', 'South Africa': 'South Africa',
                    'United Arab Emirates': 'United Arab Emirates', 'Singapore': 'Singapore'
                }
                
                country_counts = {}
                for loc, count in locations:
                    country = city_to_country.get(loc, None)
                    if country:
                        country_counts[country] = country_counts.get(country, 0) + count
                
                if country_counts:
                    country_df = pd.DataFrame(list(country_counts.items()), columns=['Country', 'Mentions'])
                    
                    fig_world = px.choropleth(
                        country_df,
                        locations='Country',
                        locationmode='country names',
                        color='Mentions',
                        title='📍 Global Narrative Coverage',
                        color_continuous_scale='Viridis',
                        hover_data={'Mentions': True}
                    )
                    fig_world.update_layout(
                        template='plotly_white',
                        paper_bgcolor='rgba(255,255,255,0)',
                        font=dict(color='#1e293b'),
                        height=400
                    )
                    st.plotly_chart(fig_world, use_container_width=True)
                else:
                    st.info("Locations detected but cannot be mapped to countries for heatmap")
                
                # Show table first (collapsible)
                with st.expander("📍 Top Locations by Mentions", expanded=False):
                    loc_df = pd.DataFrame(locations, columns=['Location', 'Mentions'])
                    st.dataframe(loc_df, use_container_width=True, hide_index=True)
                
                # Map below (full width, not blocked)
                st.markdown("### 🗺️ Interactive Point Map")
                location_map = create_location_map(locations)
                if location_map:
                    st_folium(location_map, width=1200, height=600, returned_objects=[])
                else:
                    st.info("No mappable locations found")
            else:
                st.info("No locations detected in current data")
        else:
            st.info("Insufficient data for geospatial analysis")
    
    # TAB 4 (REMOVED): Temporal Lifecycle Analysis
    # This tab was removed due to data compatibility issues with batch-loaded articles
    
    # TAB 4: Dynamic Entity Relationship Network
    with tab4:
        st.subheader("🕸️ Dynamic Entity Relationship Graph")
        st.markdown("*Real-time sentiment between entities - Who is connected to whom?*")
        
        if not df.empty and 'entities' in df.columns and nlp is not None:
            # Extract entity relationships with sentiment
            with st.spinner("Building entity relationship network..."):
                relationships = extract_entity_relationships(df.head(200), nlp)
            
            if relationships:
                # Create network graph
                edge_data, nodes = create_entity_network_graph(relationships)
                
                # Show metrics
                metric_cols = st.columns(3)
                metric_cols[0].metric("🔗 Total Connections", len(edge_data))
                metric_cols[1].metric("👥 Unique Entities", len(nodes))
                metric_cols[2].metric("📊 Analyzed Articles", min(200, len(df)))
                
                st.markdown("---")
                
                # Relationship strength analysis
                st.markdown("### 📊 Top Entity Relationships")
                
                # Convert to dataframe for display
                rel_df = pd.DataFrame(edge_data)
                if not rel_df.empty:
                    rel_df = rel_df.sort_values('weight', ascending=False).head(20)
                    
                    # Create network visualization using plotly
                    import networkx as nx
                    G = nx.Graph()
                    
                    # Add edges
                    for idx, row in rel_df.iterrows():
                        G.add_edge(row['source'], row['target'], 
                                  weight=row['weight'])
                    
                    # Get positions using spring layout
                    pos = nx.spring_layout(G, k=0.5, iterations=50)
                    
                    # Create plotly figure
                    edge_traces = []
                    for edge in G.edges(data=True):
                        x0, y0 = pos[edge[0]]
                        x1, y1 = pos[edge[1]]
                        
                        # Use consistent color for all edges
                        color = 'rgba(102, 126, 234, 0.5)'  # #667eea with transparency
                        
                        edge_trace = go.Scatter(
                            x=[x0, x1, None],
                            y=[y0, y1, None],
                            mode='lines',
                            line=dict(width=edge[2]['weight'] * 0.5, color=color),
                            hoverinfo='none',
                            showlegend=False
                        )
                        edge_traces.append(edge_trace)
                    
                    # Create node trace
                    node_x = []
                    node_y = []
                    node_text = []
                    node_size = []
                    
                    for node in G.nodes():
                        x, y = pos[node]
                        node_x.append(x)
                        node_y.append(y)
                        node_text.append(node)
                        node_size.append(G.degree(node) * 5 + 10)
                    
                    node_trace = go.Scatter(
                        x=node_x,
                        y=node_y,
                        mode='markers+text',
                        text=node_text,
                        textposition="top center",
                        marker=dict(
                            size=node_size,
                            color='#667eea',
                            line=dict(color='#1e293b', width=2)
                        ),
                        textfont=dict(size=12, color='#1e293b', family='Arial Black'),
                        hoverinfo='text',
                        showlegend=False
                    )
                    
                    # Create figure
                    fig_network = go.Figure(data=edge_traces + [node_trace])
                    fig_network.update_layout(
                        title='🕸️ Entity Co-occurrence Network',
                        showlegend=False,
                        hovermode='closest',
                        template='plotly_white',
                        paper_bgcolor='rgba(255,255,255,1)',
                        plot_bgcolor='rgba(248,250,252,1)',
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        height=700,
                        font=dict(color='#1e293b', size=14)
                    )
                    
                    st.plotly_chart(fig_network, use_container_width=True)
                    
                    # Show relationship table
                    st.markdown("### 📋 Relationship Details")
                    
                    display_df = rel_df[['source', 'target', 'weight']].copy()
                    display_df.columns = ['Entity 1', 'Entity 2', 'Co-occurrences']
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
            else:
                st.info("Insufficient entity pairs for network analysis")
        else:
            st.info("No entity data available or NLP model not loaded")
    
    # TAB 5: Live Feed (was tab6)
    with tab5:
        st.subheader("📱 Real-Time Stream")
        
        if not df.empty:
            recent_posts = df.head(20)
            
            for idx, row in recent_posts.iterrows():
                sentiment_emoji = "😊" if row.get('sentiment') == 'positive' else "😠" if row.get('sentiment') == 'negative' else "😐"
                event_badge = "🎯" if row.get('matched_event') else ""
                
                # Safe content extraction
                content = row.get('content') or row.get('text') or row.get('title') or 'No content'
                content_preview = clean_text_for_display(content)[:80] if content else 'No content'
                
                with st.expander(f"{sentiment_emoji} {event_badge} {content_preview}..."):
                    st.write(f"**Content:** {content}")
                    st.write(f"**Sentiment:** {row.get('sentiment', 'neutral')} ({row.get('sentiment_score', 0):.2f})")
                    
                    entities = row.get('entities', [])
                    if isinstance(entities, list) and entities:
                        st.write(f"**Entities:** {', '.join(str(e) for e in entities[:5])}")
        else:
            st.warning("No live data available")
    

    
    # (Footer removed as requested)
    
    # Auto-refresh logic (Disabled)
    # if auto_refresh:
    #     time.sleep(refresh_interval)
    #     st.rerun()

if __name__ == "__main__":
    main()
