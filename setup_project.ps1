$ErrorActionPreference = "Stop"
Write-Host "🚀 Starting Narrative Engine Setup..."

if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating Python virtual environment..."
    python -m venv venv
}

Write-Host "⬇️ Installing Python dependencies..."
.\venv\Scripts\pip install -r requirements.txt

Write-Host "🧠 Downloading spaCy English model..."
.\venv\Scripts\python -m spacy download en_core_web_sm

Write-Host "🐳 Starting Docker services..."
docker-compose up -d

Write-Host "⏳ Waiting for Kafka to be ready (30s)..."
Start-Sleep -Seconds 30

Write-Host "📢 Creating Kafka topics..."
docker exec narrative-kafka kafka-topics --create --topic raw_news --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker exec narrative-kafka kafka-topics --create --topic raw_social --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker exec narrative-kafka kafka-topics --create --topic detected_events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker exec narrative-kafka kafka-topics --create --topic enriched_narratives --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists

Write-Host "✅ Setup Complete!"
