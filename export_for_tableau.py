import pandas as pd
from elasticsearch import Elasticsearch
import time
import os

# Configuration
ES_HOST = "http://localhost:9200"
INDEX_NAME = "enriched_narratives"
OUTPUT_FILE = "tableau_data.csv"

def export_data():
    print(f"🔌 Connecting to Elasticsearch at {ES_HOST}...")
    es = Elasticsearch(ES_HOST)
    
    if not es.ping():
        print("❌ Could not connect to Elasticsearch. Is Docker running?")
        return

    print(f"📥 Fetching data from index '{INDEX_NAME}'...")
    
    # Check if index exists
    if not es.indices.exists(index=INDEX_NAME):
        print(f"⚠️ Index '{INDEX_NAME}' not found. Have you run the pipeline yet?")
        return

    # Fetch all documents (scroll API simplified via size=10000 for demo)
    # For production, use scan/scroll helper
    try:
        resp = es.search(index=INDEX_NAME, query={"match_all": {}}, size=10000)
        hits = resp['hits']['hits']
        print(f"✅ Found {len(hits)} records.")
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return

    if len(hits) == 0:
        print("⚠️ No data found. Run the pipeline (run_pipeline.ps1) and wait a few minutes.")
        return

    # Flatten data
    data = []
    for hit in hits:
        source = hit['_source']
        # Flatten entities if possible, or just take counts
        # This structure depends on your actual data schema, adjusting generic flattening
        row = source.copy()
        
        # Handle specific nested fields if known
        # Example: timestamp normalization
        # row['timestamp'] = source.get('timestamp', '')
        
        data.append(row)

    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"💾 Exported data to: {os.path.abspath(OUTPUT_FILE)}")
    print("👉 improved: Open Tableau Public > Connect to Text File > Select this CSV.")

if __name__ == "__main__":
    export_data()
