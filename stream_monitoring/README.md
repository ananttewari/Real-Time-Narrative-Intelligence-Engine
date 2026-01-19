# Real-Time Performance Monitoring Suite

## Overview

This suite provides comprehensive performance analysis for the Narrative Intelligence Engine's stream processing pipeline, generating two key engineering results for research publication:

1. **Latency vs. Throughput Performance Analysis** - Quantifies end-to-end latency ($L = T_{ES} - T_{Kafka}$) across varying traffic loads
2. **Peak Velocity Detection** - Measures detection lag for breaking news narratives using $V_p = \max(\Delta N / \Delta t)$

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Synthetic Dataset (Elasticsearch: news_articles_batch)     │
│  1,000 pre-generated articles with ML enrichment            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Load Testing Producer (load_testing_producer.py)           │
│  • Injects at 100, 1K, 10K articles/min                     │
│  • Captures T_kafka timestamp                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │  Kafka Topic   │
        │  (raw_news)    │
        └────────┬───────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Latency Monitor (latency_monitor.py)                       │
│  • Consumes from Kafka                                      │
│  • Calculates L = T_es - T_kafka                            │
│  • Indexes to Elasticsearch                                 │
│  • Stores metrics in monitoring_metrics index               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │ Elasticsearch  │
        │ (news_articles)│
        └────────┬───────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Peak Velocity Monitor (peak_velocity_monitor.py)           │
│  • Queries cluster ingestion rates                          │
│  • Calculates V_p = max(ΔN/Δt)                              │
│  • Measures Detection Lag                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Visualization Generator (generate_visualizations.py)        │
│ • Dual-axis latency chart (Matplotlib/Seaborn)              │
│ • Temporal area chart for peak velocity                     │
│ • Publication-ready figures (300 DPI)                       │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Running Services**:
   - Kafka broker on `localhost:9092`
   - Elasticsearch on `localhost:9200`

2. **Data**:
   - Synthetic dataset in `news_articles_batch` index (run `batch_analytics/generate_batch_data.py` if not exists)

3. **Python Dependencies**:
   ```bash
   pip install kafka-python elasticsearch matplotlib seaborn pandas numpy
   ```

## Quick Start

### Option 1: Run Complete Suite (Automatic)

```bash
cd "c:\Users\anant\Downloads\zipped (1)\stream_monitoring"
python run_monitoring_suite.py
```

This will:
- Check prerequisites
- Run load tests at 100, 1K, 10K articles/min
- Monitor latency throughout
- Analyze peak velocities
- Generate all visualizations
- Create summary report

### Option 2: Run Components Individually

#### 1. Load Testing Producer
```bash
# Single throughput level
python load_testing_producer.py --rate 1000 --duration 120

# All throughput levels
python load_testing_producer.py
```

#### 2. Latency Monitor
```bash
# Run for 5 minutes
python latency_monitor.py --duration 300 --output results/latency_data.json

# Run indefinitely (Ctrl+C to stop)
python latency_monitor.py
```

#### 3. Peak Velocity Monitor
```bash
python peak_velocity_monitor.py --duration 300 --output results/velocity_data.json
```

#### 4. Generate Visualizations
```bash
python generate_visualizations.py \
  --latency-data results/latency_data.json \
  --velocity-data results/velocity_data.json \
  --output-dir results
```

## Output Files

All results are saved in the `results/` directory:

- `latency_data.json` - Latency statistics per throughput level
- `velocity_data.json` - Peak velocity metrics per cluster
- `latency_throughput.png` - Dual-axis line chart (Throughput vs Latency)
- `peak_velocity_detection.png` - Temporal area chart with detection lag
- `summary_report.json` - Complete test summary
- `load_test_*.json` - Individual load test results

## Mathematical Formulas

### End-to-End Latency

$$L = T_{ES} - T_{Kafka}$$

Where:
- $T_{Kafka}$ = Producer timestamp (when article sent to Kafka)
- $T_{ES}$ = Elasticsearch ingest timestamp
- $L$ = Latency in milliseconds

### Peak Velocity

$$V_p = \max\left(\frac{\Delta N}{\Delta t}\right)$$

Where:
- $V_p$ = Peak velocity (documents per minute)
- $\Delta N$ = Number of documents in time window
- $\Delta t$ = Time window (default: 60 seconds)

### Detection Lag

$$D_{lag} = T_{peak} - T_{first}$$

Where:
- $T_{first}$ = Timestamp of first article in cluster
- $T_{peak}$ = Timestamp when peak velocity exceeded threshold
- $D_{lag}$ = Detection lag interval (seconds)

## Configuration

Edit `config.py` to customize:

```python
# Throughput levels to test
THROUGHPUT_LEVELS = [100, 1000, 10000]

# Test duration per level
TEST_DURATION_SECONDS = 120

# Velocity monitoring
VELOCITY_WINDOW_SECONDS = 60
VELOCITY_THRESHOLD = 50  # docs/min to trigger alert

# Visualization
FIGURE_DPI = 300  # Publication quality
```

## Expected Results

**Latency Benchmarks** (typical performance):
- 100 art/min: ~50-200ms average latency
- 1,000 art/min: ~200-500ms average latency
- 10,000 art/min: ~500-2000ms average latency

**Peak Velocity**:
- Detection lag typically < 60 seconds for breaking news clusters
- Velocities vary by category (Technology, Sports, etc.)

## Troubleshooting

### "Elasticsearch not responding"
Ensure Elasticsearch is running:
```bash
curl http://localhost:9200
```

### "Kafka connection failed"
Check Kafka broker:
```bash
# Windows PowerShell
netstat -an | Select-String "9092"
```

### "No documents in news_articles_batch"
Generate synthetic dataset:
```bash
cd ../batch_analytics
python generate_batch_data.py --count 1000
```

### Latency monitor not capturing data
Ensure the load testing producer has started and is sending messages. The monitor consumes from `auto_offset_reset='latest'`, so it only captures new messages.

## For Research Paper

Use these visualizations in your paper:

1. **Figure 1**: `latency_throughput.png`
   - Caption: "End-to-End Latency ($L = T_{ES} - T_{Kafka}$) vs. Throughput Analysis. Error bars represent standard deviation across test samples."

2. **Figure 2**: `peak_velocity_detection.png`
   - Caption: "Peak Velocity Detection and Topic Lifecycle Analysis. Top panel shows cumulative document accumulation with marked detection lag interval. Bottom panel displays instantaneous ingestion velocity."

## Citation

Metrics data from `latency_data.json` and `velocity_data.json` can be used to populate tables in your research paper.

## License

Part of the Narrative Intelligence Engine project.
