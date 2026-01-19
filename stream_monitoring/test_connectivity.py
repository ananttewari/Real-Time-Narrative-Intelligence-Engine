"""
Test Script - Verify installation and connectivity
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """Test all required imports"""
    logger.info("Testing Python package imports...")
    
    try:
        import kafka
        logger.info("  ✅ kafka-python")
    except ImportError:
        logger.error("  ❌ kafka-python not installed")
        return False
    
    try:
        import elasticsearch
        logger.info("  ✅ elasticsearch")
    except ImportError:
        logger.error("  ❌ elasticsearch not installed")
        return False
    
    try:
        import matplotlib
        logger.info("  ✅ matplotlib")
    except ImportError:
        logger.error("  ❌ matplotlib not installed")
        return False
    
    try:
        import seaborn
        logger.info("  ✅ seaborn")
    except ImportError:
        logger.error("  ❌ seaborn not installed")
        return False
    
    try:
        import pandas
        logger.info("  ✅ pandas")
    except ImportError:
        logger.error("  ❌ pandas not installed")
        return False
    
    try:
        import numpy
        logger.info("  ✅ numpy")
    except ImportError:
        logger.error("  ❌ numpy not installed")
        return False
    
    logger.info("✅ All imports successful!\n")
    return True


def test_elasticsearch():
    """Test Elasticsearch connection"""
    logger.info("Testing Elasticsearch connection...")
    
    try:
        from elasticsearch import Elasticsearch
        es = Elasticsearch(['http://localhost:9200'])
        
        if not es.ping():
            logger.error("  ❌ Elasticsearch not responding")
            return False
        
        # Get cluster info
        info = es.info()
        logger.info(f"  ✅ Connected to Elasticsearch {info['version']['number']}")
        
        # Check if synthetic dataset exists
        from config import ES_SOURCE_INDEX
        if es.indices.exists(index=ES_SOURCE_INDEX):
            count = es.count(index=ES_SOURCE_INDEX)['count']
            logger.info(f"  ✅ Synthetic dataset '{ES_SOURCE_INDEX}' exists ({count} documents)")
        else:
            logger.warning(f"  ⚠️ Synthetic dataset '{ES_SOURCE_INDEX}' not found")
            logger.warning(f"     Run: cd ../batch_analytics && python generate_batch_data.py")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Elasticsearch connection failed: {e}")
        return False


def test_kafka():
    """Test Kafka connection"""
    logger.info("\nTesting Kafka connection...")
    
    try:
        from kafka import KafkaProducer
        from config import KAFKA_BOOTSTRAP_SERVERS
        
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=5000
        )
        
        # Get topics
        topics = producer.list_topics(timeout=5)
        producer.close()
        
        logger.info(f"  ✅ Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
        logger.info(f"  ✅ Available topics: {len(topics)}")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Kafka connection failed: {e}")
        logger.error(f"     Make sure Kafka is running on {KAFKA_BOOTSTRAP_SERVERS}")
        return False


def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("MONITORING SUITE - CONNECTIVITY TEST")
    logger.info("="*60 + "\n")
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test Elasticsearch
    results.append(("Elasticsearch", test_elasticsearch()))
    
    # Test Kafka
    results.append(("Kafka", test_kafka()))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    all_pass = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name:<20} {status}")
        if not passed:
            all_pass = False
    
    logger.info("="*60)
    
    if all_pass:
        logger.info("\n🎉 All tests passed! You're ready to run the monitoring suite.")
        logger.info("\nNext steps:")
        logger.info("  1. Run full suite: python run_monitoring_suite.py")
        logger.info("  2. Or run components individually (see README.md)")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
