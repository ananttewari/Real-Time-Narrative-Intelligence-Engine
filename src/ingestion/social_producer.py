"""
Social Media Producer - Simulates high-velocity social media streams
Generates fake posts with Faker, 20% containing event-related keywords
"""

import json
import time
import logging
import sys
import random
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from faker import Faker
import uuid
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    TOPIC_RAW_SOCIAL,
    SOCIAL_POSTS_PER_SECOND,
    EVENT_KEYWORDS,
    SOCIAL_LOCATIONS,
    SOCIAL_PLATFORMS,
    LOG_LEVEL,
    LOG_FORMAT
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()


class SocialMediaProducer:
    """
    Simulates high-velocity social media stream
    Generates 10 posts per second with realistic content
    """
    
    def __init__(self):
        """Initialize Kafka producer"""
        self.producer = None
        self.post_count = 0
        self.event_post_count = 0
        self.connect_kafka()
    
    def connect_kafka(self):
        """Connect to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info(f"✅ Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
        except KafkaError as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            raise
    
    def generate_event_related_post(self) -> str:
        """
        Generate a post containing event-related keywords
        20% of all posts should be event-related
        """
        keyword = random.choice(EVENT_KEYWORDS)
        
        templates = [
            f"Breaking: {keyword} alert in the region! Everyone stay safe.",
            f"Just heard about the {keyword}. This is massive!",
            f"Can't believe what's happening with {keyword} right now.",
            f"Latest update on {keyword}: situation is developing rapidly.",
            f"{keyword} news is trending everywhere. What's your take?",
            f"Experts weigh in on {keyword} situation. Thread below 👇",
            f"URGENT: {keyword} confirmed by multiple sources.",
            f"My thoughts on the {keyword} situation: {fake.sentence()}",
            f"{keyword} is dominating headlines today. Here's why...",
            f"Live updates: {keyword} - stay tuned for more information."
        ]
        
        return random.choice(templates)
    
    def generate_generic_post(self) -> str:
        """
        Generate generic social media content
        80% of posts are generic noise
        """
        templates = [
            fake.sentence(),
            f"{fake.sentence()} What do you think?",
            f"Hot take: {fake.sentence()}",
            f"{fake.sentence()} #trending",
            f"Can't stop thinking about {fake.word()}",
            f"{fake.sentence()} Anyone else?",
            f"PSA: {fake.sentence()}",
            f"Just finished {fake.word()}! {fake.sentence()}",
            f"Today's mood: {fake.word()} 😊",
            f"{fake.sentence()} 🔥"
        ]
        
        return random.choice(templates)
    
    def generate_post(self) -> dict:
        """
        Generate a social media post
        20% event-related, 80% generic
        """
        # Decide if this is an event-related post
        is_event_related = random.random() < 0.2
        
        if is_event_related:
            text = self.generate_event_related_post()
            self.event_post_count += 1
        else:
            text = self.generate_generic_post()
        
        # Generate hashtags if event-related, otherwise random small set
        if is_event_related:
            hashtags = [f"#{keyword.replace(' ', '')}" for keyword in text.split() if keyword.istitle()][:3]
        else:
            hashtags = [f"#{fake.word()}" for _ in range(random.randint(0, 2))]

        post = {
            "post_id": str(uuid.uuid4()),
            "platform": random.choice(SOCIAL_PLATFORMS),
            "username": fake.user_name(),
            "content": text,
            "location": random.choice(SOCIAL_LOCATIONS),
            "timestamp": datetime.now().isoformat(),
            "likes": random.randint(0, 10000),
            "retweets": random.randint(0, 1000),
            "is_event_related": is_event_related,
            "hashtags": hashtags
        }
        
        self.post_count += 1
        return post
    
    def produce_to_kafka(self, post: dict) -> bool:
        """
        Send post to Kafka topic
        
        Args:
            post: Social media post dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.producer.send(TOPIC_RAW_SOCIAL, value=post)
            return True
        except KafkaError as e:
            logger.error(f"❌ Kafka error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending to Kafka: {e}")
            return False
    
    def run(self):
        """Main loop - generate and produce posts continuously"""
        logger.info("=" * 80)
        logger.info("🚀 Starting Social Media Producer")
        logger.info(f"📡 Kafka Topic: {TOPIC_RAW_SOCIAL}")
        logger.info(f"⚡ Rate: {SOCIAL_POSTS_PER_SECOND} posts/second")
        logger.info(f"🎯 Event Keywords: {len(EVENT_KEYWORDS)} keywords")
        logger.info("=" * 80)
        
        sleep_interval = 1.0 / SOCIAL_POSTS_PER_SECOND
        start_time = time.time()
        last_report_time = start_time
        
        try:
            while True:
                # Generate and send post
                post = self.generate_post()
                self.produce_to_kafka(post)
                
                # Log sample posts occasionally
                if self.post_count % 100 == 0:
                    # Use new keys `username` and `content`
                    logger.info(f"📱 Sample: [{post['platform']}] {post['username']}: {post['content'][:60]}...")
                
                # Report statistics every 10 seconds
                current_time = time.time()
                if current_time - last_report_time >= 10:
                    elapsed = current_time - start_time
                    rate = self.post_count / elapsed
                    event_percentage = (self.event_post_count / self.post_count * 100) if self.post_count > 0 else 0
                    
                    logger.info(f"\n📊 Statistics:")
                    logger.info(f"  Total Posts: {self.post_count}")
                    logger.info(f"  Event-Related: {self.event_post_count} ({event_percentage:.1f}%)")
                    logger.info(f"  Rate: {rate:.1f} posts/sec")
                    logger.info(f"  Elapsed: {elapsed:.1f}s\n")
                    
                    last_report_time = current_time
                
                # Sleep to maintain rate
                time.sleep(sleep_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️ Shutting down Social Media Producer...")
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
                
                # Final statistics
                elapsed = time.time() - start_time
                logger.info(f"\n📈 Final Statistics:")
                logger.info(f"  Total Posts: {self.post_count}")
                logger.info(f"  Event-Related: {self.event_post_count}")
                logger.info(f"  Duration: {elapsed:.1f}s")
                logger.info(f"  Average Rate: {self.post_count / elapsed:.1f} posts/sec")
                logger.info("✅ Social Media producer closed")


def main():
    """Entry point"""
    producer = SocialMediaProducer()
    producer.run()


if __name__ == "__main__":
    main()
