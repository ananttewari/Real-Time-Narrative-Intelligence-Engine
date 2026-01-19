"""
Configuration for Real-Time Performance Monitoring Suite
"""

# ============================================
# Kafka Configuration
# ============================================
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_TOPIC_RAW_NEWS = 'raw_news'
KAFKA_CONSUMER_GROUP = 'monitoring-suite-consumer'

# ============================================
# Elasticsearch Configuration
# ============================================
ELASTICSEARCH_HOST = 'http://localhost:9200'
ES_SOURCE_INDEX = 'news_articles_batch'  # Synthetic dataset for load testing
ES_TARGET_INDEX = 'news_articles'  # Target index for stream processing
ES_MONITORING_INDEX = 'monitoring_metrics'  # Store monitoring results

# ============================================
# Load Testing Configuration
# ============================================
# Throughput levels (articles per minute)
THROUGHPUT_LEVELS = [100, 1000, 10000]

# Test duration for each throughput level (seconds)
TEST_DURATION_SECONDS = 120  # 2 minutes per test

# ============================================
# Peak Velocity Configuration
# ============================================
# Time window for velocity calculation (seconds)
VELOCITY_WINDOW_SECONDS = 60  # 1 minute

# Velocity threshold to trigger alert (docs/min)
VELOCITY_THRESHOLD = 50

# Polling interval for velocity monitoring (seconds)
VELOCITY_POLL_INTERVAL = 5

# ============================================
# Visualization Configuration
# ============================================
# Output directory for results
RESULTS_DIR = 'results'

# Figure DPI for publication quality
FIGURE_DPI = 300

# Figure size (width, height in inches)
FIGURE_SIZE_LATENCY = (10, 6)
FIGURE_SIZE_VELOCITY = (12, 6)

# ============================================
# Logging Configuration
# ============================================
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
