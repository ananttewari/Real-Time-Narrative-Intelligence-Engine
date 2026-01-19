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
    
    # RSS Feeds (no API limits, rich geographic content)
    RSS_FEEDS = {
        'world': [
            'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
            'https://feeds.bbci.co.uk/news/world/rss.xml',
            'https://www.theguardian.com/world/rss',
            'https://www.aljazeera.com/xml/rss/all.xml',
            'https://feeds.reuters.com/reuters/topNews',
        ],
        'technology': [
            'https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml',
            'https://feeds.bbci.co.uk/news/technology/rss.xml',
            'https://www.theguardian.com/technology/rss',
        ],
        'business': [
            'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml',
            'https://feeds.bbci.co.uk/news/business/rss.xml',
            'https://www.theguardian.com/business/rss',
            'https://www.cnbc.com/id/100003114/device/rss/rss.html',
        ],
        'general': [
            'http://feeds.abcnews.com/abcnews/topstories',
            'https://feeds.bbci.co.uk/news/rss.xml',
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
        """Fetch from NewsAPI"""
        if NEWS_API_KEY == 'YOUR_NEWSAPI_KEY_HERE':
            return []
        
        try:
            url = 'https://newsapi.org/v2/top-headlines'
            params = {
                'apiKey': NEWS_API_KEY,
                'category': category,
                'language': 'en',
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
        """Fetch from Guardian API"""
        if GUARDIAN_API_KEY in ['YOUR_GUARDIAN_KEY_HERE', None]:
            return []
        
        try:
            section_map = {
                'general': 'world',
                'technology': 'technology',
                'business': 'business',
                'world': 'world'
            }
            
            url = 'https://content.guardianapis.com/search'
            params = {
                'api-key': GUARDIAN_API_KEY,
                'section': section_map.get(category, 'world'),
                'page-size': 20,
                'show-fields': 'headline,bodyText,shortUrl'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                results = response.json().get('response', {}).get('results', [])
                
                articles = []
                for item in results:
                    articles.append({
                        'source': {'id': 'guardian', 'name': 'The Guardian'},
                        'author': 'The Guardian',
                        'title': item.get('webTitle', ''),
                        'description': item.get('fields', {}).get('headline', '')[:500],
                        'url': item.get('webUrl', ''),
                        'urlToImage': None,
                        'publishedAt': item.get('webPublicationDate', ''),
                        'content': item.get('fields', {}).get('bodyText', '')[:1000]
                    })
                
                logger.info(f"  ✅ Guardian: {len(articles)} articles")
                return articles
        except Exception as e:
            logger.warning(f"  ⚠️ Guardian error: {e}")
        
        return []
    
    def fetch_news(self, category: str = 'general') -> list:
        """Fetch from all sources"""
        logger.info(f"🌐 Fetching {category} news from all sources...")
        
        all_articles = []
        
        # RSS feeds (primary source - no limits)
        all_articles.extend(self.fetch_from_rss(category))
        
        # NewsAPI (supplementary)
        all_articles.extend(self.fetch_from_newsapi(category))
        
        # Guardian (supplementary)
        all_articles.extend(self.fetch_from_guardian(category))
        
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
