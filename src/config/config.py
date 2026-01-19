"""
Configuration file for Narrative Intelligence Engine
Centralizes all configuration parameters for Kafka, Elasticsearch, and APIs
"""

# ============================================
# Kafka Configuration
# ============================================
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_BOOTSTRAP_SERVERS_INTERNAL = ['kafka:9093']  # For Flink jobs inside Docker

# Kafka Topics
TOPIC_RAW_NEWS = 'raw_news'
TOPIC_RAW_SOCIAL = 'raw_social'
TOPIC_DETECTED_EVENTS = 'detected_events'
TOPIC_ENRICHED_NARRATIVES = 'enriched_narratives'

# Kafka Consumer Groups
CONSUMER_GROUP_NEWS = 'news_consumer_group'
CONSUMER_GROUP_SOCIAL = 'social_consumer_group'
CONSUMER_GROUP_EVENTS = 'events_consumer_group'

# ============================================
# Elasticsearch Configuration
# ============================================
ELASTICSEARCH_HOST = 'http://localhost:9200'
ELASTICSEARCH_HOST_INTERNAL = 'http://elasticsearch:9200'  # For Flink jobs inside Docker

# Elasticsearch Indices
ES_INDEX_EVENTS = 'narrative_events'
ES_INDEX_ENRICHED = 'enriched_narratives'

# ============================================
# NewsAPI Configuration
# ============================================
# Get your free API key from: https://newsapi.org/
NEWS_API_KEY = '537d1a5fa7f749c7860c6ddd09a1468a'
NEWS_API_ENDPOINT = 'https://newsapi.org/v2/top-headlines'

# Additional News API Sources (Free alternatives)
# The Guardian API - Get key from: https://open-platform.theguardian.com/
GUARDIAN_API_KEY = 'test'  # Using test key for demo
GUARDIAN_API_ENDPOINT = 'https://content.guardianapis.com/search'

# New York Times API - Get key from: https://developer.nytimes.com/
NYTIMES_API_KEY = 'YOUR_NYTIMES_KEY_HERE'  # Free tier: 1000 calls/day
NYTIMES_API_ENDPOINT = 'https://api.nytimes.com/svc/topstories/v2'

# GNews API - Get key from: https://gnews.io/
GNEWS_API_KEY = 'YOUR_GNEWS_KEY_HERE'  # Free tier: 100 calls/day
GNEWS_API_ENDPOINT = 'https://gnews.io/api/v4/top-headlines'

# Currents API - Get key from: https://currentsapi.services/
CURRENTS_API_KEY = 'YOUR_CURRENTS_KEY_HERE'  # Free tier: 600 calls/day
CURRENTS_API_ENDPOINT = 'https://api.currentsapi.services/v1/latest-news'

# MediaStack API - Get key from: https://mediastack.com/
MEDIASTACK_API_KEY = 'YOUR_MEDIASTACK_KEY_HERE'  # Free tier: 500 calls/month
MEDIASTACK_API_ENDPOINT = 'http://api.mediastack.com/v1/news'

# Bing News API - Get key from: https://azure.microsoft.com/en-us/services/cognitive-services/bing-news-search-api/
BING_NEWS_API_KEY = 'YOUR_BING_KEY_HERE'  # Free tier: 1000 calls/month
BING_NEWS_API_ENDPOINT = 'https://api.bing.microsoft.com/v7.0/news/search'
GNEWS_API_ENDPOINT = 'https://gnews.io/api/v4/top-headlines'

# Currents API - Get key from: https://currentsapi.services/
CURRENTS_API_KEY = 'YOUR_CURRENTS_KEY_HERE'  # Free tier: 600 calls/day
CURRENTS_API_ENDPOINT = 'https://api.currentsapi.services/v1/latest-news'

# MediaStack API - Get key from: https://mediastack.com/
MEDIASTACK_API_KEY = 'YOUR_MEDIASTACK_KEY_HERE'  # Free tier: 500 calls/month
MEDIASTACK_API_ENDPOINT = 'http://api.mediastack.com/v1/news'

# News sources to fetch from
NEWS_SOURCES = [
    'bbc-news',
    'cnn',
    'reuters',
    'the-verge',
    'techcrunch',
    'bloomberg',
    'the-wall-street-journal'
]

# News categories
NEWS_CATEGORIES = ['general', 'technology', 'business', 'science', 'health']

# Fetch interval (seconds)
NEWS_FETCH_INTERVAL = 120  # 2 minutes

# ============================================
# Social Media Simulation Configuration
# ============================================
# Social media post generation rate
SOCIAL_POSTS_PER_SECOND = 10

# Event-related keywords (20% of posts will contain these)
EVENT_KEYWORDS = [
    'Earthquake', 'Tsunami', 'Flood', 'Hurricane',
    'Election', 'Vote', 'Campaign', 'President',
    'Bitcoin', 'Crypto', 'NFT', 'Stock Market',
    'AI', 'ChatGPT', 'Tesla', 'SpaceX',
    'Climate', 'Protest', 'Strike', 'War'
]

# Simulated locations
SOCIAL_LOCATIONS = [
    'New York', 'London', 'Tokyo', 'Mumbai', 'Delhi',
    'Beijing', 'San Francisco', 'Los Angeles', 'Paris',
    'Berlin', 'Sydney', 'Toronto', 'Dubai', 'Singapore'
]

# Social media platforms
SOCIAL_PLATFORMS = ['Twitter', 'Reddit', 'Facebook']

# ============================================
# NLP & ML Configuration
# ============================================
# Sentence Transformer Model
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
EMBEDDING_DIMENSION = 384

# Clustering thresholds
COSINE_SIMILARITY_THRESHOLD = 0.75  # If similarity > 0.75, consider same cluster
NEW_EVENT_THRESHOLD = 0.75  # If max similarity < 0.75, it's a new event

# spaCy model for NER
SPACY_MODEL = 'en_core_web_sm'

# Sentiment analysis thresholds
SENTIMENT_POSITIVE_THRESHOLD = 0.05
SENTIMENT_NEGATIVE_THRESHOLD = -0.05

# ============================================
# Flink Configuration
# ============================================
# Checkpoint configuration
FLINK_CHECKPOINT_INTERVAL = 60000  # 60 seconds
FLINK_CHECKPOINT_DIR = 'file:///tmp/flink-checkpoints'

# State TTL (Time To Live) - 24 hours
FLINK_STATE_TTL_HOURS = 24

# Parallelism
FLINK_PARALLELISM = 2

# ============================================
# Logging Configuration
# ============================================
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ============================================
# Deduplication Configuration
# ============================================
# Time window for deduplication (seconds)
DEDUP_WINDOW_SECONDS = 3600  # 1 hour

# Maximum size of deduplication cache
DEDUP_CACHE_SIZE = 10000
