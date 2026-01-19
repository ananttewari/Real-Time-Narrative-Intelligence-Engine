"""
Flink Job 1: Event Birth Detector
Consumes news from Kafka, vectorizes, clusters, and detects new events
Uses stateful processing with KeyedProcessFunction
"""

import json
import logging
import sys
from datetime import datetime
from typing import Iterator

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor, MapStateDescriptor
from pyflink.common.typeinfo import Types
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors.kafka import (
    KafkaSource,
    KafkaSink,
    KafkaRecordSerializationSchema,
    KafkaOffsetsInitializer
)
from pyflink.common.watermark_strategy import WatermarkStrategy

# Add parent directory to path
sys.path.append('..')
from config.config import (
    KAFKA_BOOTSTRAP_SERVERS_INTERNAL,
    TOPIC_RAW_NEWS,
    TOPIC_DETECTED_EVENTS,
    COSINE_SIMILARITY_THRESHOLD,
    NEW_EVENT_THRESHOLD,
    FLINK_CHECKPOINT_INTERVAL,
    FLINK_PARALLELISM
)
from processing.utils import (
    load_embedding_model,
    cosine_similarity,
    find_most_similar_centroid,
    extract_keywords,
    generate_event_id,
    safe_json_loads,
    safe_json_dumps
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventDetectorFunction(KeyedProcessFunction):
    """
    Stateful function to detect new events from news articles
    Maintains cluster centroids and detects event births
    """
    
    def __init__(self):
        """Initialize the function"""
        self.centroids_state = None
        self.embedding_model = None
    
    def open(self, runtime_context: RuntimeContext):
        """Initialize state and models when function starts"""
        logger.info("🚀 Opening EventDetectorFunction...")
        
        # Initialize state to store cluster centroids
        # Key: event_id, Value: {"centroid": [vector], "keywords": [words], "count": n}
        centroids_descriptor = MapStateDescriptor(
            "centroids",
            Types.STRING(),
            Types.STRING()  # Will store JSON-serialized dict
        )
        self.centroids_state = runtime_context.get_map_state(centroids_descriptor)
        
        # Load embedding model
        logger.info("📚 Loading embedding model...")
        self.embedding_model = load_embedding_model()
        
        if self.embedding_model is None:
            logger.error("❌ Failed to load embedding model!")
            raise RuntimeError("Embedding model required for event detection")
        
        logger.info("✅ EventDetectorFunction ready")
    
    def process_element(self, value, ctx: 'KeyedProcessFunction.Context'):
        """
        Process each news article
        
        Args:
            value: JSON string of news article
            ctx: Processing context
        """
        try:
            # Parse article
            article = safe_json_loads(value)
            if article is None:
                return
            
            title = article.get('title', '')
            if not title:
                return
            
            # Generate embedding for title
            logger.info(f"🔍 Processing: {title[:60]}...")
            vector = self.embedding_model.encode(title).tolist()
            
            # Get current centroids from state
            centroids = {}
            for event_id in self.centroids_state.keys():
                centroid_json = self.centroids_state.get(event_id)
                centroids[event_id] = safe_json_loads(centroid_json)
            
            # Find most similar existing centroid
            centroid_vectors = {
                eid: data['centroid']
                for eid, data in centroids.items()
            }
            
            best_event_id, max_similarity = find_most_similar_centroid(
                vector,
                centroid_vectors
            )
            
            logger.info(f"  Best match: {best_event_id} (similarity: {max_similarity:.3f})")
            
            # Check if this is a NEW EVENT
            if max_similarity < NEW_EVENT_THRESHOLD:
                # NEW EVENT DETECTED!
                new_event_id = generate_event_id()
                keywords = extract_keywords(title)
                
                logger.info(f"🎉 NEW EVENT DETECTED: {new_event_id}")
                logger.info(f"  Keywords: {keywords}")
                
                # Store new centroid in state
                centroid_data = {
                    "centroid": vector,
                    "keywords": keywords,
                    "count": 1,
                    "created_at": datetime.now().isoformat()
                }
                self.centroids_state.put(new_event_id, safe_json_dumps(centroid_data))
                
                # Emit new event
                event = {
                    "event_id": new_event_id,
                    "keywords": keywords,
                    "vector": vector,
                    "title": title,
                    "source": article.get('source', 'Unknown'),
                    "timestamp": datetime.now().isoformat(),
                    "similarity": 0.0,
                    "is_new": True
                }
                
                yield safe_json_dumps(event)
                
            else:
                # Article belongs to existing event - update centroid
                logger.info(f"  Belongs to existing event: {best_event_id}")
                
                # Get existing centroid data
                centroid_data = centroids[best_event_id]
                old_centroid = centroid_data['centroid']
                count = centroid_data['count']
                
                # Update centroid using moving average
                new_count = count + 1
                new_centroid = [
                    (old_c * count + new_c) / new_count
                    for old_c, new_c in zip(old_centroid, vector)
                ]
                
                # Update state
                centroid_data['centroid'] = new_centroid
                centroid_data['count'] = new_count
                self.centroids_state.put(best_event_id, safe_json_dumps(centroid_data))
                
                # Optionally emit update (not a new event)
                # Can be used for tracking event evolution
                
        except Exception as e:
            logger.error(f"❌ Error processing article: {e}", exc_info=True)


def create_event_detector_job():
    """
    Create and configure the Flink job for event detection
    """
    logger.info("=" * 80)
    logger.info("🚀 CREATING EVENT DETECTOR JOB")
    logger.info("=" * 80)
    
    # Create execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(FLINK_PARALLELISM)
    
    # Enable checkpointing
    env.enable_checkpointing(FLINK_CHECKPOINT_INTERVAL)
    
    logger.info(f"✅ Environment configured (parallelism: {FLINK_PARALLELISM})")
    
    # Create Kafka source for raw_news
    kafka_source = KafkaSource.builder() \
        .set_bootstrap_servers(','.join(KAFKA_BOOTSTRAP_SERVERS_INTERNAL)) \
        .set_topics(TOPIC_RAW_NEWS) \
        .set_group_id('event_detector_group') \
        .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()
    
    logger.info(f"✅ Kafka source created: {TOPIC_RAW_NEWS}")
    
    # Create data stream
    news_stream = env.from_source(
        kafka_source,
        WatermarkStrategy.no_watermarks(),
        "News Source"
    )
    
    # Key by a constant to ensure all articles go to same partition
    # This maintains global state for all centroids
    keyed_stream = news_stream.key_by(lambda x: "global")
    
    # Apply event detection function
    detected_events = keyed_stream.process(EventDetectorFunction())
    
    logger.info("✅ Event detector function applied")
    
    # Create Kafka sink for detected_events
    kafka_sink = KafkaSink.builder() \
        .set_bootstrap_servers(','.join(KAFKA_BOOTSTRAP_SERVERS_INTERNAL)) \
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
            .set_topic(TOPIC_DETECTED_EVENTS)
            .set_value_serialization_schema(SimpleStringSchema())
            .build()
        ) \
        .build()
    
    logger.info(f"✅ Kafka sink created: {TOPIC_DETECTED_EVENTS}")
    
    # Sink detected events to Kafka
    detected_events.sink_to(kafka_sink)
    
    logger.info("=" * 80)
    logger.info("✅ Job configured successfully")
    logger.info(f"📥 Input: {TOPIC_RAW_NEWS}")
    logger.info(f"📤 Output: {TOPIC_DETECTED_EVENTS}")
    logger.info("=" * 80)
    
    return env


def main():
    """Entry point"""
    try:
        # Create job
        env = create_event_detector_job()
        
        # Execute job
        logger.info("\n🚀 Starting Event Detector Job...")
        env.execute("Event Birth Detector")
        
    except Exception as e:
        logger.error(f"❌ Job failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
