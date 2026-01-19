Write-Host ">>> Launching Narrative Engine Pipeline (LITE MODE)..." -ForegroundColor Green

# 1. Start Docker Containers (Lite)
Write-Host ">>> Starting Docker containers (Lite Configuration)..."
docker-compose -f docker-compose.lite.yml up -d

Write-Host ">>> Waiting for services to initialize..."
Start-Sleep -Seconds 20

# 2. Launch News Producer
Write-Host ">>> Starting News Producer (New Window)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\anant\Downloads\Narrative-Engine-main Updated 2\Narrative-Engine-main'; .\venv\Scripts\python.exe src/ingestion/news_producer.py"

# 3. Launch Social Producer
Write-Host ">>> Starting Social Producer (New Window)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\anant\Downloads\Narrative-Engine-main Updated 2\Narrative-Engine-main'; .\venv\Scripts\python.exe src/ingestion/social_producer.py"

# 4. Launch Elasticsearch Consumer (Ingests data for Dashboard)
Write-Host ">>> Starting Elasticsearch Consumer (New Window)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\anant\Downloads\Narrative-Engine-main Updated 2\Narrative-Engine-main'; .\venv\Scripts\python.exe elasticsearch_consumer.py"

# 5. Launch Streamlit Dashboard
Write-Host ">>> Launching Dashboard (New Window)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\anant\Downloads\Narrative-Engine-main Updated 2\Narrative-Engine-main'; .\venv\Scripts\python.exe -m streamlit run dashboard_enhanced.py"

# 6. Instructions
Write-Host ">>> LITE MODE STARTED!" -ForegroundColor Green
Write-Host "    - Dashboard: http://localhost:8501"
Write-Host "    - Kafka UI: http://localhost:9000"
Write-Host "    - Kibana: http://localhost:5601"
Write-Host ">>> To stop the pipeline, run: docker-compose -f docker-compose.lite.yml down"
