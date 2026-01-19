#!/usr/bin/env python
"""Quick test: Can we fetch data using requests instead of ES client?"""
import requests
import pandas as pd

ES_URL = "http://localhost:9200"
ES_INDEX = "news_articles_batch"

print("Testing direct HTTP access to ES...")

# Try the search endpoint
try:
    query = {"size": 10, "query": {"match_all": {}}}
    response = requests.post(f"{ES_URL}/{ES_INDEX}/_search", json=query, timeout=5)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        hits = data['hits']['hits']
        print(f"✅ Found {len(hits)} articles!")
        print(f"Total in index: {data['hits']['total']['value']}")
        
        # Sample article
        if hits:
            sample = hits[0]['_source']
            print(f"\nSample article:")
            print(f"  Title: {sample.get('title', 'N/A')[:60]}...")
            print(f"  Category: {sample.get('category', 'N/A')}")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Failed: {e}")
