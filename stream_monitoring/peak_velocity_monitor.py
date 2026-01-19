"""
Peak Velocity Monitor for Topic Lifecycle Detection
Calculates V_p = max(ΔN/Δt) and measures Detection Lag
"""

import json
import time
import logging
import argparse
from datetime import datetime, timedelta, timezone
from elasticsearch import Elasticsearch
import sys
from collections import defaultdict

from config import (
    ELASTICSEARCH_HOST,
    ES_TARGET_INDEX,
    ES_MONITORING_INDEX,
    VELOCITY_WINDOW_SECONDS,
    VELOCITY_THRESHOLD,
    VELOCITY_POLL_INTERVAL,
    LOG_LEVEL,
    LOG_FORMAT
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


class PeakVelocityMonitor:
    """Monitor semantic cluster velocities and detect breaking news spikes"""
    
    def __init__(self):
        """Initialize Elasticsearch client"""
        self.es = None
        self.cluster_data = defaultdict(lambda: {
            'first_article_time': None,
            'peak_velocity': 0,
            'peak_time': None,
            'detection_lag': None,
            'velocity_history': []
        })
        self.connect_elasticsearch()
    
    def connect_elasticsearch(self):
        """Connect to Elasticsearch"""
        try:
            self.es = Elasticsearch([ELASTICSEARCH_HOST])
            if self.es.ping():
                logger.info(f"✅ Connected to Elasticsearch: {ELASTICSEARCH_HOST}")
            else:
                raise Exception("Elasticsearch ping failed")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
            raise
    
    def get_cluster_velocity(self, cluster_id=None, category=None):
        """
        Calculate cluster ingestion velocity: V_p = ΔN / Δt
        
        Args:
            cluster_id: Specific cluster ID to monitor
            category: Category to filter by
        
        Returns:
            dict: Velocity metrics per cluster
        """
        try:
            # Build query for last window
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=VELOCITY_WINDOW_SECONDS)
            
            # Query for documents in time window
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "ingest_timestamp": {
                                        "gte": window_start.isoformat(),
                                        "lte": now.isoformat()
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            
            # Add cluster/category filter if specified
            if cluster_id is not None:
                query["query"]["bool"]["must"].append({"term": {"cluster_id": cluster_id}})
            if category:
                query["query"]["bool"]["must"].append({"term": {"category": category}})
            
            # Add aggregation by cluster or category
            if cluster_id is None:
                # Aggregate by category (since synthetic data uses category)
                query["aggs"] = {
                    "by_category": {
                        "terms": {
                            "field": "category",
                            "size": 20
                        },
                        "aggs": {
                            "first_article": {
                                "min": {
                                    "field": "ingest_timestamp"
                                }
                            }
                        }
                    }
                }
            
            # Execute query
            response = self.es.search(
                index=ES_TARGET_INDEX,
                body=query,
                size=0  # We only need aggregations
            )
            
            # Calculate velocities
            velocities = {}
            
            if cluster_id is None and "by_category" in response.get("aggregations", {}):
                # Process category aggregations
                for bucket in response["aggregations"]["by_category"]["buckets"]:
                    cat = bucket["key"]
                    count = bucket["doc_count"]
                    
                    # Velocity = docs per minute
                    velocity = (count / VELOCITY_WINDOW_SECONDS) * 60
                    
                    # Get first article timestamp
                    first_timestamp = bucket.get("first_article", {}).get("value_as_string")
                    
                    velocities[cat] = {
                        'count': count,
                        'velocity': velocity,
                        'first_timestamp': first_timestamp,
                        'window_seconds': VELOCITY_WINDOW_SECONDS
                    }
            else:
                # Single cluster/category query
                total_count = response["hits"]["total"]["value"]
                velocity = (total_count / VELOCITY_WINDOW_SECONDS) * 60
                
                key = cluster_id if cluster_id is not None else category
                velocities[key] = {
                    'count': total_count,
                    'velocity': velocity,
                    'window_seconds': VELOCITY_WINDOW_SECONDS
                }
            
            return velocities
            
        except Exception as e:
            logger.error(f"❌ Error calculating velocity: {e}")
            return {}
    
    def get_first_article_time(self, cluster_key):
        """Get timestamp of first article in cluster"""
        try:
            query = {
                "query": {
                    "term": {"category": cluster_key}
                },
                "sort": [
                    {"ingest_timestamp": {"order": "asc"}}
                ],
                "size": 1
            }
            
            response = self.es.search(index=ES_TARGET_INDEX, body=query)
            
            if response["hits"]["total"]["value"] > 0:
                first_doc = response["hits"]["hits"][0]["_source"]
                timestamp_str = first_doc.get("ingest_timestamp")
                if timestamp_str:
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Error getting first article time: {e}")
            return None
    
    def update_peak_velocity(self, cluster_key, velocity, timestamp):
        """
        Update peak velocity for a cluster and calculate detection lag
        
        Args:
            cluster_key: Cluster identifier
            velocity: Current velocity (docs/min)
            timestamp: Current timestamp
        """
        cluster = self.cluster_data[cluster_key]
        
        # Get first article time if not set
        if cluster['first_article_time'] is None:
            first_time = self.get_first_article_time(cluster_key)
            if first_time:
                cluster['first_article_time'] = first_time
                logger.info(f"   📌 {cluster_key}: First article at {first_time.isoformat()}")
        
        # Update peak velocity
        if velocity > cluster['peak_velocity']:
            cluster['peak_velocity'] = velocity
            cluster['peak_time'] = timestamp
            
            # Calculate detection lag if we have first article time
            if cluster['first_article_time']:
                lag_seconds = (timestamp - cluster['first_article_time']).total_seconds()
                cluster['detection_lag'] = lag_seconds
                
                logger.info(f"   🔥 NEW PEAK: {cluster_key} | "
                          f"V_p = {velocity:.1f} docs/min | "
                          f"Detection Lag = {lag_seconds:.1f}s")
        
        # Store velocity in history
        cluster['velocity_history'].append({
            'timestamp': timestamp.isoformat(),
            'velocity': velocity
        })
    
    def monitor_velocities(self, duration_seconds=None, output_file=None):
        """
        Monitor cluster velocities in real-time
        
        Args:
            duration_seconds: How long to monitor (None = indefinite)
            output_file: JSON file to save results
        """
        logger.info("🚀 Starting peak velocity monitoring")
        logger.info(f"   Index: {ES_TARGET_INDEX}")
        logger.info(f"   Window: {VELOCITY_WINDOW_SECONDS}s")
        logger.info(f"   Poll interval: {VELOCITY_POLL_INTERVAL}s")
        logger.info(f"   Velocity threshold: {VELOCITY_THRESHOLD} docs/min")
        if duration_seconds:
            logger.info(f"   Duration: {duration_seconds} seconds")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while True:
                # Check duration
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    logger.info(f"⏱️ Duration reached ({duration_seconds}s), stopping...")
                    break
                
                iteration += 1
                current_time = datetime.now(timezone.utc)
                
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 Velocity Check #{iteration} | {current_time.strftime('%H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # Get velocities for all clusters/categories
                velocities = self.get_cluster_velocity()
                
                if not velocities:
                    logger.info("   No data in current window")
                else:
                    # Display and update
                    logger.info(f"{'Cluster/Category':<25} {'Docs in Window':<18} {'Velocity (docs/min)':<22} {'Status':<15}")
                    logger.info("-" * 80)
                    
                    for cluster_key, metrics in sorted(velocities.items(), key=lambda x: x[1]['velocity'], reverse=True):
                        velocity = metrics['velocity']
                        count = metrics['count']
                        
                        # Update peak velocity tracking
                        self.update_peak_velocity(cluster_key, velocity, current_time)
                        
                        # Determine status
                        if velocity >= VELOCITY_THRESHOLD:
                            status = "🔥 ALERT"
                        elif velocity >= VELOCITY_THRESHOLD * 0.5:
                            status = "⚠️ ELEVATED"
                        else:
                            status = "✅ NORMAL"
                        
                        logger.info(f"{cluster_key:<25} {count:<18} {velocity:<22.1f} {status:<15}")
                    
                    # Show peak velocities
                    logger.info(f"\n📈 Peak Velocities:")
                    logger.info(f"{'Cluster/Category':<25} {'Peak V_p (docs/min)':<25} {'Detection Lag (s)':<20}")
                    logger.info("-" * 70)
                    
                    for cluster_key, data in sorted(self.cluster_data.items(), 
                                                   key=lambda x: x[1]['peak_velocity'], 
                                                   reverse=True)[:10]:
                        peak_v = data['peak_velocity']
                        lag = data['detection_lag']
                        lag_str = f"{lag:.1f}" if lag is not None else "N/A"
                        
                        logger.info(f"{cluster_key:<25} {peak_v:<25.1f} {lag_str:<20}")
                
                # Wait before next check
                time.sleep(VELOCITY_POLL_INTERVAL)
        
        except KeyboardInterrupt:
            logger.info("\n⏹️ Monitoring interrupted by user")
        
        finally:
            # Save results
            if output_file:
                self.save_results(output_file)
            
            # Print final summary
            self.print_summary()
    
    def print_summary(self):
        """Print summary of monitoring session"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 MONITORING SUMMARY")
        logger.info(f"{'='*60}")
        
        if not self.cluster_data:
            logger.info("No clusters monitored")
            return
        
        logger.info(f"\nTotal clusters monitored: {len(self.cluster_data)}")
        logger.info(f"\n{'Cluster/Category':<25} {'Peak V_p':<20} {'Detection Lag':<20} {'Data Points':<15}")
        logger.info("-" * 80)
        
        for cluster_key, data in sorted(self.cluster_data.items(), 
                                       key=lambda x: x[1]['peak_velocity'], 
                                       reverse=True):
            peak_v = data['peak_velocity']
            lag = data['detection_lag']
            lag_str = f"{lag:.1f}s" if lag is not None else "N/A"
            points = len(data['velocity_history'])
            
            logger.info(f"{cluster_key:<25} {peak_v:<20.1f} {lag_str:<20} {points:<15}")
    
    def save_results(self, output_file):
        """Save velocity data to JSON file"""
        try:
            results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'window_seconds': VELOCITY_WINDOW_SECONDS,
                'clusters': {}
            }
            
            for cluster_key, data in self.cluster_data.items():
                results['clusters'][cluster_key] = {
                    'peak_velocity_docs_per_min': data['peak_velocity'],
                    'peak_time': data['peak_time'].isoformat() if data['peak_time'] else None,
                    'first_article_time': data['first_article_time'].isoformat() if data['first_article_time'] else None,
                    'detection_lag_seconds': data['detection_lag'],
                    'velocity_history': data['velocity_history']
                }
            
            import os
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Peak Velocity Monitor for Topic Lifecycle Detection'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=300,  # 5 minutes default
        help='Monitoring duration in seconds (default: 300)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/velocity_data.json',
        help='Output JSON file for results (default: results/velocity_data.json)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize monitor
        monitor = PeakVelocityMonitor()
        
        # Run monitoring
        monitor.monitor_velocities(
            duration_seconds=args.duration,
            output_file=args.output
        )
        
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
