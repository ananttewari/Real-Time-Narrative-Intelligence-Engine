Write-Host ">>> Launching Narrative Engine Pipeline..." -ForegroundColor Cyan

# 1. Launch News Producer
Write-Host ">>> Starting News Producer (New Window)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\anant\Downloads\Narrative-Engine-main\Narrative-Engine-main'; .\venv\Scripts\python src/ingestion/news_producer.py"

# 2. Launch Social Producer
Write-Host ">>> Starting Social Producer (New Window)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\anant\Downloads\Narrative-Engine-main\Narrative-Engine-main'; .\venv\Scripts\python src/ingestion/social_producer.py"

# 3. Submit Flink Jobs (Running locally for simplicity)
Write-Host ">>> Submitting Event Detector Job (Background)..."

Write-Host ">>> To run the Flink jobs, please use the commands in GUIDE.md or run 'python_job_runner.ps1' if you want to run them locally outside Docker."

Write-Host ">>> Producers started! Check the new windows."
