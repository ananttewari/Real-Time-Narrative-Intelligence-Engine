import json
import random
import time
import argparse
from datetime import datetime, timedelta
from faker import Faker
import numpy as np
from confluent_kafka import Producer
import socket

# Initialize Faker with Indian locale
fake = Faker('en_IN')

# Configuration
KAFKA_BROKER = 'localhost:9092'
TOPIC_NAME = 'raw_news'

# Taxonomy for Stratified Generation
CITIES = ['Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad']
ORGANIZATIONS = [
    'NITI Aayog', 'RBI', 'ISRO', 'DRDO', 'SEBI', 
    'Reliance Industries', 'Tata Group', 'Infosys', 'Wipro', 'HDFC Bank',
    'Indian Oil', 'Coal India', 'SBI'
]
TOPICS = ['Economy', 'Politics', 'Technology', 'Cricket', 'Bollywood', 'Infrastructure', 'Healthcare', 'Education']

# Clickbait/Sensationalism Keywords
CLICKBAIT_PATTERNS = [
    "You won't believe what happened in {}!",
    "Shocking truth about {} revealed!",
    "{} implies massive disaster for {}!",
    "The secret {} doesn't want you to know!",
    "URGENT: {} in crisis!",
    "Exclusive: The dark side of {}!"
]

def create_kafka_producer():
    """Create and return a configured Kafka producer"""
    try:
        conf = {
            'bootstrap.servers': KAFKA_BROKER,
            'client.id': socket.gethostname()
        }
        return Producer(conf)
    except Exception as e:
        print(f"⚠️ Warning: Could not connect to Kafka: {e}")
        print("Running in dry-run mode (printing to stdout only).")
        return None

def delivery_report(err, msg):
    """Callback for Kafka message delivery"""
    if err is not None:
        print(f'Message delivery failed: {err}')
    # else:
    #     print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def generate_article(article_id, is_clickbait=False):
    """Generate a single synthetic article"""
    
    # Core attributes
    city = random.choice(CITIES)
    org = random.choice(ORGANIZATIONS)
    topic = random.choice(TOPICS)
    timestamp = datetime.now() - timedelta(days=random.randint(0, 30), minutes=random.randint(0, 1440))
    
    if is_clickbait:
        # Generate Clickbait (Noise)
        pattern = random.choice(CLICKBAIT_PATTERNS)
        title = pattern.format(city if random.random() > 0.5 else org, topic)
        
        # High sensationalism, low factual density
        content = f"{title.upper()}!!! Experts are shocked. This changes everything for residents of {city}. {fake.sentence()} {fake.sentence()} " \
                  "Share this immediately! " * 3
        
        sensationalism_score = round(random.uniform(0.7, 1.0), 2)
        factual_density = round(random.uniform(0.0, 0.3), 2)
        sentiment_score = round(random.uniform(-0.9, 0.9), 2) # Wild swings
        
    else:
        # Generate Factual News (Signal)
        title = f"{org} announces new initiatives in {city} regarding {topic}"
        if random.random() < 0.3:
            title = f"{topic} update: {city} sees growth in {org} sector"
            
        # Normal news content
        content = f"In a recent development, {org} has unveiled plans to improve {topic.lower()} infrastructure in {city}. " \
                  f"According to official reports, this move is expected to benefit local residents. {fake.text(max_nb_chars=200)} " \
                  f"The project timeline is estimated at 18 months."
        
        sensationalism_score = round(random.uniform(0.0, 0.4), 2)
        factual_density = round(random.uniform(0.6, 1.0), 2)
        
        # More grounded sentiment
        sentiment_prob = random.random()
        if sentiment_prob < 0.4: # Positive
             sentiment_score = round(random.uniform(0.2, 0.8), 2)
        elif sentiment_prob < 0.7: # Neutral
             sentiment_score = round(random.uniform(-0.2, 0.2), 2)
        else: # Negative
             sentiment_score = round(random.uniform(-0.6, -0.2), 2)

    return {
        "id": f"syn_{article_id}",
        "title": title,
        "content": content,
        "published_at": timestamp.isoformat(),
        "source": "SyntheticIN_News",
        "author": fake.name(),
        "url": f"https://synthetic-news.in/{topic.lower()}/{article_id}",
        "category": topic,
        "metadata": {
            "is_synthetic": True,
            "region": city,
            "organization": org,
            "sensationalism_score": sensationalism_score,
            "factual_density": factual_density,
            "precalc_sentiment": sentiment_score
        }
    }

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic news data for Narrative Engine')
    parser.add_argument('--count', type=int, default=1000, help='Number of articles to generate')
    parser.add_argument('--clickbait-ratio', type=float, default=0.08, help='Ratio of clickbait articles (0.0 to 1.0)')
    parser.add_argument('--dry-run', action='store_true', help='Print to stdout instead of sending to Kafka')
    
    args = parser.parse_args()
    
    # Calculate counts
    total_count = args.count
    clickbait_count = int(total_count * args.clickbait_ratio)
    factual_count = total_count - clickbait_count
    
    print(f"🚀 Generating {total_count} articles ({factual_count} factual, {clickbait_count} clickbait)...")
    
    # Create stratified list of types
    types = [False] * factual_count + [True] * clickbait_count
    random.shuffle(types)
    
    producer = None
    if not args.dry_run:
        producer = create_kafka_producer()
    
    start_time = time.time()
    
    for i, is_clickbait in enumerate(types):
        article = generate_article(i, is_clickbait)
        
        json_str = json.dumps(article)
        
        if args.dry_run:
            print(f"[{i+1}/{total_count}] ({'CLICKBAIT' if is_clickbait else 'FACTUAL'}) {article['title']}")
            # print(json_str) 
        else:
            if producer:
                producer.produce(TOPIC_NAME, key=article['id'], value=json_str, callback=delivery_report)
                if i % 100 == 0:
                    producer.poll(0)
    
    if producer:
        print("📦 Flushing Kafka producer...")
        producer.flush()
    
    duration = time.time() - start_time
    print(f"✅ Completed Generation in {duration:.2f} seconds.")

if __name__ == "__main__":
    main()
