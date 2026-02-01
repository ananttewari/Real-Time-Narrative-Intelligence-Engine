"""
Local News Producer (No Docker Required)
Fetches real-time news from Indian RSS feeds and writes to a local JSONL file.
"""

import json
import time
import logging
import os
import feedparser
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Output file
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'live_feed.jsonl')

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Indian RSS Feeds
RSS_FEEDS = {
    'top_stories': [
        'https://timesofindia.indiatimes.com/rssfeedstopstories.cms',
        'https://feeds.feedburner.com/ndtvnews-top-stories',
        'https://www.thehindu.com/news/national/feeder/default.rss',
    ],
    'technology': [
        'https://timesofindia.indiatimes.com/rssfeeds/4719148.cms',
        'https://www.gadgets360.com/rss/feeds',
    ],
    'business': [
        'https://timesofindia.indiatimes.com/rssfeeds/1898055.cms',
        'https://economictimes.indiatimes.com/rssfeedstopstories.cms',
    ]
}

def fetch_rss_feed(url, category):
    """Fetch and parse single RSS feed"""
    try:
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:5]:  # Top 5 per feed
            article = {
                'id': entry.get('id', entry.get('link')),
                'title': entry.get('title', ''),
                'description': entry.get('summary', entry.get('description', '')),
                'source': feed.feed.get('title', 'Unknown Source'),
                'url': entry.get('link', ''),
                'published_at': entry.get('published', datetime.now().isoformat()),
                'ingested_at': datetime.now().isoformat(),
                'category': category,
                'sentiment': 'neutral', # Placeholder
                'sentiment_score': 0.0
            }
            articles.append(article)
            
        return articles
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return []

def run_producer():
    logger.info(f"🚀 Starting Local Producer")
    logger.info(f"📂 Writing to: {OUTPUT_FILE}")
    
    seen_ids = set()
    
    # Load existing IDs to avoid duplicates on restart
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        seen_ids.add(data['id'])
                    except: pass
        except Exception as e:
            logger.warning(f"Could not read existing file: {e}")

    try:
        while True:
            logger.info("📡 Fetching new articles...")
            new_count = 0
            
            for category, urls in RSS_FEEDS.items():
                for url in urls:
                    articles = fetch_rss_feed(url, category)
                    
                    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                        for article in articles:
                            if article['id'] not in seen_ids:
                                f.write(json.dumps(article) + '\n')
                                seen_ids.add(article['id'])
                                new_count += 1
                                logger.info(f"  ✅ New: {article['title'][:50]}...")
            
            if new_count > 0:
                logger.info(f"💾 Saved {new_count} new articles to local file.")
            else:
                logger.info("💤 No new articles found.")
                
            logger.info("⏳ Waiting 60 seconds...")
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("🛑 Producer stopped.")

if __name__ == "__main__":
    run_producer()
