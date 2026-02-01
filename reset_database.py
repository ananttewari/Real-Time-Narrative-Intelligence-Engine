"""
Database Reset Script
Clears all documents from Elasticsearch index for a fresh start.
"""

from elasticsearch import Elasticsearch
import sys

# Configuration
ES_HOST = 'http://localhost:9200'
INDEX_NAME = 'news_articles'

def reset_elasticsearch():
    """Delete all documents from the Elasticsearch index"""
    try:
        # Connect to Elasticsearch
        es = Elasticsearch([ES_HOST])
        
        # Check connection
        if not es.ping():
            print("❌ ERROR: Cannot connect to Elasticsearch at", ES_HOST)
            print("   Make sure Elasticsearch is running via docker-compose")
            return False
        
        print(f"✅ Connected to Elasticsearch at {ES_HOST}")
        
        # Check if index exists
        if es.indices.exists(index=INDEX_NAME):
            # Get current document count
            count_before = es.count(index=INDEX_NAME)['count']
            print(f"📊 Current documents in '{INDEX_NAME}': {count_before}")
            
            # Ask for confirmation
            response = input(f"\n⚠️  Are you sure you want to delete all {count_before} documents? (yes/no): ")
            
            if response.lower() != 'yes':
                print("❌ Reset cancelled.")
                return False
            
            # Delete all documents
            print(f"\n🗑️  Deleting all documents from '{INDEX_NAME}'...")
            es.delete_by_query(
                index=INDEX_NAME,
                body={"query": {"match_all": {}}}
            )
            
            # Verify deletion
            count_after = es.count(index=INDEX_NAME)['count']
            print(f"✅ Reset complete! Documents remaining: {count_after}")
            return True
        else:
            print(f"ℹ️  Index '{INDEX_NAME}' does not exist. Nothing to reset.")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  ELASTICSEARCH DATABASE RESET UTILITY")
    print("=" * 60)
    print()
    
    success = reset_elasticsearch()
    
    if success:
        print("\n✅ Database reset successful!")
        print("\nNext steps:")
        print("  1. Run producer: python src/ingestion/enhanced_news_producer.py")
        print("  2. Run consumer: python elasticsearch_consumer.py")
        print("  3. Launch dashboard: streamlit run dashboard_enhanced.py")
    else:
        print("\n❌ Database reset failed.")
        sys.exit(1)
