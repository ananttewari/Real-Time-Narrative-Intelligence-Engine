"""
Latency Monitor for Real-Time Performance Analysis
Measures end-to-end latency L = T_es - T_kafka
"""

import json
import time
import logging
import argparse
from datetime import datetime, timezone
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from elasticsearch import Elasticsearch, helpers
import sys
from collections import defaultdict
import statistics

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC_RAW_NEWS,
    KAFKA_CONSUMER_GROUP,
    ELASTICSEARCH_HOST,
    ES_TARGET_INDEX,
    ES_MONITORING_INDEX,
    LOG_LEVEL,
    LOG_FORMAT
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


class LatencyMonitor:
    """Monitor end-to-end latency from Kafka to Elasticsearch"""
    
    def __init__(self):
        """Initialize Kafka consumer and Elasticsearch client"""
        self.consumer = None
        self.es = None
        self.latency_data = defaultdict(list)  # throughput -> [latencies]
        self.message_count = 0
        self.connect_services()
    
    def connect_services(self):
        """Connect to Kafka and Elasticsearch"""
        try:
            # Connect to Kafka Consumer
            self.consumer = KafkaConsumer(
                KAFKA_TOPIC_RAW_NEWS,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_CONSUMER_GROUP,
                auto_offset_reset='latest',  # Start from latest messages
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info(f"✅ Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
            logger.info(f"   Consuming from topic: {KAFKA_TOPIC_RAW_NEWS}")
            
            # Connect to Elasticsearch
            self.es = Elasticsearch([ELASTICSEARCH_HOST])
            if self.es.ping():
                logger.info(f"✅ Connected to Elasticsearch: {ELASTICSEARCH_HOST}")
            else:
                raise Exception("Elasticsearch ping failed")
            
            # Create monitoring index if doesn't exist
            self.create_monitoring_index()
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to services: {e}")
            raise
    
    def create_monitoring_index(self):
        """Create Elasticsearch index for storing monitoring metrics"""
        try:
            if not self.es.indices.exists(index=ES_MONITORING_INDEX):
                mapping = {
                    "mappings": {
                        "properties": {
                            "timestamp": {"type": "date"},
                            "kafka_timestamp": {"type": "date"},
                            "elasticsearch_timestamp": {"type": "date"},
                            "latency_ms": {"type": "float"},
                            "throughput_level": {"type": "integer"},
                            "article_id": {"type": "keyword"},
                            "test_sequence": {"type": "integer"},
                            "load_test_id": {"type": "keyword"}
                        }
                    }
                }
                self.es.indices.create(index=ES_MONITORING_INDEX, body=mapping)
                logger.info(f"✅ Created monitoring index: {ES_MONITORING_INDEX}")
            else:
                logger.info(f"✅ Monitoring index exists: {ES_MONITORING_INDEX}")
        except Exception as e:
            logger.warning(f"⚠️ Could not create monitoring index: {e}")
    
    def calculate_latency(self, article):
        """
        Calculate end-to-end latency: L = T_es - T_kafka
        
        Args:
            article: Article dictionary with kafka_timestamp
        
        Returns:
            float: Latency in milliseconds, or None if calculation fails
        """
        try:
            # Get Kafka timestamp (T_kafka)
            kafka_timestamp_str = article.get('kafka_timestamp')
            if not kafka_timestamp_str:
                return None
            
            # Parse ISO format timestamp
            t_kafka = datetime.fromisoformat(kafka_timestamp_str.replace('Z', '+00:00'))
            
            # Get Elasticsearch ingest timestamp (T_es)
            t_es = datetime.now(timezone.utc)
            
            # Calculate latency in milliseconds
            latency_delta = t_es - t_kafka
            latency_ms = latency_delta.total_seconds() * 1000
            
            return latency_ms
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to calculate latency: {e}")
            return None
    
    def index_to_elasticsearch(self, article, latency_ms):
        """
        Index article to Elasticsearch with ingest timestamp
        
        Args:
            article: Article dictionary
            latency_ms: Calculated latency
        
        Returns:
            bool: Success status
        """
        try:
            # Prepare document with enriched metadata
            doc = article.copy()
            doc['ingest_timestamp'] = datetime.now(timezone.utc).isoformat()
            doc['measured_latency_ms'] = latency_ms
            
            # Index to target index (news_articles)
            self.es.index(
                index=ES_TARGET_INDEX,
                id=doc.get('id', doc.get('_es_id')),
                body=doc
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to index article: {e}")
            return False
    
    def store_latency_metric(self, article, latency_ms):
        """
        Store latency metric in monitoring index
        
        Args:
            article: Article dictionary
            latency_ms: Calculated latency
        """
        try:
            metric_doc = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'kafka_timestamp': article.get('kafka_timestamp'),
                'elasticsearch_timestamp': datetime.now(timezone.utc).isoformat(),
                'latency_ms': latency_ms,
                'throughput_level': article.get('test_throughput'),
                'article_id': article.get('id', article.get('_es_id')),
                'test_sequence': article.get('test_sequence'),
                'load_test_id': article.get('load_test_id')
            }
            
            self.es.index(
                index=ES_MONITORING_INDEX,
                body=metric_doc
            )
            
            # Also store in memory for live statistics
            throughput = article.get('test_throughput')
            if throughput:
                self.latency_data[throughput].append(latency_ms)
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to store latency metric: {e}")
    
    def print_statistics(self):
        """Print current latency statistics"""
        logger.info("\n" + "="*60)
        logger.info("📊 LATENCY STATISTICS (Live)")
        logger.info("="*60)
        
        if not self.latency_data:
            logger.info("No data collected yet")
            return
        
        logger.info(f"{'Throughput (art/min)':<25} {'Avg Latency (ms)':<20} {'Min (ms)':<15} {'Max (ms)':<15} {'Samples':<10}")
        logger.info("-" * 95)
        
        for throughput in sorted(self.latency_data.keys()):
            latencies = self.latency_data[throughput]
            if latencies:
                avg = statistics.mean(latencies)
                min_val = min(latencies)
                max_val = max(latencies)
                count = len(latencies)
                logger.info(f"{throughput:<25} {avg:<20.2f} {min_val:<15.2f} {max_val:<15.2f} {count:<10}")
        
        logger.info("="*60 + "\n")
    
    def run(self, duration_seconds=None, output_file=None):
        """
        Run latency monitoring
        
        Args:
            duration_seconds: How long to monitor (None = indefinite)
            output_file: JSON file to save results
        """
        logger.info("🚀 Starting latency monitoring")
        logger.info(f"   Topic: {KAFKA_TOPIC_RAW_NEWS}")
        logger.info(f"   Target index: {ES_TARGET_INDEX}")
        logger.info(f"   Monitoring index: {ES_MONITORING_INDEX}")
        if duration_seconds:
            logger.info(f"   Duration: {duration_seconds} seconds")
        else:
            logger.info(f"   Duration: Indefinite (Ctrl+C to stop)")
        
        start_time = time.time()
        last_stats_time = start_time
        stats_interval = 30  # Print stats every 30 seconds
        
        try:
            for message in self.consumer:
                # Check duration
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    logger.info(f"⏱️ Duration reached ({duration_seconds}s), stopping...")
                    break
                
                try:
                    article = message.value
                    self.message_count += 1
                    
                    # Calculate latency: L = T_es - T_kafka
                    latency_ms = self.calculate_latency(article)
                    
                    if latency_ms is not None:
                        # Index to Elasticsearch with ingest timestamp
                        self.index_to_elasticsearch(article, latency_ms)
                        
                        # Store latency metric
                        self.store_latency_metric(article, latency_ms)
                        
                        # Log individual measurement
                        if self.message_count % 100 == 0:
                            logger.info(f"   Processed {self.message_count} articles | "
                                      f"Latest latency: {latency_ms:.2f}ms | "
                                      f"Throughput: {article.get('test_throughput', 'N/A')}/min")
                    
                    # Print statistics periodically
                    if time.time() - last_stats_time > stats_interval:
                        self.print_statistics()
                        last_stats_time = time.time()
                    
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    continue
        
        except KeyboardInterrupt:
            logger.info("\n⏹️ Monitoring interrupted by user")
        
        finally:
            # Final statistics
            self.print_statistics()
            
            # Save to file if requested
            if output_file:
                self.save_results(output_file)
            
            logger.info(f"✅ Total messages processed: {self.message_count}")
    
    def save_results(self, output_file):
        """Save latency data to JSON file"""
        try:
            # Convert to serializable format
            results = {
                'total_messages': self.message_count,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'latency_by_throughput': {}
            }
            
            for throughput, latencies in self.latency_data.items():
                if latencies:
                    results['latency_by_throughput'][str(throughput)] = {
                        'count': len(latencies),
                        'avg_ms': statistics.mean(latencies),
                        'min_ms': min(latencies),
                        'max_ms': max(latencies),
                        'median_ms': statistics.median(latencies),
                        'stdev_ms': statistics.stdev(latencies) if len(latencies) > 1 else 0,
                        'samples': latencies[:100]  # Store first 100 samples
                    }
            
            import os
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
    
    def close(self):
        """Close connections"""
        if self.consumer:
            self.consumer.close()
            logger.info("✅ Kafka consumer closed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Latency Monitor for Real-Time Performance Analysis'
    )
    parser.add_argument(
        '--duration',
        type=int,
        help='Monitoring duration in seconds (default: indefinite)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/latency_data.json',
        help='Output JSON file for results (default: results/latency_data.json)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize monitor
        monitor = LatencyMonitor()
        
        # Run monitoring
        monitor.run(duration_seconds=args.duration, output_file=args.output)
        
        # Close connections
        monitor.close()
        
    except KeyboardInterrupt:
        logger.info("\n👋 Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
