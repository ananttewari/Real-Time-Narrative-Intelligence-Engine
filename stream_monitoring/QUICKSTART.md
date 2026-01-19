# Quick Start Guide - Real-Time Performance Monitoring Suite

## Prerequisites Checklist

Before running the monitoring suite, ensure:

- [ ] Kafka broker running on `localhost:9092`
- [ ] Elasticsearch running on `localhost:9200`
- [ ] Virtual environment activated (`.venv`)
- [ ] Synthetic dataset exists (`news_articles_batch` index)

## Fast Setup (15 minutes)

### Step 1: Verify Services (2 min)

```powershell
# Check Elasticsearch
curl http://localhost:9200

# Check Kafka
netstat -an | Select-String "9092"
```

### Step 2: Activate Virtual Environment (1 min)

```powershell
cd "c:\Users\anant\Downloads\zipped (1)"
.\.venv\Scripts\Activate.ps1
```

### Step 3: Generate Synthetic Data if Needed (3 min)

```powershell
# Check if dataset exists
curl "http://localhost:9200/news_articles_batch/_count"

# If count is 0, generate data:
cd batch_analytics
python generate_batch_data.py --count 1000
cd ..
```

### Step 4: Test Connectivity (1 min)

```powershell
cd stream_monitoring
python test_connectivity.py
```

Expected output:
```
✅ All tests passed! You're ready to run the monitoring suite.
```

### Step 5: Run Complete Suite (10-15 min)

```powershell
python run_monitoring_suite.py
```

This will:
1. Run load tests at 100, 1K, 10K articles/min
2. Monitor latency throughout
3. Analyze peak velocities
4. Generate visualizations
5. Create summary report

### Step 6: Review Results

```powershell
# View generated figures
explorer results\latency_throughput.png
explorer results\peak_velocity_detection.png

# View data
code results\summary_report.json
```

## Troubleshooting

### "Kafka connection failed"
```powershell
# Check if Kafka is running
docker ps | Select-String kafka
# OR
Get-Service | Select-String kafka
```

### "Elasticsearch not responding"
```powershell
# Restart Elasticsearch service or Docker container
docker restart elasticsearch
```

### "No synthetic dataset"
```powershell
cd ..\batch_analytics
python generate_batch_data.py --count 1000
```

### "Import errors"
```powershell
# Ensure venv is activated and dependencies installed
pip install kafka-python elasticsearch matplotlib seaborn
```

## Manual Component Testing

### Test 1: Load Producer Only
```powershell
python load_testing_producer.py --rate 100 --duration 60
```

### Test 2: Latency Monitor Only
```powershell
python latency_monitor.py --duration 120
```

### Test 3: Velocity Monitor Only
```powershell
python peak_velocity_monitor.py --duration 60
```

### Test 4: Visualizations Only
```powershell
# Requires existing JSON data files
python generate_visualizations.py
```

## Output Files

All results saved in `results/` directory:

- ✅ `latency_data.json` - Latency metrics
- ✅ `velocity_data.json` - Velocity metrics
- ✅ `latency_throughput.png` - Figure 1
- ✅ `peak_velocity_detection.png` - Figure 2
- ✅ `summary_report.json` - Complete summary

## For Research Paper

1. Copy figures to paper directory:
   ```powershell
   Copy-Item results\*.png -Destination "path\to\paper\figures\"
   ```

2. Extract metrics from JSON files for tables

3. Use figure captions from `walkthrough.md`

## Estimated Time
- Full suite: 10-15 minutes
- Individual component tests: 2-5 minutes each
- Setup: 5 minutes (first time only)

## Support

See `README.md` for detailed documentation and `walkthrough.md` for complete implementation details.
