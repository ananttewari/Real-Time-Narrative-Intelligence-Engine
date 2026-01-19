#!/usr/bin/env python
"""Quick ES connectivity test"""
from elasticsearch import Elasticsearch

ES_URL = 'http://localhost:9200'

print("🔍 Testing Elasticsearch connection...")
es = Elasticsearch([ES_URL])

print("✅ Connected!")
print("\nCluster Info:")
info = es.info()
print(f"  Cluster: {info['cluster_name']}")
print(f"  Version: {info['version']['number']}")

print("\nExisting indices:")
indices = es.cat.indices(format='json')
for idx in indices:
    print(f"  - {idx['index']} ({idx['docs.count']} docs)")

if not indices:
    print("  (no indices yet)")
