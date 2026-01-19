"""
Main Orchestration Script for Real-Time Performance Monitoring Suite
Runs complete test suite: load testing, latency monitoring, velocity tracking, and visualization
"""

import logging
import sys
import time
import subprocess
import json
from pathlib import Path
from datetime import datetime
import threading

from config import (
    THROUGHPUT_LEVELS,
    TEST_DURATION_SECONDS,
    RESULTS_DIR,
    LOG_LEVEL,
    LOG_FORMAT
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


class MonitoringSuite:
    """Orchestrate the complete monitoring suite"""
    
    def __init__(self):
        """Initialize monitoring suite"""
        self.results_dir = Path(RESULTS_DIR)
        self.results_dir.mkdir(exist_ok=True, parents=True)
        self.start_time = None
        self.end_time = None
    
    def check_prerequisites(self):
        """Check if Kafka and Elasticsearch are running"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check Elasticsearch
        try:
            from elasticsearch import Elasticsearch
            es = Elasticsearch(['http://localhost:9200'])
            if not es.ping():
                raise Exception("Elasticsearch not responding")
            logger.info("   ✅ Elasticsearch is running")
            
            # Check if synthetic dataset exists
            from config import ES_SOURCE_INDEX
            count = es.count(index=ES_SOURCE_INDEX)['count']
            if count == 0:
                raise Exception(f"No documents in {ES_SOURCE_INDEX}")
            logger.info(f"   ✅ Synthetic dataset ready ({count} documents)")
            
        except Exception as e:
            logger.error(f"   ❌ Elasticsearch check failed: {e}")
            return False
        
        # Check Kafka
        try:
            from kafka import KafkaProducer
            from config import KAFKA_BOOTSTRAP_SERVERS
            
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                request_timeout_ms=10000
            )
            producer.close()
            logger.info("   ✅ Kafka is running")
            
        except Exception as e:
            logger.error(f"   ❌ Kafka check failed: {e}")
            return False
        
        logger.info("✅ All prerequisites met!\n")
        return True
    
    def run_load_test(self, throughput, duration):
        """
        Run load testing at specified throughput
        
        Args:
            throughput: Articles per minute
            duration: Test duration in seconds
        
        Returns:
            subprocess.CompletedProcess: Result of load test
        """
        logger.info(f"🚀 Starting load test: {throughput} articles/min")
        
        cmd = [
            sys.executable,
            'load_testing_producer.py',
            '--rate', str(throughput),
            '--duration', str(duration)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"   ✅ Load test completed successfully")
        else:
            logger.error(f"   ❌ Load test failed: {result.stderr}")
        
        return result
    
    def run_latency_monitor(self, duration):
        """
        Run latency monitoring in background
        
        Args:
            duration: Monitoring duration in seconds
        
        Returns:
            threading.Thread: Monitor thread
        """
        logger.info(f"📊 Starting latency monitor (duration: {duration}s)")
        
        def monitor_thread():
            cmd = [
                sys.executable,
                'latency_monitor.py',
                '--duration', str(duration),
                '--output', str(self.results_dir / 'latency_data.json')
            ]
            subprocess.run(cmd)
        
        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()
        
        return thread
    
    def run_velocity_monitor(self, duration):
        """
        Run peak velocity monitoring
        
        Args:
            duration: Monitoring duration in seconds
        
        Returns:
            subprocess.CompletedProcess: Result of monitoring
        """
        logger.info(f"📈 Starting peak velocity monitor (duration: {duration}s)")
        
        cmd = [
            sys.executable,
            'peak_velocity_monitor.py',
            '--duration', str(duration),
            '--output', str(self.results_dir / 'velocity_data.json')
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"   ✅ Velocity monitoring completed")
        else:
            logger.error(f"   ❌ Velocity monitoring failed: {result.stderr}")
        
        return result
    
    def generate_visualizations(self):
        """Generate all visualizations"""
        logger.info("🎨 Generating visualizations...")
        
        cmd = [
            sys.executable,
            'generate_visualizations.py',
            '--latency-data', str(self.results_dir / 'latency_data.json'),
            '--velocity-data', str(self.results_dir / 'velocity_data.json'),
            '--output-dir', str(self.results_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("   ✅ Visualizations generated")
        else:
            logger.error(f"   ❌ Visualization failed: {result.stderr}")
        
        return result
    
    def run_complete_suite(self):
        """Run the complete monitoring suite"""
        logger.info("\n" + "="*70)
        logger.info("🎯 REAL-TIME PERFORMANCE MONITORING SUITE")
        logger.info("="*70)
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Throughput levels: {THROUGHPUT_LEVELS}")
        logger.info(f"Duration per test: {TEST_DURATION_SECONDS}s")
        logger.info("="*70 + "\n")
        
        self.start_time = time.time()
        
        # Step 1: Start latency monitor (runs throughout all tests)
        total_duration = len(THROUGHPUT_LEVELS) * (TEST_DURATION_SECONDS + 10)  # +10s cooldown
        monitor_thread = self.run_latency_monitor(total_duration + 30)  # +30s buffer
        
        # Give monitor time to start
        time.sleep(5)
        
        # Step 2: Run load tests at each throughput level
        for i, throughput in enumerate(THROUGHPUT_LEVELS):
            logger.info(f"\n{'='*70}")
            logger.info(f"TEST {i+1}/{len(THROUGHPUT_LEVELS)}: {throughput} articles/min")
            logger.info(f"{'='*70}")
            
            self.run_load_test(throughput, TEST_DURATION_SECONDS)
            
            # Cooldown between tests
            if i < len(THROUGHPUT_LEVELS) - 1:
                cooldown = 10
                logger.info(f"⏳ Cooldown: {cooldown}s...")
                time.sleep(cooldown)
        
        # Step 3: Wait for latency monitor to finish
        logger.info("\n⏳ Waiting for latency monitor to complete...")
        monitor_thread.join(timeout=60)
        
        # Step 4: Run velocity monitoring (analyze collected data)
        logger.info("\n" + "="*70)
        logger.info("PHASE 2: Peak Velocity Analysis")
        logger.info("="*70 + "\n")
        
        # Monitor for shorter duration to analyze the data
        self.run_velocity_monitor(duration=120)  # 2 minutes
        
        # Step 5: Generate visualizations
        logger.info("\n" + "="*70)
        logger.info("PHASE 3: Visualization Generation")
        logger.info("="*70 + "\n")
        
        self.generate_visualizations()
        
        # Step 6: Generate summary report
        self.end_time = time.time()
        self.generate_summary_report()
        
        logger.info("\n" + "="*70)
        logger.info("🎉 MONITORING SUITE COMPLETE!")
        logger.info("="*70)
        logger.info(f"Total execution time: {(self.end_time - self.start_time)/60:.1f} minutes")
        logger.info(f"Results directory: {self.results_dir.absolute()}")
        logger.info("="*70 + "\n")
    
    def generate_summary_report(self):
        """Generate summary report of all tests"""
        logger.info("📝 Generating summary report...")
        
        summary = {
            'execution_time': {
                'start': datetime.fromtimestamp(self.start_time).isoformat(),
                'end': datetime.fromtimestamp(self.end_time).isoformat(),
                'duration_minutes': (self.end_time - self.start_time) / 60
            },
            'test_configuration': {
                'throughput_levels': THROUGHPUT_LEVELS,
                'duration_per_test': TEST_DURATION_SECONDS
            },
            'output_files': {
                'latency_data': str(self.results_dir / 'latency_data.json'),
                'velocity_data': str(self.results_dir / 'velocity_data.json'),
                'latency_chart': str(self.results_dir / 'latency_throughput.png'),
                'velocity_chart': str(self.results_dir / 'peak_velocity_detection.png')
            }
        }
        
        # Try to load and summarize latency data
        try:
            latency_file = self.results_dir / 'latency_data.json'
            if latency_file.exists():
                with open(latency_file, 'r') as f:
                    latency_data = json.load(f)
                summary['latency_summary'] = latency_data.get('latency_by_throughput', {})
        except:
            pass
        
        # Try to load and summarize velocity data
        try:
            velocity_file = self.results_dir / 'velocity_data.json'
            if velocity_file.exists():
                with open(velocity_file, 'r') as f:
                    velocity_data = json.load(f)
                
                # Summarize top 5 clusters by peak velocity
                clusters = velocity_data.get('clusters', {})
                top_clusters = sorted(
                    clusters.items(),
                    key=lambda x: x[1].get('peak_velocity_docs_per_min', 0),
                    reverse=True
                )[:5]
                
                summary['velocity_summary'] = {
                    cluster: {
                        'peak_velocity': data['peak_velocity_docs_per_min'],
                        'detection_lag': data.get('detection_lag_seconds')
                    }
                    for cluster, data in top_clusters
                }
        except:
            pass
        
        # Save summary
        summary_file = self.results_dir / 'summary_report.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"   ✅ Summary saved: {summary_file}")
        
        # Print key findings
        logger.info("\n" + "="*70)
        logger.info("📊 KEY FINDINGS")
        logger.info("="*70)
        
        if 'latency_summary' in summary:
            logger.info("\nLatency Analysis (L = T_es - T_kafka):")
            for throughput, metrics in sorted(summary['latency_summary'].items(), 
                                             key=lambda x: int(x[0])):
                logger.info(f"   {throughput} art/min: Avg = {metrics['avg_ms']:.1f}ms, "
                          f"Min = {metrics['min_ms']:.1f}ms, Max = {metrics['max_ms']:.1f}ms")
        
        if 'velocity_summary' in summary:
            logger.info("\nTop Peak Velocities (V_p = max(ΔN/Δt)):")
            for cluster, metrics in summary['velocity_summary'].items():
                lag_str = f"{metrics['detection_lag']:.1f}s" if metrics['detection_lag'] else "N/A"
                logger.info(f"   {cluster}: V_p = {metrics['peak_velocity']:.1f} docs/min, "
                          f"Detection Lag = {lag_str}")
        
        logger.info("="*70)


def main():
    """Main entry point"""
    try:
        suite = MonitoringSuite()
        
        # Check prerequisites
        if not suite.check_prerequisites():
            logger.error("❌ Prerequisites not met. Please ensure Kafka and Elasticsearch are running.")
            return 1
        
        # Run complete suite
        suite.run_complete_suite()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n👋 Suite interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
