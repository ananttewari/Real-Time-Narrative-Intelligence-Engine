"""
Load Testing Producer for Kafka
Injects articles from synthetic dataset at variable rates to simulate traffic spikes
"""

import json
import time
import logging
import argparse
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import KafkaError
from elasticsearch import Elasticsearch
import sys

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC_RAW_NEWS,
    ELASTICSEARCH_HOST,
    ES_SOURCE_INDEX,
    THROUGHPUT_LEVELS,
    TEST_DURATION_SECONDS,
    LOG_LEVEL,
    LOG_FORMAT
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


class LoadTestingProducer:
    """Kafka producer for load testing with variable throughput"""
    
    def __init__(self):
        """Initialize Kafka producer and Elasticsearch client"""
        self.producer = None
        self.es = None
        self.articles_cache = []
        self.connect_services()
    
    def connect_services(self):
        """Connect to Kafka and Elasticsearch"""
        try:
            # Connect to Kafka
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"✅ Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
            
            # Connect to Elasticsearch
            self.es = Elasticsearch([ELASTICSEARCH_HOST])
            if self.es.ping():
                logger.info(f"✅ Connected to Elasticsearch: {ELASTICSEARCH_HOST}")
            else:
                raise Exception("Elasticsearch ping failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to services: {e}")
            raise
    
    def load_synthetic_dataset(self, limit=1000):
        """Load articles from Elasticsearch synthetic dataset"""
        try:
            logger.info(f"📥 Loading synthetic dataset from {ES_SOURCE_INDEX}...")
            
            # Query all documents from batch index
            response = self.es.search(
                index=ES_SOURCE_INDEX,
                body={
                    "query": {"match_all": {}},
                    "size": limit,
                    "_source": {
                        "excludes": ["embedding_vector"]  # Exclude large embedding vectors
                    }
                },
                scroll='2m'
            )
            
            # Extract articles
            self.articles_cache = []
            for hit in response['hits']['hits']:
                article = hit['_source']
                article['_es_id'] = hit['_id']
                self.articles_cache.append(article)
            
            # Handle scroll if more results
            scroll_id = response.get('_scroll_id')
            while len(response['hits']['hits']) > 0 and len(self.articles_cache) < limit:
                response = self.es.scroll(scroll_id=scroll_id, scroll='2m')
                for hit in response['hits']['hits']:
                    article = hit['_source']
                    article['_es_id'] = hit['_id']
                    self.articles_cache.append(article)
                    if len(self.articles_cache) >= limit:
                        break
            
            logger.info(f"✅ Loaded {len(self.articles_cache)} articles from synthetic dataset")
            return len(self.articles_cache)
            
        except Exception as e:
            logger.error(f"❌ Failed to load synthetic dataset: {e}")
            raise
    
    def inject_at_rate(self, target_throughput, duration_seconds):
        """
        Inject articles at target throughput rate
        
        Args:
            target_throughput: Articles per minute
            duration_seconds: Duration of the test in seconds
        
        Returns:
            dict: Statistics about the injection
        """
        logger.info(f"🚀 Starting load test: {target_throughput} articles/min for {duration_seconds}s")
        
        # Calculate timing
        articles_per_second = target_throughput / 60.0
        sleep_interval = 1.0 / articles_per_second if articles_per_second > 0 else 0.1
        
        total_articles = int((duration_seconds / 60.0) * target_throughput)
        
        logger.info(f"   Target: {total_articles} total articles")
        logger.info(f"   Rate: {articles_per_second:.2f} articles/second")
        logger.info(f"   Interval: {sleep_interval*1000:.2f}ms between articles")
        
        # Statistics
        sent_count = 0
        error_count = 0
        start_time = time.time()
        latencies = []
        
        try:
            for i in range(total_articles):
                # Get article (cycle through cache if needed)
                article_idx = i % len(self.articles_cache)
                article = self.articles_cache[article_idx].copy()
                
                # Add performance tracking metadata
                kafka_timestamp = datetime.now(timezone.utc).isoformat()
                article['kafka_timestamp'] = kafka_timestamp
                article['test_throughput'] = target_throughput
                article['test_sequence'] = i
                article['load_test_id'] = f"test_{target_throughput}_{int(start_time)}"
                
                # Send to Kafka
                try:
                    send_start = time.time()
                    future = self.producer.send(KAFKA_TOPIC_RAW_NEWS, value=article)
                    future.get(timeout=10)  # Block until sent
                    send_latency = (time.time() - send_start) * 1000  # ms
                    latencies.append(send_latency)
                    sent_count += 1
                    
                    # Log progress every 10% or every 100 articles
                    if sent_count % max(1, total_articles // 10) == 0 or sent_count % 100 == 0:
                        elapsed = time.time() - start_time
                        actual_rate = (sent_count / elapsed) * 60  # articles/min
                        logger.info(f"   Progress: {sent_count}/{total_articles} articles "
                                  f"({sent_count*100//total_articles}%) - "
                                  f"Actual rate: {actual_rate:.1f}/min")
                    
                except KafkaError as e:
                    logger.error(f"❌ Kafka send error: {e}")
                    error_count += 1
                
                # Rate limiting with precise sleep
                if i < total_articles - 1:  # Don't sleep after last article
                    time.sleep(sleep_interval)
                
                # Check if we've exceeded duration (safety check)
                if time.time() - start_time > duration_seconds + 10:
                    logger.warning("⚠️ Test duration exceeded, stopping early")
                    break
            
            # Final statistics
            end_time = time.time()
            actual_duration = end_time - start_time
            actual_throughput = (sent_count / actual_duration) * 60  # articles/min
            
            stats = {
                'target_throughput': target_throughput,
                'duration_seconds': actual_duration,
                'total_sent': sent_count,
                'total_errors': error_count,
                'actual_throughput': actual_throughput,
                'avg_send_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
                'max_send_latency_ms': max(latencies) if latencies else 0,
                'start_time': datetime.fromtimestamp(start_time).isoformat(),
                'end_time': datetime.fromtimestamp(end_time).isoformat()
            }
            
            logger.info(f"✅ Load test completed!")
            logger.info(f"   Sent: {sent_count} articles")
            logger.info(f"   Errors: {error_count}")
            logger.info(f"   Target throughput: {target_throughput} articles/min")
            logger.info(f"   Actual throughput: {actual_throughput:.1f} articles/min")
            logger.info(f"   Avg send latency: {stats['avg_send_latency_ms']:.2f}ms")
            
            return stats
            
        except KeyboardInterrupt:
            logger.info("⏹️ Load test interrupted by user")
            raise
        except Exception as e:
            logger.error(f"❌ Error during load test: {e}")
            raise
    
    def run_all_tests(self):
        """Run load tests at all throughput levels"""
        logger.info("🎯 Running complete load test suite")
        logger.info(f"   Throughput levels: {THROUGHPUT_LEVELS}")
        logger.info(f"   Duration per test: {TEST_DURATION_SECONDS}s")
        
        all_stats = []
        
        for throughput in THROUGHPUT_LEVELS:
            logger.info(f"\n{'='*60}")
            logger.info(f"TEST: {throughput} articles/min")
            logger.info(f"{'='*60}")
            
            stats = self.inject_at_rate(throughput, TEST_DURATION_SECONDS)
            all_stats.append(stats)
            
            # Cool-down period between tests
            if throughput != THROUGHPUT_LEVELS[-1]:
                cooldown = 10
                logger.info(f"⏳ Cool-down period: {cooldown}s before next test...")
                time.sleep(cooldown)
        
        logger.info(f"\n{'='*60}")
        logger.info("🎉 ALL TESTS COMPLETED")
        logger.info(f"{'='*60}")
        
        # Summary table
        logger.info("\n📊 SUMMARY:")
        logger.info(f"{'Target (art/min)':<20} {'Actual (art/min)':<20} {'Total Sent':<15} {'Errors':<10}")
        logger.info("-" * 65)
        for stats in all_stats:
            logger.info(f"{stats['target_throughput']:<20} "
                       f"{stats['actual_throughput']:<20.1f} "
                       f"{stats['total_sent']:<15} "
                       f"{stats['total_errors']:<10}")
        
        return all_stats
    
    def close(self):
        """Close connections"""
        if self.producer:
            self.producer.close()
            logger.info("✅ Kafka producer closed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Load Testing Producer for Kafka Performance Analysis'
    )
    parser.add_argument(
        '--rate',
        type=int,
        help=f'Throughput rate in articles/min. Default: run all tests {THROUGHPUT_LEVELS}'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=TEST_DURATION_SECONDS,
        help=f'Test duration in seconds (default: {TEST_DURATION_SECONDS})'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=1000,
        help='Number of articles to load from synthetic dataset (default: 1000)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize producer
        producer = LoadTestingProducer()
        
        # Load synthetic dataset
        producer.load_synthetic_dataset(limit=args.limit)
        
        # Run test(s)
        if args.rate:
            # Single test at specified rate
            stats = producer.inject_at_rate(args.rate, args.duration)
            print(f"\n📄 Results saved to: results/load_test_{args.rate}.json")
            
            # Save stats
            import os
            os.makedirs('results', exist_ok=True)
            with open(f'results/load_test_{args.rate}.json', 'w') as f:
                json.dump(stats, f, indent=2)
        else:
            # Run all tests
            all_stats = producer.run_all_tests()
            
            # Save all stats
            import os
            os.makedirs('results', exist_ok=True)
            with open('results/load_test_all.json', 'w') as f:
                json.dump(all_stats, f, indent=2)
            print(f"\n📄 Results saved to: results/load_test_all.json")
        
        # Close connections
        producer.close()
        
    except KeyboardInterrupt:
        logger.info("\n👋 Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
