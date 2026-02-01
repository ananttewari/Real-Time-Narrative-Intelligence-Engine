"""
Export Elasticsearch Data to Local JSON File
Backs up all documents from news_articles index to a local file
"""

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
import json
from datetime import datetime
import sys

# Configuration
ES_HOST = 'http://localhost:9200'
INDEX_NAME = 'news_articles'
OUTPUT_FILE = 'elasticsearch_backup.json'

def export_elasticsearch_data():
    """Export all documents from Elasticsearch to JSON file"""
    try:
        # Connect to Elasticsearch
        es = Elasticsearch([ES_HOST])
        
        # Check connection
        if not es.ping():
            print(f"❌ ERROR: Cannot connect to Elasticsearch at {ES_HOST}")
            print("   Make sure Elasticsearch is running via docker-compose")
            return False
        
        print(f"✅ Connected to Elasticsearch at {ES_HOST}")
        
        # Check if index exists
        if not es.indices.exists(index=INDEX_NAME):
            print(f"❌ ERROR: Index '{INDEX_NAME}' does not exist")
            return False
        
        # Get total document count
        total_docs = es.count(index=INDEX_NAME)['count']
        print(f"📊 Found {total_docs} documents in '{INDEX_NAME}'")
        
        if total_docs == 0:
            print("⚠️  No documents to export")
            return True
        
        # Export all documents using scan (efficient for large datasets)
        print(f"\n📥 Exporting documents to '{OUTPUT_FILE}'...")
        
        documents = []
        for doc in scan(es, index=INDEX_NAME, query={"query": {"match_all": {}}}):
            # Extract the source document (exclude metadata)
            documents.append(doc['_source'])
        
        # Write to JSON file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Successfully exported {len(documents)} documents")
        print(f"📁 File saved: {OUTPUT_FILE}")
        
        # Show file size
        import os
        file_size = os.path.getsize(OUTPUT_FILE)
        size_mb = file_size / (1024 * 1024)
        print(f"📦 File size: {size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  ELASTICSEARCH DATA EXPORT UTILITY")
    print("=" * 60)
    print()
    
    success = export_elasticsearch_data()
    
    if success:
        print("\n✅ Export successful!")
        print(f"\n📋 Summary:")
        print(f"   - Index: {INDEX_NAME}")
        print(f"   - Output: {OUTPUT_FILE}")
        print(f"   - Format: JSON")
        print("\n💡 To restore this data later:")
        print("   python src/ingestion/synthetic_to_es.py")
    else:
        print("\n❌ Export failed.")
        sys.exit(1)
