"""
News Producer - Fetches news from NewsAPI and produces to Kafka
Implements deduplication to avoid sending duplicate articles
"""

import json
import time
import logging
import sys
from datetime import datetime, timedelta
from typing import Set, Dict, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
import requests
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    TOPIC_RAW_NEWS,
    NEWS_API_KEY,
    NEWS_API_ENDPOINT,
    GUARDIAN_API_KEY,
    GUARDIAN_API_ENDPOINT,
    GNEWS_API_KEY,
    GNEWS_API_ENDPOINT,
    CURRENTS_API_KEY,
    CURRENTS_API_ENDPOINT,
    NEWS_SOURCES,
    NEWS_CATEGORIES,
    NEWS_FETCH_INTERVAL,
    DEDUP_CACHE_SIZE,
    LOG_LEVEL,
    LOG_FORMAT
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


class NewsProducer:
    """
    Fetches news from NewsAPI and produces to Kafka with deduplication
    """
    
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
    
    def fetch_news_from_api(self, category: str = 'general') -> list:
        """
        Fetch news from multiple APIs (NewsAPI, Guardian, GNews, Currents)
        
        Args:
            category: News category (general, technology, business, etc.)
            
        Returns:
            List of article dictionaries from all sources
        """
        all_articles = []
        
        # Fetch from NewsAPI (Strictly Indian)
        # Note: Other APIs disabled to enforce "Only Indian Sources" policy
        all_articles.extend(self._fetch_newsapi(category))
        
        # Guardian, GNews, Currents disabled
        # all_articles.extend(self._fetch_guardian(category))
        # all_articles.extend(self._fetch_gnews(category))
        # all_articles.extend(self._fetch_currents(category))
        
        logger.info(f"📰 Total fetched: {len(all_articles)} articles from all sources ({category})")
        return all_articles
    
    def _fetch_newsapi(self, category: str) -> list:
        """Fetch from NewsAPI.org"""
        if NEWS_API_KEY == 'YOUR_NEWSAPI_KEY_HERE':
            return []
        
        try:
            params = {
                'apiKey': NEWS_API_KEY,
                'category': category,
                'country': 'in', # Enforce India
                'pageSize': 50,
                'sortBy': 'publishedAt'
            }
            
            response = requests.get(NEWS_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            
            articles = response.json().get('articles', [])
            logger.info(f"  ✅ NewsAPI: {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.warning(f"  ⚠️ NewsAPI error: {e}")
            return []
    
    def _fetch_guardian(self, category: str) -> list:
        """Fetch from The Guardian API - DISABLED"""
        return []
        
    def _fetch_gnews(self, category: str) -> list:
        """Fetch from GNews API - DISABLED"""
        return []
    
    def _fetch_currents(self, category: str) -> list:
        """Fetch from Currents API - DISABLED"""
        return []
    
    def _generate_mock_news(self, category: str) -> list:
        """Generate mock news articles for testing"""
        mock_articles = [
            {
                "source": {"id": "ndtv", "name": "NDTV"},
                "title": f"Breaking: Major {category} development in Indian markets",
                "description": f"Experts analyze the impact of recent {category} events on economy",
                "url": f"https://ndtv.com/news/{category}/{int(time.time())}",
                "publishedAt": datetime.now().isoformat(),
                "content": f"This is a mock article about {category} for testing purposes."
            },
            {
                "source": {"id": "the-times-of-india", "name": "The Times of India"},
                "title": f"Bengaluru scientists discover breakthrough in {category}",
                "description": f"New findings from IISc could revolutionize {category} industry",
                "url": f"https://timesofindia.indiatimes.com/news/{category}/{int(time.time()) + 1}",
                "publishedAt": datetime.now().isoformat(),
                "content": f"Researchers announce significant progress in {category} field."
            }
        ]
        logger.info(f"📰 Generated {len(mock_articles)} mock articles ({category})")
        return mock_articles
    
    def is_duplicate(self, url: str) -> bool:
        """
        Check if article URL has been seen before
        
        Args:
            url: Article URL
            
        Returns:
            True if duplicate, False otherwise
        """
        if url in self.seen_urls:
            return True
        
        # Add to cache and maintain size limit
        self.seen_urls.add(url)
        if len(self.seen_urls) > DEDUP_CACHE_SIZE:
            # Remove oldest entries (simple FIFO approach)
            self.seen_urls = set(list(self.seen_urls)[-DEDUP_CACHE_SIZE:])
        
        return False
    
    def format_article(self, article: Dict) -> Optional[Dict]:
        """
        Format article into standardized schema
        
        Args:
            article: Raw article from NewsAPI
            
        Returns:
            Formatted article dictionary or None if invalid
        """
        try:
            url = article.get('url', '')
            
            # Skip if duplicate
            if self.is_duplicate(url):
                return None
            
            formatted = {
                "source": article.get('source', {}).get('name', 'Unknown'),
                "title": article.get('title', '').strip(),
                "description": article.get('description', '').strip(),
                "content": article.get('content', '').strip(),
                "url": url,
                "published_at": article.get('publishedAt', datetime.now().isoformat()),
                "author": article.get('author', 'Unknown'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Validate required fields
            if not formatted['title'] or not formatted['url']:
                logger.warning(f"⚠️ Invalid article: missing title or URL")
                return None
            
            return formatted
            
        except Exception as e:
            logger.error(f"❌ Error formatting article: {e}")
            return None
    
    def produce_to_kafka(self, article: Dict) -> bool:
        """
        Send article to Kafka topic
        
        Args:
            article: Formatted article dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            future = self.producer.send(TOPIC_RAW_NEWS, value=article)
            future.get(timeout=10)  # Block until sent
            
            logger.info(f"✅ Sent: {article['title'][:50]}...")
            return True
            
        except KafkaError as e:
            logger.error(f"❌ Kafka error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending to Kafka: {e}")
            return False
    
    def run(self):
        """Main loop - fetch and produce news continuously"""
        logger.info("=" * 80)
        logger.info("🚀 Starting News Producer")
        logger.info(f"📡 Kafka Topic: {TOPIC_RAW_NEWS}")
        logger.info(f"⏱️  Fetch Interval: {NEWS_FETCH_INTERVAL}s")
        logger.info("=" * 80)
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                logger.info(f"\n📊 Fetch Cycle #{cycle}")
                
                total_fetched = 0
                total_sent = 0
                total_duplicates = 0
                
                # Fetch from each category
                for category in NEWS_CATEGORIES:
                    articles = self.fetch_news_from_api(category)
                    total_fetched += len(articles)
                    
                    for article in articles:
                        formatted = self.format_article(article)
                        
                        if formatted is None:
                            total_duplicates += 1
                            continue
                        
                        if self.produce_to_kafka(formatted):
                            total_sent += 1
                
                # Summary
                logger.info(f"\n📈 Cycle Summary:")
                logger.info(f"  Fetched: {total_fetched}")
                logger.info(f"  Sent: {total_sent}")
                logger.info(f"  Duplicates: {total_duplicates}")
                logger.info(f"  Cache Size: {len(self.seen_urls)}")
                
                # Wait before next fetch
                logger.info(f"\n⏳ Sleeping for {NEWS_FETCH_INTERVAL}s...\n")
                time.sleep(NEWS_FETCH_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️ Shutting down News Producer...")
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
                logger.info("✅ Kafka producer closed")


def main():
    """Entry point"""
    producer = NewsProducer()
    producer.run()


if __name__ == "__main__":
    main()
