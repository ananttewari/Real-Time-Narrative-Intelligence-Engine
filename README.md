# Real-Time Narrative Intelligence Engine

## 🎯 Project Overview

The **Real-Time Narrative Intelligence Engine** is an advanced analytics platform that processes and analyzes news articles in real-time to detect patterns, track narratives, identify clickbait, and visualize information flows across geographic and temporal dimensions. This system combines machine learning, natural language processing, and interactive visualization to provide actionable intelligence from news data streams.

### Key Capabilities

1. **Intelligent Clustering** - Automatically groups similar news articles using K-Means algorithm with UMAP dimensionality reduction
2. **Sentiment Analysis** - Tracks positive, negative, and neutral narratives across time and geography
3. **Clickbait Detection** - Identifies sensationalist content using hype scoring algorithms
4. **Entity Network Analysis** - Maps relationships between organizations, people, and locations
5. **Geospatial Visualization** - Interactive maps showing where stories are happening
6. **Timeline Intelligence** - Tracks story evolution over 24-hour windows
7. **Real-Time Metrics** - Live dashboard with streaming analytics

---

## 🏗️ Complete System Architecture

### High-Level Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA LAYER (Storage & Indexing)                       │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │               Elasticsearch (localhost:9200)                     │   │
│  │  • Index: news_articles                                          │   │
│  │  • 1000 documents with full metadata                             │   │
│  │  • Real-time indexing and search                                 │   │
│  │  • Mappings: timestamp, sentiment_score, cluster metadata        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────────┐
│                  PROCESSING LAYER (ML & Analytics)                        │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Machine Learning Pipeline                                        │  │
│  │  ────────────────────────────                                    │  │
│  │  1. Text Embeddings: sentence-transformers/all-MiniLM-L6-v2      │  │
│  │     • Converts article content to 384-dimensional vectors        │  │
│  │     • Enables semantic similarity computation                     │  │
│  │                                                                   │  │
│  │  2. Dimensionality Reduction: UMAP                               │  │
│  │     • Reduces 384D → 2D for visualization                        │  │
│  │     • Preserves local and global structure                       │  │
│  │     • Parameters: n_neighbors=15, min_dist=0.1                   │  │
│  │                                                                   │  │
│  │  3. Clustering: K-Means                                          │  │
│  │     • Configurable clusters (5-15, default 8)                    │  │
│  │     • Identifies thematic groups in news                         │  │
│  │     • Random state=42 for reproducibility                        │  │
│  │                                                                   │  │
│  │  4. Named Entity Recognition: spaCy en_core_web_sm               │  │
│  │     • Extracts: PERSON, ORG, GPE, LOC                           │  │
│  │     • Builds entity co-occurrence networks                       │  │
│  │                                                                   │  │
│  │  5. Summarization: BART (facebook/bart-large-cnn)                │  │
│  │     • Generates concise cluster summaries                        │  │
│  │     • Max length: 100 tokens                                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────────┐
│              PRESENTATION LAYER (Visualization & UI)                      │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Streamlit Dashboard (dashboard_enhanced.py)                      │  │
│  │  ──────────────────────────────────────────                      │  │
│  │                                                                   │  │
│  │  Tab 1: Live Intelligence                                        │  │
│  │  ├─ Real-time metrics (total docs, active streams)               │  │
│  │  ├─ Timeline Intelligence (Last 24 Hours)                        │  │
│  │  ├─ Critical Alerts (Negative sentiment tracking)                │  │
│  │  ├─ Positive Developments (Success stories)                      │  │
│  │  └─ Hype vs. Substance (Clickbait detection)                     │  │
│  │                                                                   │  │
│  │  Tab 2: Clustering Analysis                                      │  │
│  │  ├─ K-Means UMAP Visualization (2D scatter plot)                 │  │
│  │  ├─ Cluster distribution (bar chart)                             │  │
│  │  ├─ Silhouette score (quality metric)                            │  │
│  │  └─ Detailed cluster breakdowns with summaries                   │  │
│  │                                                                   │  │
│  │  Tab 3: Geospatial Analysis                                      │  │
│  │  ├─ Interactive Folium map (article locations)                   │  │
│  │  ├─ Choropleth map (country-level aggregation)                   │  │
│  │  └─ Location frequency analysis                                  │  │
│  │                                                                   │  │
│  │  Tab 4: Entity Networks                                          │  │
│  │  ├─ NetworkX graph visualization                                 │  │
│  │  ├─ Entity co-occurrence relationships                           │  │
│  │  ├─ Degree centrality ranking                                    │  │
│  │  └─ Interactive entity filtering                                 │  │
│  │                                                                   │  │
│  │  Tab 5: Temporal Analysis                                        │  │
│  │  ├─ Time series visualization                                    │  │
│  │  ├─ Hourly article distribution                                  │  │
│  │  └─ Sentiment trends over time                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Detailed Component Breakdown

### 1. Data Generation & Ingestion

#### Synthetic Data Generator (`src/ingestion/synthetic_to_es.py`)

This module creates realistic news article data for testing and demonstration purposes.

**Features:**
- **13 Pre-defined Clusters:**
  - 12 regular clusters covering Indian scenarios (Digital Transformation, Pharma, Space, Banking, Renewables, Infrastructure, Auto, EdTech, Healthcare, Cybersecurity, Economic Policy)
  - 1 clickbait cluster with sensationalist content
  
- **Article Generation:**
  ```python
  TOTAL_DOCS = 1000  # 920 regular + 80 clickbait (8% ratio)
  ```
  
- **Metadata Enrichment:**
  - **Title Variation:** 3 methods (prefix/suffix, day markers, variation words) ensure uniqueness
  - **Entity Groups:** Pre-defined co-occurrence patterns (e.g., ["Reliance Jio", "Google", "NITI Aayog"])
  - **Locations:** Indian-majority (Mumbai, Delhi, Bengaluru) + international (Dubai, Singapore)
  - **Sentiment Scoring:** 
    - Positive: 0.65-0.95
    - Negative: -0.65 to -0.35
    - Neutral: 0.05-0.35
  - **Sensationalism Score (0-5):**
    - Clickbait: 4.0-5.0
    - Regular: 0-3.0
  - **Factual Density:** Entities per 100 words
    - Clickbait: 0.3-0.9
    - Regular: 1.5-2.5

**How It Works:**
1. Creates Elasticsearch index with proper mappings
2. Generates 920 regular articles distributed across 12 clusters
3. Generates 80 clickbait articles with high sensationalism
4. Uses bulk insert API for efficient indexing
5. Each article includes: title, content, source, author, timestamp, location, entities, sentiment, cluster metadata

#### Elasticsearch Integration

**Index:** `news_articles`

**Schema:**
```json
{
  "id": "unique-uuid",
  "title": "Article headline",
  "content": "Full article text",
  "source": "Times of India",
  "author": "Reporter Name",
  "timestamp": "2025-12-21T10:30:00",
  "locations": ["Mumbai", "Delhi"],
  "entities": ["Reliance", "NITI Aayog", "RBI"],
  "sentiment": "positive",
  "sentiment_score": 0.85,
  "sensationalism_score": 1.2,
  "factual_density": 2.1,
  "cluster_id": 3,
  "cluster_topic": "Indian Pharma Leadership",
  "cluster_confidence": 0.92,
  "is_clickbait": false
}
```

---

### 2. Machine Learning Pipeline

#### A. Text Embeddings (Sentence Transformers)

**Model:** `sentence-transformers/all-MiniLM-L6-v2`

**How It Works:**
1. Takes article content as input text
2. Processes through transformer layers
3. Outputs 384-dimensional dense vector
4. Vectors capture semantic meaning
5. Similar articles have vectors close in cosine space

**Usage in Code:**
```python
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer('all-MiniLM-L6-v2')
texts = df['content'].tolist()
embeddings = embedder.encode(texts, show_progress_bar=True)
# Output shape: (1000, 384)
```

**Why This Model:**
- Fast inference (important for real-time)
- Good balance of quality and speed
- 384D is manageable for downstream tasks
- Pre-trained on semantic textual similarity

---

#### B. Dimensionality Reduction (UMAP)

**Algorithm:** Uniform Manifold Approximation and Projection

**Parameters:**
```python
reducer = umap.UMAP(
    n_neighbors=15,      # Local neighborhood size
    min_dist=0.1,        # Minimum distance in 2D space
    n_components=2,      # Output dimensions
    metric='cosine',     # Distance metric
    random_state=42      # Reproducibility
)
```

**How It Works:**
1. **Graph Construction:**
   - For each point, find 15 nearest neighbors in 384D space
   - Build weighted graph of local relationships
   
2. **Optimization:**
   - Create low-dimensional (2D) representation
   - Preserve local structure (nearby points stay nearby)
   - Preserve global structure (cluster separation)
   
3. **Output:**
   - 2D coordinates for each article
   - Can be visualized in scatter plot
   - Clusters become visually apparent

**Why UMAP Over PCA/t-SNE:**
- Better preserves global structure than t-SNE
- Faster than t-SNE for large datasets
- More flexible than PCA (non-linear)
- Configurable balance of local/global preservation

---

#### C. Clustering (K-Means)

**Algorithm:** K-Means with configurable K

**Parameters:**
```python
kmeans = KMeans(
    n_clusters=8,        # Adjustable 5-15 via sidebar
    random_state=42,     # Reproducibility
    n_init=10,           # Multiple initializations
    max_iter=300         # Convergence iterations
)
```

**How It Works:**
1. **Initialization:**
   - Randomly place 8 centroids in embedding space
   - Use k-means++ for smart initialization
   
2. **Assignment Step:**
   - Each article assigned to nearest centroid
   - Distance metric: Euclidean in embedding space
   
3. **Update Step:**
   - Recompute centroid as mean of assigned articles
   - Centroids move to cluster centers
   
4. **Iteration:**
   - Repeat assign + update until convergence
   - Or until max_iter (300) reached
   
5. **Output:**
   - Cluster label (0-7) for each article
   - Cluster centroids in embedding space

**Quality Metrics:**
- **Silhouette Score (-1 to 1):**
  - Measures cluster cohesion and separation
  - >0.5 = Good clustering
  - <0.2 = Weak clustering
  
**Dashboard Features:**
- Adjustable cluster count (5-15) with slider
- Real-time re-clustering on parameter change
- Color-coded scatter plot with cluster labels
- Centroid markers (★) on visualization

---

#### D. Named Entity Recognition (spaCy)

**Model:** `en_core_web_sm`

**Entity Types Extracted:**
- `PERSON` - Names of people (e.g., "Narendra Modi")
- `ORG` - Organizations (e.g., "Reliance Industries", "ISRO")
- `GPE` - Geopolitical entities (e.g., "India", "Mumbai")
- `LOC` - Non-GPE locations (e.g., "Himalayas")

**How It Works:**
1. **Tokenization:** Split text into tokens
2. **POS Tagging:** Identify parts of speech
3. **Dependency Parsing:** Analyze grammatical structure
4. **Entity Recognition:** Use pre-trained model to classify spans
5. **Entity Linking:** Group related mentions

**Usage:**
```python
import spacy
nlp = spacy.load('en_core_web_sm')

doc = nlp("Reliance Jio partners with Google in Mumbai")
entities = [(ent.text, ent.label_) for ent in doc.ents]
# Output: [('Reliance Jio', 'ORG'), ('Google', 'ORG'), ('Mumbai', 'GPE')]
```

**Network Analysis:**
- Builds graph where nodes = entities
- Edges = co-occurrence in same article
- Weighted by frequency of co-occurrence
- Identifies key players (high degree centrality)

---

#### E. Text Summarization (BART)

**Model:** `facebook/bart-large-cnn`

**Purpose:** Generate concise cluster summaries

**How It Works:**
1. **Input:** Concatenated articles from cluster (max 1024 tokens)
2. **Encoding:** BART encoder processes input sequence
3. **Decoding:** Generate summary autoregressively
4. **Output:** 50-100 token summary capturing main themes

**Parameters:**
```python
summarizer = pipeline(
    'summarization',
    model='facebook/bart-large-cnn',
    device=0 if torch.cuda.is_available() else -1
)

summary = summarizer(
    texts,
    max_length=100,
    min_length=50,
    do_sample=False
)
```

**Used In:**
- Timeline Intelligence summaries
- Positive Developments section
- Critical Alerts section
- Cluster detail pages

---

### 3. Dashboard Features (Detailed)

### 3. Dashboard Features (Detailed)

#### Tab 1: Live Intelligence Hub

**Real-Time Metrics Row:**

1. **Total Documents**
   - Fetches live count from Elasticsearch
   - Query: `GET /news_articles/_count`
   - Updates automatically on page refresh
   
2. **Active Streams**
   - Counts unique sources in last 5 minutes
   - Helps monitor data pipeline health
   
3. **Sentiment Distribution**
   - Pie chart showing positive/negative/neutral split
   - Color-coded: Green (positive), Red (negative), Gray (neutral)
   
4. **Avg Sentiment**
   - Mean sentiment score across all articles
   - Range: -1.0 (very negative) to 1.0 (very positive)
   
5. **Entity Coverage**
   - Total unique entities extracted
   - Indicates data richness

**Timeline Intelligence (Last 24 Hours):**
- **Purpose:** Show recent narrative trends
- **Implementation:**
  ```python
  cutoff_24 = datetime.utcnow() - timedelta(hours=24)
  recent_24h = df[df['timestamp'] > cutoff_24]
  ```
- **Display:**
  - Article count in 24h window
  - 3 key story themes extracted from titles
  - Top 3 actual headlines with bullets
  
**Critical Intelligence Alerts (Negative Sentiment):**
- **Purpose:** Flag concerning narratives
- **Filtering:**
  ```python
  negative_articles = df[df['sentiment'] == 'negative']
  ```
- **Features:**
  - Auto-generated summary using BART
  - Top 3 critical headlines with locations
  - Alert count in red badge
  
**Positive Developments:**
- **Purpose:** Highlight success stories
- **Filtering:**
  ```python
  positive_articles = df[df['sentiment'] == 'positive']
  ```
- **Features:**
  - BART-generated summary of positive trends
  - Top 4 headlines with location tags
  - Success story count in green badge

**Hype vs. Substance Analysis (Clickbait Detection):**

**Algorithm:**
```python
def calculate_hype_score(text, entities):
    word_count = len(text.split())
    entity_count = len(entities)
    
    # Factual density: entities per 10 words
    entity_density = (entity_count / word_count * 10) if word_count > 0 else 0
    
    # Sensationalism detection
    sensationalism = 0
    if any(word in text.lower() for word in ["shocking", "breaking", "exposed"]):
        sensationalism += 2
    if text.isupper() or any(word.isupper() for word in text.split()):
        sensationalism += 1.5
    
    # Hype score: high sensationalism + low factual density = clickbait
    hype_score = max(0, min(10, sensationalism - entity_density))
    
    return hype_score, sensationalism, entity_density
```

**Visualization:**
- **Scatter Plot:** Factual Density (x) vs Sensationalism (y)
- **Quadrants:**
  - Top-left: High hype (clickbait)
  - Bottom-right: High substance (quality journalism)
- **Color:** Red gradient (darker = more clickbait risk)
- **Size:** Bubble size = hype score magnitude

**Clickbait Examples (Synthetic):**
Two pre-defined examples for teacher demonstration:

1. **Extreme Clickbait:**
   - Title: "SHOCKING: You Won't BELIEVE What This Indian Startup CEO Just Revealed..."
   - Summary: Anonymous sources, vague claims, emotional triggers
   - Analysis: Explains ALL CAPS, curiosity gaps, zero facts
   
2. **High Clickbait:**
   - Title: "BREAKING: Tech Industry Secret EXPOSED - What Companies Don't Want You To Know!"
   - Summary: Alleged leaks, conspiracy framing, no verification
   - Analysis: Dramatic language, viral-focused design

**Expander Details:**
- Full title (untruncated)
- Sensationalism score /5.0
- Factual density (entities per 100 words)
- 2-3 line summary
- Clickbait pattern analysis

---

#### Tab 2: Clustering Analysis

**K-Means UMAP Visualization:**

**Interactive Scatter Plot:**
- **X/Y axes:** UMAP dimensions 1 & 2
- **Colors:** 8 distinct cluster colors
- **Markers:** 
  - ● = Regular articles
  - ★ = Cluster centroids
- **Hover:** Shows article title
- **Legend:** Cluster labels (Cluster 0, 1, 2...)

**Sidebar Controls:**
```python
n_clusters = st.slider("Number of Clusters", 5, 15, 8)
data_limit = st.selectbox("Data Points", [100, 500, 1000, 2000, 5000])
```

**Re-clustering Logic:**
1. User adjusts slider → triggers rerun
2. K-Means reinitializes with new K
3. Embeddings re-clustered
4. UMAP recalculates 2D projection
5. Plot updates with new cluster assignments

**Cluster Distribution Chart:**
- **Type:** Bar chart
- **X-axis:** Cluster IDs (0, 1, 2...)
- **Y-axis:** Article count per cluster
- **Color:** Matches scatter plot colors
- **Purpose:** Show cluster balance

**Quality Metrics:**
```python
from sklearn.metrics import silhouette_score

score = silhouette_score(embeddings, cluster_labels)
st.metric("Silhouette Score", f"{score:.3f}")
```

**Interpretation:**
- `0.7-1.0`: Strong, well-separated clusters
- `0.5-0.7`: Reasonable structure
- `0.25-0.5`: Weak structure
- `<0.25`: No meaningful clusters

**Detailed Cluster Breakdown:**

For each cluster:
1. **Cluster Header:** "Cluster X (Y articles)"
2. **BART Summary:** Auto-generated theme description
3. **Sample Articles:** Top 5 with titles, sources, timestamps
4. **Metrics:**
   - Average sentiment
   - Common entities
   - Time distribution

---

#### Tab 3: Geospatial Analysis

**Interactive Folium Map:**

**Implementation:**
```python
import folium
from streamlit_folium import st_folium

m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

for idx, row in df.iterrows():
    if row['locations']:
        loc = row['locations'][0]
        coords = CITY_COORDS.get(loc, [28.6139, 77.2090])  # Default: Delhi
        
        folium.CircleMarker(
            location=coords,
            radius=5,
            popup=f"<b>{row['title'][:50]}</b><br>{row['source']}",
            color='red' if row['sentiment'] == 'negative' else 'green',
            fill=True
        ).add_to(m)

st_folium(m, width=700, height=500)
```

**Features:**
- **Markers:** One per article location
- **Color Coding:**
  - 🔴 Red: Negative sentiment
  - 🟢 Green: Positive sentiment
  - ⚪ Gray: Neutral sentiment
- **Popups:** Click marker → see title, source
- **Pan/Zoom:** Fully interactive
- **Default View:** India-centered

**Choropleth Map:**

**Purpose:** Country-level article aggregation

**City-to-Country Mapping:**
```python
city_to_country = {
    "Mumbai": "India",
    "Delhi": "India",
    "Bengaluru": "India",
    "Dubai": "United Arab Emirates",
    "Singapore": "Singapore",
    # ... more mappings
}
```

**Implementation:**
```python
location_counts = df['locations'].explode().map(city_to_country).value_counts()

fig = px.choropleth(
    location_df,
    locations='country',
    locationmode='country names',
    color='count',
    hover_data=['count'],
    color_continuous_scale='Viridis',
    title='Article Distribution by Country'
)
```

**Features:**
- Darker color = more articles
- Hover shows exact count
- Legend with color scale
- Focus on India, UAE, Singapore

**Location Frequency Table:**
- Top 20 cities by article count
- Bar chart visualization
- Sortable table with counts

---

#### Tab 4: Entity Networks

**Graph Construction:**

**Algorithm:**
```python
import networkx as nx

G = nx.Graph()

for entities in df['entities']:
    entities_list = entities if isinstance(entities, list) else []
    
    # Add nodes
    for ent in entities_list:
        if not G.has_node(ent):
            G.add_node(ent, count=1)
        else:
            G.nodes[ent]['count'] += 1
    
    # Add edges (co-occurrence)
    for i, ent1 in enumerate(entities_list):
        for ent2 in entities_list[i+1:]:
            if G.has_edge(ent1, ent2):
                G[ent1][ent2]['weight'] += 1
            else:
                G.add_edge(ent1, ent2, weight=1)
```

**Visualization:**

**Layout:** Spring layout (force-directed)
```python
pos = nx.spring_layout(G, k=0.5, iterations=50)
```

**Node Properties:**
- **Size:** Proportional to degree centrality
- **Color:** Based on entity type or degree
- **Label:** Entity name (if node large enough)

**Edge Properties:**
- **Width:** Proportional to co-occurrence weight
- **Color:** Light gray, semi-transparent
- **Style:** Straight lines

**Metrics Display:**

**Degree Centrality Ranking:**
```python
centrality = nx.degree_centrality(G)
top_entities = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
```

**Table Columns:**
| Entity | Degree Centrality | Connections |
|--------|-------------------|-------------|
| NITI Aayog | 0.45 | 23 |
| RBI | 0.38 | 19 |
| Reliance | 0.35 | 18 |

**Filters:**
- Minimum connections slider (hide low-degree nodes)
- Entity type filter (ORG, PERSON, GPE)
- Search box for specific entity

**Use Cases:**
- Identify key players (high centrality)
- Find collaboration patterns
- Discover entity clusters (sub-communities)

---

#### Tab 5: Temporal Analysis

**Time Series Visualization:**

**Hourly Article Distribution:**
```python
df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
hourly_counts = df.groupby('hour').size()

fig = px.line(
    x=hourly_counts.index,
    y=hourly_counts.values,
    title='Article Publishing Patterns by Hour',
    labels={'x': 'Hour of Day', 'y': 'Article Count'}
)
```

**Features:**
- X-axis: 0-23 hours
- Y-axis: Article count
- Identifies peak publishing times
- Helps understand news cycles

**Sentiment Over Time:**

**Implementation:**
```python
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp')

fig = px.line(
    df.head(200),  # Recent 200 articles
    x='timestamp',
    y='sentiment_score',
    color='sentiment',
    title='Sentiment Trend Analysis'
)
```

**Color Coding:**
- 🟢 Green line: Positive articles
- 🔴 Red line: Negative articles
- ⚪ Gray line: Neutral articles

**Insights:**
- Sentiment volatility over time
- Positive/negative waves
- Crisis periods (sustained negativity)

**Article Velocity:**
- Articles per hour calculation
- Rolling average (3-hour window)
- Detects traffic spikes
- Useful for anomaly detection

---

## 🚀 Installation & Setup

### Prerequisites

**System Requirements:**
- **OS:** Windows 10/11, macOS, or Linux
- **RAM:** Minimum 8GB (16GB recommended for ML models)
- **Disk:** 5GB free space
- **Python:** 3.8, 3.9, or 3.10
- **Elasticsearch:** 7.x or 8.x running on localhost:9200

**Required Software:**
1. Python 3.8+ with pip
2. Elasticsearch (download from elastic.co)
3. Git (optional)

### Step-by-Step Installation

#### 1. Download/Clone Project

```bash
cd C:\Users\YourName\Desktop
git clone <repository-url> Narrative-Engine
cd Narrative-Engine
```

Or download ZIP and extract.

#### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Key Dependencies:**
```
streamlit==1.28.0
elasticsearch==7.17.9
sentence-transformers==2.2.2
transformers==4.35.0
torch==2.1.0
umap-learn==0.5.4
scikit-learn==1.3.2
spacy==3.7.2
pandas==2.1.3
plotly==5.17.0
folium==0.15.0
streamlit-folium==0.15.0
networkx==3.2
```

#### 4. Download ML Models

```bash
# spaCy English model
python -m spacy download en_core_web_sm

# Sentence transformers (auto-downloads on first run)
# BART summarizer (auto-downloads on first run)
```

#### 5. Start Elasticsearch

**Windows (if installed as service):**
```powershell
# Check if running
curl http://localhost:9200

# If not, start service
net start Elasticsearch
```

**macOS (Homebrew):**
```bash
brew services start elasticsearch
```

**Docker:**
```bash
docker run -d -p 9200:9200 -e "discovery.type=single-node" elasticsearch:7.17.9
```

**Verify Elasticsearch:**
```bash
curl http://localhost:9200
# Should return JSON with cluster info
```

#### 6. Generate Synthetic Data

```bash
cd src/ingestion
python synthetic_to_es.py
```

**Expected Output:**
```
✅ Indexed 1000 synthetic docs with cluster metadata into 'news_articles'.
📊 Includes 80 clickbait articles for Hype vs. Substance analysis.
🎯 Clickbait articles have high sensationalism (4.8) and low factual density (~0.5-0.8).
✨ Regular articles have moderate sensationalism (0-3) and higher factual density (1.5-2.5).
```

**Verify Data:**
```bash
curl http://localhost:9200/news_articles/_count
# Should return: {"count":1000}
```

#### 7. Launch Dashboard

```bash
cd ../..  # Back to project root
streamlit run dashboard_enhanced.py
```

**Dashboard Opens:** http://localhost:8501

**First Load:**
- Loading ML models (30-60 seconds)
- Generating embeddings (20-30 seconds)
- Running UMAP (10-15 seconds)
- Total: ~1-2 minutes first time

**Subsequent Loads:**
- Much faster (models cached)
- ~10-20 seconds

---

## 🎯 Usage Guide

### Basic Workflow

1. **Start Elasticsearch** (if not running)
2. **Generate Data** (first time only): `python src/ingestion/synthetic_to_es.py`
3. **Launch Dashboard**: `streamlit run dashboard_enhanced.py`
4. **Explore Tabs:**
   - Live Intelligence → Overview
   - Clustering → Pattern discovery
   - Geospatial → Location analysis
   - Entity Networks → Relationship mapping
   - Temporal → Time trends

### Advanced Usage

#### Regenerate Data with Different Sentiment Distribution

Edit `src/ingestion/synthetic_to_es.py`:
```python
# Line ~505: Increase positive articles
if sentiment == "positive":
    score = round(random.uniform(0.75, 0.98), 2)  # Even more positive
```

Then regenerate:
```bash
python src/ingestion/synthetic_to_es.py
```

#### Adjust Clustering Parameters

In dashboard sidebar:
1. Move **"Number of Clusters"** slider (5-15)
2. Change **"Data Points"** limit (100, 500, 1000, 2000, 5000)
3. Watch visualization update in real-time

#### Export Data for External Analysis

```python
# In Python console
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])
response = es.search(index='news_articles', size=1000, body={'query': {'match_all': {}}})

# Convert to DataFrame
import pandas as pd
hits = response['hits']['hits']
df = pd.DataFrame([hit['_source'] for hit in hits])
df.to_csv('exported_articles.csv', index=False)
```

---

## 📈 Performance Optimization

### For Large Datasets (>5000 articles)

1. **Increase Data Limit:**
   ```python
   # dashboard_enhanced.py, line ~302
   data_limit = st.selectbox(..., options=[100, 500, 1000, 2000, 5000, 10000])
   ```

2. **Batch Embedding Generation:**
   ```python
   # dashboard_enhanced.py, line ~990
   batch_size = 32
   embeddings = embedder.encode(texts, batch_size=batch_size, show_progress_bar=True)
   ```

3. **Reduce UMAP Neighbors:**
   ```python
   # Line ~1002
   reducer = umap.UMAP(n_neighbors=10, ...)  # Lower from 15
   ```

### For Faster Dashboard Load

1. **Cache ML Models:**
   ```python
   @st.cache_resource
   def load_ml_models():
       # Models cached across reruns
   ```

2. **Cache Embeddings:**
   ```python
   @st.cache_data
   def generate_embeddings(texts):
       # Embeddings cached until texts change
   ```

3. **Limit Initial Data:**
   - Start with 1000 articles
   - Scale up as needed

---

## 🐛 Troubleshooting

### Issue: Elasticsearch Connection Error

**Error:**
```
ConnectionError: Connection to http://localhost:9200 failed
```

**Solutions:**
1. Check if Elasticsearch is running:
   ```bash
   curl http://localhost:9200
   ```
   
2. Start Elasticsearch:
   ```bash
   # Windows
   net start Elasticsearch
   
   # macOS
   brew services start elasticsearch
   
   # Docker
   docker start <elasticsearch-container>
   ```

3. Verify port 9200 not blocked by firewall

---

### Issue: ML Models Not Loading

**Error:**
```
OSError: Can't load model for 'sentence-transformers/all-MiniLM-L6-v2'
```

**Solutions:**
1. Check internet connection (first download)
2. Manually download:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')
   ```
3. Check disk space (models ~400MB each)

---

### Issue: Dashboard Runs Slow

**Symptoms:**
- Long loading times (>2 minutes)
- Laggy interactions
- High CPU/RAM usage

**Solutions:**
1. Reduce data limit to 1000 or 2000
2. Close other applications
3. Use smaller embedding model:
   ```python
   model = SentenceTransformer('all-MiniLM-L6-v2')  # Already smallest
   ```
4. Disable summarization in sidebar
5. Increase system RAM

---

### Issue: No Articles Showing

**Error:**
```
DataFrame is empty, no clusters to display!
```

**Solutions:**
1. Verify data in Elasticsearch:
   ```bash
   curl http://localhost:9200/news_articles/_search?size=1
   ```
   
2. Regenerate data:
   ```bash
   python src/ingestion/synthetic_to_es.py
   ```
   
3. Check index name matches:
   ```python
   # dashboard_enhanced.py, line ~275
   ES_INDEX = "news_articles"
   ```

---

### Issue: UMAP/Clustering Errors

**Error:**
```
ValueError: n_neighbors must be less than n_samples
```

**Solution:**
- Increase data limit above n_neighbors (15)
- Or reduce n_neighbors in code

---

## 📚 Project Structure

```
Narrative-Engine-main/
│
├── dashboard_enhanced.py          # Main Streamlit dashboard (1843 lines)
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── docker-compose.yml             # Infrastructure (optional)
│
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py              # Configuration parameters
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── synthetic_to_es.py     # Data generator (652 lines)
│   │   ├── news_producer.py       # NewsAPI ingestion (optional)
│   │   └── social_producer.py     # Social media sim (optional)
│   │
│   └── processing/
│       ├── __init__.py
│       ├── utils.py               # NLP utilities
│       ├── job_event_detector.py  # Event detection (optional)
│       └── job_entity_tracker.py  # Entity tracking (optional)
│
├── venv/                          # Virtual environment (created by you)
├── __pycache__/                   # Python cache
└── .streamlit/                    # Streamlit config (auto-created)
```

---

## 🎓 Educational Value & Learning Outcomes

### Skills Demonstrated

1. **Natural Language Processing:**
   - Text embeddings with transformers
   - Named Entity Recognition
   - Sentiment analysis
   - Text summarization

2. **Machine Learning:**
   - K-Means clustering
   - Dimensionality reduction (UMAP)
   - Similarity metrics (cosine, Euclidean)
   - Model evaluation (silhouette score)

3. **Data Engineering:**
   - Elasticsearch integration
   - Bulk indexing
   - Real-time querying
   - Data pipeline design

4. **Web Development:**
   - Streamlit dashboard creation
   - Interactive visualizations
   - Real-time updates
   - Multi-page applications

5. **Data Visualization:**
   - Scatter plots (clustering)
   - Geospatial maps (Folium, choropleth)
   - Network graphs (NetworkX)
   - Time series analysis

### Key Concepts

#### 1. Semantic Similarity
Articles with similar meanings have similar embeddings, even if words differ.

**Example:**
- "India launches satellite" → [0.2, 0.8, 0.1, ...]
- "ISRO sends spacecraft" → [0.3, 0.7, 0.2, ...]
- Cosine similarity: 0.95 (very similar)

#### 2. Dimensionality Reduction
Visualizing 384D embeddings requires projection to 2D while preserving structure.

**UMAP Advantage:**
- Preserves both local (nearby points) and global (cluster separation) structure
- Faster than t-SNE
- Configurable via n_neighbors and min_dist

#### 3. Clustering Quality
Not all clusterings are good. Silhouette score measures:
- **Cohesion:** How close articles are within cluster
- **Separation:** How far apart clusters are

**Formula:**
```
silhouette(i) = (b(i) - a(i)) / max(a(i), b(i))

where:
a(i) = avg distance to same-cluster points
b(i) = avg distance to nearest-cluster points
```

#### 4. Entity Networks
Co-occurrence graphs reveal hidden relationships.

**Example:**
- Article 1: [Reliance, NITI Aayog, RBI]
- Article 2: [Reliance, RBI, Serum Institute]
- Article 3: [NITI Aayog, RBI, ISRO]

**Graph:**
```
Reliance ---- RBI ---- NITI Aayog
   |           |            |
   |     Serum Institute   ISRO
```

**Insight:** RBI is central (high degree centrality)

#### 5. Clickbait Detection
Balances two opposing signals:
- **Sensationalism:** Emotional language, ALL CAPS, vague claims
- **Factual Density:** Concrete entities, specific numbers, verifiable facts

**Hype Score Formula:**
```python
hype_score = sensationalism - entity_density

Clickbait: High sensationalism + Low entity density = High hype score
Quality: Low sensationalism + High entity density = Low hype score
```

---

## 🔬 Technical Deep Dives

### How K-Means Finds Optimal Clusters

**Step-by-Step:**

1. **Initialization (k-means++):**
   ```
   - Choose first centroid randomly
   - For each remaining centroid:
     - Choose point farthest from existing centroids
     - Adds diversity, avoids local minima
   ```

2. **Assignment:**
   ```
   For each article embedding:
     - Calculate distance to all 8 centroids
     - Assign to nearest centroid
     - Result: 8 clusters with varying sizes
   ```

3. **Update:**
   ```
   For each cluster:
     - Calculate mean of all assigned embeddings
     - Move centroid to this mean
     - Centroids shift toward cluster centers
   ```

4. **Convergence:**
   ```
   Repeat assign + update until:
     - Centroids stop moving (< 0.0001 change)
     - Or max iterations (300) reached
   ```

**Why It Works:**
- Minimizes within-cluster variance
- Maximizes between-cluster separation
- Guaranteed to converge (to local optimum)

**Limitations:**
- Assumes spherical clusters
- Sensitive to initialization (fixed by k-means++)
- Requires specifying K (we allow 5-15 adjustment)

---

### UMAP Algorithm Internals

**Phase 1: Build High-Dimensional Graph**

```python
For each article embedding:
  1. Find 15 nearest neighbors in 384D space
  2. Calculate distances to neighbors
  3. Convert distances to probabilities:
     P(i→j) = exp(-dist(i,j) / σ_i)
  4. Symmetrize: P(i↔j) = P(i→j) + P(j→i) - P(i→j)*P(j→i)
```

**Result:** Weighted graph where edges = similarity

**Phase 2: Optimize Low-Dimensional Layout**

```python
Initialize 2D positions randomly

For 200 epochs:
  For each edge in high-D graph:
    1. Calculate 2D distance
    2. Attractive force if close in high-D
    3. Repulsive force if far in high-D
    4. Move points to minimize force difference
```

**Objective:** Make 2D distances match high-D probabilities

**Parameters Effect:**
- `n_neighbors=15`: Larger = more global structure preserved
- `min_dist=0.1`: Larger = more spread out clusters
- `metric='cosine'`: Use angular distance, not Euclidean

---

### Entity Co-occurrence Network Construction

**Algorithm:**

```python
G = nx.Graph()

# Step 1: Build nodes
for article in articles:
    entities = extract_entities(article)  # spaCy NER
    
    for entity in entities:
        if entity not in G:
            G.add_node(entity, weight=1)
        else:
            G.nodes[entity]['weight'] += 1  # Frequency

# Step 2: Build edges (co-occurrence)
for article in articles:
    entities = extract_entities(article)
    
    for ent1 in entities:
        for ent2 in entities:
            if ent1 != ent2:
                if G.has_edge(ent1, ent2):
                    G[ent1][ent2]['weight'] += 1
                else:
                    G.add_edge(ent1, ent2, weight=1)

# Step 3: Calculate centrality
centrality = nx.degree_centrality(G)
# degree_centrality(node) = # connections / (total nodes - 1)
```

**Interpretation:**
- **High Centrality (0.7-1.0):** Key player, many connections
- **Medium Centrality (0.3-0.7):** Important secondary actor
- **Low Centrality (<0.3):** Peripheral mention

---

## 🎯 Use Cases & Applications

### 1. News Aggregation Platforms
- Automatically group similar stories
- Detect emerging narratives
- Track story evolution

### 2. Media Monitoring Services
- Client brand mention tracking
- Sentiment analysis for reputation management
- Crisis detection (negative sentiment spikes)

### 3. Research & Academia
- Analyze media coverage of topics
- Study narrative framing
- Track misinformation spread

### 4. Journalism Tools
- Identify underreported stories (small clusters)
- Find connections between entities
- Verify claims with entity networks

### 5. Content Moderation
- Flag clickbait automatically
- Detect sensationalist language
- Promote quality journalism

---

## 🔮 Future Enhancements

### Planned Features

1. **Real-Time Streaming:**
   - Kafka integration for live news feeds
   - Auto-refresh dashboard every 5 minutes
   - WebSocket for push updates

2. **Advanced NLP:**
   - Topic modeling (LDA/BERTopic)
   - Aspect-based sentiment analysis
   - Stance detection (pro/against)

3. **Predictive Analytics:**
   - Story virality prediction
   - Trending topic forecasting
   - Anomaly detection in news flow

4. **Multi-lingual Support:**
   - Hindi, Spanish, French embeddings
   - Language-specific NER
   - Cross-lingual clustering

5. **Export & Reporting:**
   - PDF report generation
   - CSV/Excel data export
   - API endpoints for integration

---

## 📖 References & Resources

### Academic Papers

1. **UMAP:** McInnes, L., Healy, J., & Melville, J. (2018). "UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction."

2. **BERT:** Devlin, J., et al. (2019). "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding."

3. **K-Means++:** Arthur, D., & Vassilvitskii, S. (2007). "k-means++: The Advantages of Careful Seeding."

### Documentation

- **Streamlit:** https://docs.streamlit.io/
- **Sentence Transformers:** https://www.sbert.net/
- **spaCy:** https://spacy.io/usage
- **UMAP:** https://umap-learn.readthedocs.io/
- **Elasticsearch:** https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html
- **NetworkX:** https://networkx.org/documentation/stable/

### Tutorials

- **UMAP for Beginners:** https://pair-code.github.io/understanding-umap/
- **K-Means Clustering:** https://scikit-learn.org/stable/modules/clustering.html#k-means
- **Transformer Models:** https://huggingface.co/course

---

## 📝 License & Attribution

This project is created for educational purposes as part of a capstone project demonstrating:
- Real-time data processing
- Machine learning in production
- Interactive data visualization
- Full-stack data science application

**Technologies Used:**
- Python 3.8+
- Streamlit 1.28
- Elasticsearch 7.x
- sentence-transformers
- PyTorch
- spaCy
- UMAP
- scikit-learn
- NetworkX
- Plotly
- Folium

**Data:**
- Synthetic news articles generated for demonstration
- No real user data collected
- Complies with data privacy standards

---

## 👨‍💻 About the Project

Created as a comprehensive demonstration of:
- **Stream Processing:** Real-time analytics
- **NLP Pipelines:** End-to-end text processing
- **Machine Learning:** Clustering, embeddings, dimensionality reduction
- **Data Visualization:** Interactive, multi-modal displays
- **Full-Stack Development:** Backend (Elasticsearch) + Frontend (Streamlit)

**Author:** Capstone Project - 2025
**Institution:** [Your University]
**Course:** [Your Course Code]

---

## 🙏 Acknowledgments

- **Streamlit Team:** Excellent framework for data apps
- **Hugging Face:** Transformer models and infrastructure
- **Elasticsearch:** Powerful search and analytics engine
- **spaCy Team:** Industrial-strength NLP library
- **UMAP Developers:** Revolutionary dimensionality reduction

---

## 📧 Contact & Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Email: [your.email@example.com]
- Documentation: See this README

---

**Happy Analyzing! 🚀📊🌐**
