# Setup Elasticsearch Local (No Docker)
$ES_VERSION = "8.11.3"
$ZIP_URL = "https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-$ES_VERSION-windows-x86_64.zip"
$DEST_FILE = "elasticsearch-$ES_VERSION.zip"
$EXTRACT_DIR = "elasticsearch_local"

Write-Host "🚀 Setting up Elasticsearch $ES_VERSION locally..." -ForegroundColor Cyan

# 1. Check if already extracted
if (Test-Path "$EXTRACT_DIR\elasticsearch-$ES_VERSION\bin\elasticsearch.bat") {
    Write-Host "✅ Elasticsearch already installed in $EXTRACT_DIR" -ForegroundColor Green
    Write-Host "   To start, run: .\$EXTRACT_DIR\elasticsearch-$ES_VERSION\bin\elasticsearch.bat" -ForegroundColor Yellow
    exit
}

# 2. Download
if (-not (Test-Path $DEST_FILE)) {
    Write-Host "📥 Downloading Elasticsearch (this may take a few minutes)..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $ZIP_URL -OutFile $DEST_FILE
    } catch {
        Write-Error "Failed to download. Please check your internet connection."
        exit
    }
} else {
    Write-Host "✅ Zip file found." -ForegroundColor Green
}

# 3. Extract
Write-Host "📦 Extracting to $EXTRACT_DIR..." -ForegroundColor Yellow
Expand-Archive -Path $DEST_FILE -DestinationPath $EXTRACT_DIR -Force

# 4. Configure to run without Security (for local dev simplicity, optional)
# For batch script simplicity, we'll keep default but warn about HTTPS/Auth
# Or we can disable security to match the code's "http://localhost:9200" expectation.
# The 'batch_analytics' scripts expect HTTP (not HTTPS) and no auth by default.
# We should modify elasticsearch.yml to disable security for this specific dev environment.

$CONFIG_FILE = "$EXTRACT_DIR\elasticsearch-$ES_VERSION\config\elasticsearch.yml"
$CONFIG_CONTENT = @"
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl:
  enabled: false
xpack.security.transport.ssl:
  enabled: false
http.host: 0.0.0.0
discovery.type: single-node
"@

Add-Content -Path $CONFIG_FILE -Value $CONFIG_CONTENT

Write-Host "✅ Configuration updated (Security disabled for local dev)" -ForegroundColor Green
Write-Host "🎉 Setup Complete!" -ForegroundColor Cyan
Write-Host "👉 Run this command to start Elasticsearch:" -ForegroundColor Yellow
Write-Host "   .\$EXTRACT_DIR\elasticsearch-$ES_VERSION\bin\elasticsearch.bat" -ForegroundColor White
