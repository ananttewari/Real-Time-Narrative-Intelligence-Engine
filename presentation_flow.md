# Real-Time Narrative Intelligence Engine: Presentation Flow

> **Updated**: Final 5-Tab Dashboard | Complete Setup Guide  
> **Duration**: 10-12 minutes | **Audience**: Faculty Presentation

---

## 🎯 Objective
Demonstrate an end-to-end real-time data engineering pipeline that ingests live news, processes it with NLP/ML, and visualizes narrative intelligence instantly.

---

## 🚀 Pre-Presentation Setup (10 Minutes Before)

### Step 1: Start Docker Infrastructure
```powershell
cd "c:\Users\anant\Downloads\SPA Project Updated"
docker-compose up -d
```
*Wait 30 seconds for services to initialize*

**Verify Services**:
- Kafka UI: http://localhost:9000
- Elasticsearch: `curl http://localhost:9200`

### Step 2: Start Producer (Terminal 1)
```powershell
.\.venv\Scripts\Activate.ps1
python src/ingestion/enhanced_news_producer.py
```
*Should show: "✅ Connected to Kafka" and "✅ Sent X articles"*

### Step 3: Start Consumer (Terminal 2)
```powershell
.\.venv\Scripts\Activate.ps1
python elasticsearch_consumer.py
```
*Should show: "✅ Indexed batch: 10 docs"*

### Step 4: Launch Dashboard (Terminal 3)
```powershell
.\.venv\Scripts\Activate.ps1
streamlit run dashboard_enhanced.py
```
*Opens at: http://localhost:8501*

---

## 🎤 Presentation Script (10 Minutes)

### 1. The Hook (1 Minute)
**Show**: Dashboard Tab 1

**Script**:
> "Good morning. This is a real-time narrative intelligence system—it processes thousands of news articles, extracts meaning using NLP, and visualizes the global information landscape in real-time."

---

### 2. System Architecture (1.5 Minutes)
**Script**:
> "Three-layer pipeline:
> 1. **Kafka** streams news from Indian sources (TOI, NDTV, Hindu)
> 2. **Python consumer** with spaCy NER, Transformers embeddings, sentiment analysis
> 3. **Elasticsearch + Streamlit** for storage and real-time visualization"

---

### 3. Proof of Streaming (1.5 Minutes)
**Show**: Terminals + Kafka UI

1. **Producer Terminal**: Point to fetch logs
2. **Kafka UI** (localhost:9000): Show throughput
3. **Consumer Terminal**: Show NLP processing logs

**Script**: 
> "This proves it's not a static dataset—articles flow through Kafka, get processed with NLP, and indexed in milliseconds."

---

### 4. Dashboard Features (5 Minutes)

#### Tab 1: K-Means Clustering (1 min)
**Show**: UMAP scatter plot

**Script**:
> "Sentence embeddings (MiniLM) project articles into 2D semantic space. UMAP visualization shows natural topic clusters—fully unsupervised."

---

#### Tab 2: Text Analysis (1 min)
**Show**: Top Story Topics

**Script**:
> "Entity extraction identifies trending subjects. Aggregates headlines and counts. Breaking Stories section shows high-impact articles. Hype vs. Substance chart detects clickbait."

---

#### Tab 3: Geospatial Map (0.5 min)
**Show**: India location map

**Script**:
> "spaCy NER extracts locations—mapped to show regional narrative concentration."

---

#### Tab 4: Entity Network (1 min)
**Show**: Co-occurrence graph

**Script**:
> "Network of entities appearing together. Node size = centrality. Natural clustering by domain: tech, politics, sports."

---

#### Tab 5: Live Feed (0.5 min)
**Show**: Article stream

**Script**:
> "Raw real-time feed—every article flowing through the pipeline."

---

### 5. Conclusion (30 seconds)
**Script**:
> "Scalable end-to-end streaming pipeline: Kafka → Elasticsearch → ML visualizations. Production-ready real-time intelligence. Thank you."

---

## ❓ Q\u0026A Preparation

**"System latency?"**
> "200-500ms per article: Producer → Kafka → NLP → Elasticsearch"

**"How does clickbait detection work?"**
> "Hype Score = Sensationalism (caps, exclamations, trigger words) - Entity Density (factual substance)"

**"Can it scale?"**
> "Kafka handles 100K+ msgs/sec, Elasticsearch is horizontally scalable, consumers can run in parallel"

**"What NLP models?"**
> "spaCy (en_core_web_sm) for NER, sentence-transformers (MiniLM) for embeddings"

---

## 🆘 Troubleshooting

**Dashboard empty?**
```powershell
python src/ingestion/synthetic_to_es.py
```

**Kafka connection failed?**
```powershell
docker-compose restart kafka
```

**Elasticsearch not responding?**
```powershell
curl http://localhost:9200
docker-compose restart elasticsearch
```

**Import errors?**
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 📊 Bonus: Performance Metrics

If asked about benchmarks, reference:
- `stream_monitoring/results_pdf/latency_throughput.pdf`
- `stream_monitoring/results_pdf/peak_velocity_detection.pdf`

> "Load test results: 50ms latency at 100 art/min → 2000ms at 10K art/min"

---

## ✅ Pre-Presentation Checklist

- [ ] Docker Compose running (`docker ps` shows containers)
- [ ] Producer logging fetches
- [ ] Consumer showing "Indexed batch" messages
- [ ] Dashboard accessible at localhost:8501
- [ ] Kafka UI visible at localhost:9000
- [ ] 100+ articles in Elasticsearch

**Ready to present!** 🚀
