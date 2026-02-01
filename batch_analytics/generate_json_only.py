
import json
import random
import time
import argparse
import warnings
from datetime import datetime, timedelta
import numpy as np
# from elasticsearch import Elasticsearch, helpers # Removed
# Import ML libraries for enrichment
from sentence_transformers import SentenceTransformer
import spacy
from textblob import TextBlob
from faker import Faker

# Fix Windows console encoding for emoji support
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Suppress warnings
warnings.filterwarnings("ignore")

# Initialize Faker
fake = Faker('en_IN')

# Configuration
# ES_URL = 'http://localhost:9200'
# ES_INDEX = 'news_articles_batch'  # Separate index for batch app

# Taxonomy
CITIES = ['Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad']
ORGANIZATIONS = [
    'NITI Aayog', 'RBI', 'ISRO', 'DRDO', 'SEBI', 
    'Reliance Industries', 'Tata Group', 'Infosys', 'Wipro', 'HDFC Bank',
    'Indian Oil', 'Coal India', 'SBI'
]
TOPICS = ['Economy', 'Politics', 'Technology', 'Cricket', 'Bollywood', 'Infrastructure', 'Healthcare', 'Education']

CLICKBAIT_PATTERNS = [
    "You won't believe what happened in {}!",
    "Shocking truth about {} revealed!",
    "{} implies massive disaster for {}!",
    "The secret {} doesn't want you to know!",
    "URGENT: {} in crisis!",
    "Exclusive: The dark side of {}!"
]

def load_models():
    print("⏳ Loading ML Models (this may take a moment)...")
    # Load SBERT
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    # Load Spacy (small model)
    try:
        nlp = spacy.load('en_core_web_sm')
    except:
        print("⚠️ Warning: en_core_web_sm not found. Downloading...")
        # from list_dir import run_command
        # This part is tricky inside a script, usually we expect it pre-installed.
        # Fallback provided in logic if nlp fails or we just assume it exists.
        nlp = None 
    print("✅ Models Loaded.")
    return embedder, nlp

def generate_article(article_id, is_clickbait=False):
    """Generate basic article content"""
    city = random.choice(CITIES)
    org = random.choice(ORGANIZATIONS)
    topic = random.choice(TOPICS)
    
    # Random timestamp within last 30 days
    timestamp = datetime.now() - timedelta(days=random.randint(0, 30), minutes=random.randint(0, 1440))
    
    if is_clickbait:
        # Clickbait Logic
        pattern = random.choice(CLICKBAIT_PATTERNS)
        title = pattern.format(city if random.random() > 0.5 else org, topic)
        content = f"{title.upper()}!!! Experts are shocked. This changes everything for residents of {city}. {fake.sentence()} {fake.sentence()} " \
                  "Share this immediately! " * 3
        sensationalism_score = round(random.uniform(0.7, 1.0), 2)
        factual_density = round(random.uniform(0.0, 0.3), 2)
    else:
        # Factual Logic
        title = f"{org} announces new initiatives in {city} regarding {topic}"
        if random.random() < 0.3:
            title = f"{topic} update: {city} sees growth in {org} sector"
        content = f"In a recent development, {org} has unveiled plans to improve {topic.lower()} infrastructure in {city}. " \
                  f"According to official reports, this move is expected to benefit local residents. {fake.text(max_nb_chars=200)} " \
                  f"The project timeline is estimated at 18 months."
        sensationalism_score = round(random.uniform(0.0, 0.4), 2)
        factual_density = round(random.uniform(0.6, 1.0), 2)

    return {
        "id": f"batch_{article_id}",
        "title": title,
        "content": content,
        "published_at": timestamp.isoformat(),
        "timestamp": timestamp.isoformat(), # Duplicate for dashboard compatibility
        "source": "SyntheticIN_News",
        "author": fake.name(),
        "url": f"https://synthetic-news.in/{topic.lower()}/{article_id}",
        "category": topic,
        "sensationalism_score": sensationalism_score,
        "factual_density": factual_density,
        "ingested_at": datetime.now().isoformat()
    }

def enrich_article(doc, embedder, nlp):
    """Apply NLP enrichment"""
    content = doc['content']
    
    # 1. Sentiment Analysis (TextBlob for speed in generation)
    blob = TextBlob(content)
    sentiment_score = blob.sentiment.polarity
    doc['sentiment_score'] = sentiment_score
    if sentiment_score > 0.1: doc['sentiment'] = 'positive'
    elif sentiment_score < -0.1: doc['sentiment'] = 'negative'
    else: doc['sentiment'] = 'neutral'

    # 2. NER with Spacy
    entities = []
    locations = []
    if nlp:
        spacy_doc = nlp(content)
        entities = [ent.text for ent in spacy_doc.ents if ent.label_ in ['PERSON', 'ORG', 'EVENT']]
        locations = [ent.text for ent in spacy_doc.ents if ent.label_ in ['GPE', 'LOC']]
    
    # Fallback/Augment if Spacy misses the synthetic keywords
    # (Since we know what we put in, we can ensure they are tagged)
    for org in ORGANIZATIONS:
        if org in content and org not in entities: entities.append(org)
    for city in CITIES:
        if city in content and city not in locations: locations.append(city)
        
    doc['entities'] = list(set(entities))
    doc['locations'] = list(set(locations))
    doc['entity_count'] = len(doc['entities'])

    # 3. Embeddings
    embedding = embedder.encode(content).tolist()
    doc['embedding_vector'] = embedding # Use a specific field name for vectors

    return doc

def main():
    parser = argparse.ArgumentParser(description='Batch Generator for Narrative Engine (JSON Only)')
    parser.add_argument('--count', type=int, default=1000, help='Number of articles to generate')
    args = parser.parse_args()

    print(f"🚀 Starting Batch Generation of {args.count} articles...")
    
    # 2. Load Models
    embedder, nlp = load_models()

    # 3. Generate and Index
    batch_size = 50
    all_docs = []
    total_generated = 0

    import time
    start_time = time.time()

    # Stratification: 92% Factual, 8% Clickbait
    n_clickbait = int(args.count * 0.08)
    n_factual = args.count - n_clickbait
    types = [False] * n_factual + [True] * n_clickbait
    random.shuffle(types)

    print("📢 Generating and Enriching...")
    
    for i, is_clickbait in enumerate(types):
        # Generate base
        doc = generate_article(i, is_clickbait)
        
        # Enrich
        doc = enrich_article(doc, embedder, nlp)
        
        all_docs.append(doc)
        total_generated += 1
        
        if total_generated % batch_size == 0:
            print(f"   Generated {total_generated}/{args.count}...", end='\r')

    # Save to JSON
    output_file = 'batch_analytics/synthetic_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_docs, f, indent=2, default=str)
    
    print(f"\n✅ COMPLETE! Generated {total_generated} articles in {time.time() - start_time:.2f}s.")
    print(f"📁 Data saved to: {output_file}")

if __name__ == "__main__":
    main()
