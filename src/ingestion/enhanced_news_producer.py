"""
Enhanced News Producer - Fetches from RSS feeds, NewsAPI, and Guardian
Prioritizes RSS feeds (no API limits) with NewsAPI and Guardian as supplements
"""

import json
import time
import logging
import sys
from datetime import datetime
from typing import Set
from kafka import KafkaProducer
from kafka.errors import KafkaError
import requests
import os
import feedparser

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    TOPIC_RAW_NEWS,
    NEWS_API_KEY,
    GUARDIAN_API_KEY,
    NEWS_FETCH_INTERVAL,
    LOG_LEVEL,
    LOG_FORMAT
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


class EnhancedNewsProducer:
    """Fetches news from multiple RSS feeds and APIs"""
    
    # Indian RSS Feeds
    RSS_FEEDS = {
        'world': [
            'https://timesofindia.indiatimes.com/rssfeedstopstories.cms',  # TOI Top Stories
            'https://feeds.feedburner.com/ndtvnews-top-stories',           # NDTV Top Stories
            'https://www.thehindu.com/news/national/feeder/default.rss',   # The Hindu National
            'https://www.indiatoday.in/rss/1206584',                       # India Today Top Stories
        ],
        'technology': [
            'https://timesofindia.indiatimes.com/rssfeeds/4719148.cms',    # TOI Tech
            'https://www.gadgets360.com/rss/feeds',                        # Gadgets 360
            'https://www.livemint.com/rss/technology',                     # LiveMint Tech
        ],
        'business': [
            'https://timesofindia.indiatimes.com/rssfeeds/1898055.cms',    # TOI Business
            'https://economictimes.indiatimes.com/rssfeedstopstories.cms', # Economic Times
            'https://www.moneycontrol.com/rss/latestnews.xml',             # MoneyControl
        ],
        'general': [
            'https://timesofindia.indiatimes.com/rssfeedstopstories.cms',
            'https://www.news18.com/rss/india.xml',
            'https://zeenews.india.com/rss/india-national-news.xml',
        ]
    }
    
    def __init__(self):
        """Initialize Kafka producer and deduplication cache"""
        self.producer = None
        self.seen_urls: Set[str] = set()
        self.connect_kafka()
    
    def connect_kafka(self):
        """Connect to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"✅ Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
        except KafkaError as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            raise
    
    def fetch_from_rss(self, category: str = 'general') -> list:
        """Fetch articles from RSS feeds"""
        articles = []
        feeds = self.RSS_FEEDS.get(category, self.RSS_FEEDS['general'])
        
        for feed_url in feeds:
            try:
                logger.info(f"  📡 Fetching {feed_url}...")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:15]:  # 15 articles per feed
                    article = {
                        'source': {
                            'id': feed.feed.get('title', 'rss').lower().replace(' ', '-'),
                            'name': feed.feed.get('title', 'RSS Feed')
                        },
                        'author': entry.get('author', 'Unknown'),
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', entry.get('description', ''))[:500],
                        'url': entry.get('link', ''),
                        'urlToImage': entry.get('media_thumbnail', [{}])[0].get('url') if entry.get('media_thumbnail') else None,
                        'publishedAt': entry.get('published', datetime.now().isoformat()),
                        'content': entry.get('summary', entry.get('description', ''))[:1000]
                    }
                    articles.append(article)
                
                logger.info(f"    ✅ {len(feed.entries[:15])} articles")
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"    ⚠️ Error: {e}")
                continue
        
        logger.info(f"  📰 RSS Total: {len(articles)} articles")
        return articles
    
    def fetch_from_newsapi(self, category: str) -> list:
        """Fetch from NewsAPI - Restricted to India"""
        if NEWS_API_KEY == 'YOUR_NEWSAPI_KEY_HERE':
            return []
        
        try:
            url = 'https://newsapi.org/v2/top-headlines'
            params = {
                'apiKey': NEWS_API_KEY,
                'category': category,
                'country': 'in', # Enforce India
                'pageSize': 30
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                logger.info(f"  ✅ NewsAPI: {len(articles)} articles")
                return articles
        except Exception as e:
            logger.warning(f"  ⚠️ NewsAPI error: {e}")
        
        return []
    
    def fetch_from_guardian(self, category: str) -> list:
        """Fetch from Guardian API - DISABLED (Foreign Source)"""
        return []
    
    def fetch_news(self, category: str = 'general') -> list:
        """Fetch from all sources"""
        logger.info(f"🌐 Fetching {category} news from all sources...")
        
        all_articles = []
        
        # RSS feeds (primary source - no limits)
        all_articles.extend(self.fetch_from_rss(category))
        
        # NewsAPI (disabled to ensure only Indian sources)
        # all_articles.extend(self.fetch_from_newsapi(category))
        
        # Guardian (disabled to ensure only Indian sources)
        # all_articles.extend(self.fetch_from_guardian(category))
        
        logger.info(f"📊 Total: {len(all_articles)} articles")
        return all_articles
    
    def is_duplicate(self, article: dict) -> bool:
        """Check if article has been seen before"""
        url = article.get('url', '')
        if url in self.seen_urls:
            return True
        self.seen_urls.add(url)
        
        # Keep cache manageable
        if len(self.seen_urls) > 10000:
            self.seen_urls = set(list(self.seen_urls)[-5000:])
        
        return False
    
    def send_to_kafka(self, article: dict):
        """Send article to Kafka"""
        try:
            # Add processing metadata
            article['ingested_at'] = datetime.now().isoformat()
            article['platform'] = 'news'
            
            future = self.producer.send(TOPIC_RAW_NEWS, value=article)
            future.get(timeout=10)
            
        except Exception as e:
            logger.error(f"❌ Kafka send error: {e}")
    
    def run(self):
        """Main loop: fetch and stream news"""
        logger.info("🚀 Enhanced News Producer started")
        logger.info(f"⏱️  Fetch interval: {NEWS_FETCH_INTERVAL} seconds")
        
        categories = ['world', 'technology', 'business', 'general']
        
        while True:
            try:
                for category in categories:
                    articles = self.fetch_news(category)
                    
                    sent_count = 0
                    dup_count = 0
                    
                    for article in articles:
                        if not self.is_duplicate(article):
                            self.send_to_kafka(article)
                            sent_count += 1
                        else:
                            dup_count += 1
                    
                    logger.info(f"✅ Sent {sent_count} new articles ({dup_count} duplicates)")
                    time.sleep(2)  # Brief pause between categories
                
                logger.info(f"⏳ Waiting {NEWS_FETCH_INTERVAL}s until next fetch...")
                time.sleep(NEWS_FETCH_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("👋 Shutting down...")
                break
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                time.sleep(30)
        
        if self.producer:
            self.producer.close()


if __name__ == "__main__":
    producer = EnhancedNewsProducer()
    producer.run()
