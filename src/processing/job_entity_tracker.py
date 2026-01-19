"""
Flink Job 2: Entity & Narrative Tracker
Stream-stream join between detected events and social media posts
Enriches posts with NER and sentiment, sinks to Elasticsearch
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict

from pyflink.datastream import StreamExecutionEnvironment, TimeCharacteristic
from pyflink.datastream.functions import CoProcessFunction, RuntimeContext
from pyflink.datastream.state import MapStateDescriptor, StateTtlConfig
from pyflink.common.typeinfo import Types
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.time import Time
from pyflink.datastream.connectors.kafka import (
    KafkaSource,
    KafkaOffsetsInitializer
)
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.datastream.connectors.elasticsearch import (
    Elasticsearch7SinkBuilder,
    ElasticsearchEmitter
)
from pyflink.common import Row

# Add parent directory to path
sys.path.append('..')
from config.config import (
    KAFKA_BOOTSTRAP_SERVERS_INTERNAL,
    TOPIC_RAW_SOCIAL,
    TOPIC_DETECTED_EVENTS,
    ELASTICSEARCH_HOST_INTERNAL,
    ES_INDEX_ENRICHED,
    FLINK_CHECKPOINT_INTERVAL,
    FLINK_PARALLELISM,
    FLINK_STATE_TTL_HOURS
)
from processing.utils import (
    load_spacy_model,
    extract_entities_spacy,
    analyze_sentiment,
    contains_keywords,
    extract_matching_keywords,
    safe_json_loads,
    safe_json_dumps
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NarrativeEnricher(CoProcessFunction):
    """
    Stream-stream join: correlates detected events with social media posts
    Enriches matched posts with NER and sentiment analysis
    """
    
    def __init__(self):
        """Initialize the function"""
        self.events_state = None
        self.spacy_model = None
        self.match_count = 0
    
    def open(self, runtime_context: RuntimeContext):
        """Initialize state and models"""
        logger.info("🚀 Opening NarrativeEnricher...")
        
        # State TTL configuration (24 hours)
        ttl_config = StateTtlConfig.new_builder(Time.hours(FLINK_STATE_TTL_HOURS)) \
            .set_update_type(StateTtlConfig.UpdateType.OnCreateAndWrite) \
            .set_state_visibility(StateTtlConfig.StateVisibility.NeverReturnExpired) \
            .build()
        
        # State to store active events
        # Key: event_id, Value: {"keywords": [...], "timestamp": "..."}
        events_descriptor = MapStateDescriptor(
            "active_events",
            Types.STRING(),
            Types.STRING()
        )
        events_descriptor.enable_time_to_live(ttl_config)
        
        self.events_state = runtime_context.get_map_state(events_descriptor)
        
        # Load spaCy model for NER
        logger.info("📚 Loading spaCy model...")
        self.spacy_model = load_spacy_model()
        
        logger.info("✅ NarrativeEnricher ready")
    
    def process_element1(self, value, ctx: 'CoProcessFunction.Context'):
        """
        Process detected events (first stream)
        Store events in state for matching with social posts
        
        Args:
            value: JSON string of detected event
            ctx: Processing context
        """
        try:
            event = safe_json_loads(value)
            if event is None:
                return
            
            event_id = event.get('event_id')
            keywords = event.get('keywords', [])
            
            if not event_id or not keywords:
                return
            
            logger.info(f"📌 Storing event: {event_id} with keywords: {keywords}")
            
            # Store event in state
            event_data = {
                "keywords": keywords,
                "timestamp": datetime.now().isoformat(),
                "title": event.get('title', '')
            }
            
            self.events_state.put(event_id, safe_json_dumps(event_data))
            
        except Exception as e:
            logger.error(f"❌ Error processing event: {e}")
    
    def process_element2(self, value, ctx: 'CoProcessFunction.Context'):
        """
        Process social media posts (second stream)
        Match against stored events and enrich
        
        Args:
            value: JSON string of social post
            ctx: Processing context
        """
        try:
            post = safe_json_loads(value)
            if post is None:
                return
            
            text = post.get('text', '')
            if not text:
                return
            
            # Check all active events for keyword matches
            matched_events = []
            
            for event_id in self.events_state.keys():
                event_json = self.events_state.get(event_id)
                event_data = safe_json_loads(event_json)
                
                if event_data is None:
                    continue
                
                keywords = event_data.get('keywords', [])
                
                # Check if post contains event keywords
                if contains_keywords(text, keywords):
                    matched_keywords = extract_matching_keywords(text, keywords)
                    matched_events.append({
                        "event_id": event_id,
                        "matched_keywords": matched_keywords,
                        "event_title": event_data.get('title', '')
                    })
            
            # If post matches any events, enrich it
            if matched_events:
                self.match_count += 1
                
                logger.info(f"🎯 MATCH #{self.match_count}: Post matched {len(matched_events)} event(s)")
                logger.info(f"  Text: {text[:80]}...")
                
                # Extract entities using spaCy
                entities = extract_entities_spacy(text, self.spacy_model)
                
                # Analyze sentiment
                sentiment = analyze_sentiment(text)
                
                # Create enriched document for each matched event
                for match in matched_events:
                    enriched_doc = {
                        "event_id": match['event_id'],
                        "event_title": match['event_title'],
                        "matched_keywords": match['matched_keywords'],
                        "social_text": text,
                        "platform": post.get('platform', 'Unknown'),
                        "user": post.get('user', 'Unknown'),
                        "location": post.get('location', 'Unknown'),
                        "timestamp": post.get('timestamp', datetime.now().isoformat()),
                        "sentiment": sentiment,
                        "entities": entities,
                        "likes": post.get('likes', 0),
                        "retweets": post.get('retweets', 0),
                        "enriched_at": datetime.now().isoformat()
                    }
                    
                    logger.info(f"  Event: {match['event_id']}")
                    logger.info(f"  Keywords: {match['matched_keywords']}")
                    logger.info(f"  Sentiment: {sentiment:.3f}")
                    logger.info(f"  Entities: {entities}")
                    
                    # Emit enriched document
                    yield safe_json_dumps(enriched_doc)
            
        except Exception as e:
            logger.error(f"❌ Error processing social post: {e}")


class ESDocumentEmitter(ElasticsearchEmitter):
    """Custom emitter for Elasticsearch documents"""
    
    def emit(self, element, context):
        """
        Emit element to Elasticsearch
        
        Args:
            element: JSON string of enriched document
            context: Emission context
        """
        try:
            doc = safe_json_loads(element)
            if doc is None:
                return
            
            # Generate document ID from event_id and timestamp
            doc_id = f"{doc.get('event_id', 'unknown')}_{doc.get('timestamp', '').replace(':', '')}_{doc.get('user', 'unknown')}"
            
            # Return document for indexing
            return {
                '_index': ES_INDEX_ENRICHED,
                '_id': doc_id,
                '_source': doc
            }
        except Exception as e:
            logger.error(f"Error emitting to ES: {e}")
            return None


def create_narrative_tracker_job():
    """
    Create and configure the Flink job for narrative tracking
    """
    logger.info("=" * 80)
    logger.info("🚀 CREATING NARRATIVE TRACKER JOB")
    logger.info("=" * 80)
    
    # Create execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(FLINK_PARALLELISM)
    
    # Enable checkpointing
    env.enable_checkpointing(FLINK_CHECKPOINT_INTERVAL)
    
    logger.info(f"✅ Environment configured (parallelism: {FLINK_PARALLELISM})")
    
    # Create Kafka source for detected_events
    events_source = KafkaSource.builder() \
        .set_bootstrap_servers(','.join(KAFKA_BOOTSTRAP_SERVERS_INTERNAL)) \
        .set_topics(TOPIC_DETECTED_EVENTS) \
        .set_group_id('narrative_tracker_events_group') \
        .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()
    
    # Create Kafka source for raw_social
    social_source = KafkaSource.builder() \
        .set_bootstrap_servers(','.join(KAFKA_BOOTSTRAP_SERVERS_INTERNAL)) \
        .set_topics(TOPIC_RAW_SOCIAL) \
        .set_group_id('narrative_tracker_social_group') \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()
    
    logger.info(f"✅ Kafka sources created: {TOPIC_DETECTED_EVENTS}, {TOPIC_RAW_SOCIAL}")
    
    # Create data streams
    events_stream = env.from_source(
        events_source,
        WatermarkStrategy.no_watermarks(),
        "Events Source"
    )
    
    social_stream = env.from_source(
        social_source,
        WatermarkStrategy.no_watermarks(),
        "Social Source"
    )
    
    # Key streams (use constant key for global matching)
    keyed_events = events_stream.key_by(lambda x: "global")
    keyed_social = social_stream.key_by(lambda x: "global")
    
    # Connect streams and apply enricher
    enriched_stream = keyed_events.connect(keyed_social).process(NarrativeEnricher())
    
    logger.info("✅ Narrative enricher applied")
    
    # Create Elasticsearch sink
    es_sink = Elasticsearch7SinkBuilder() \
        .set_hosts([ELASTICSEARCH_HOST_INTERNAL]) \
        .set_emitter(ESDocumentEmitter()) \
        .set_bulk_flush_max_actions(100) \
        .set_bulk_flush_interval(5000) \
        .build()
    
    logger.info(f"✅ Elasticsearch sink created: {ELASTICSEARCH_HOST_INTERNAL}")
    logger.info(f"   Index: {ES_INDEX_ENRICHED}")
    
    # Sink enriched documents to Elasticsearch
    enriched_stream.sink_to(es_sink)
    
    logger.info("=" * 80)
    logger.info("✅ Job configured successfully")
    logger.info(f"📥 Input 1: {TOPIC_DETECTED_EVENTS} (events)")
    logger.info(f"📥 Input 2: {TOPIC_RAW_SOCIAL} (social posts)")
    logger.info(f"📤 Output: Elasticsearch ({ES_INDEX_ENRICHED})")
    logger.info("=" * 80)
    
    return env


def main():
    """Entry point"""
    try:
        # Create job
        env = create_narrative_tracker_job()
        
        # Execute job
        logger.info("\n🚀 Starting Narrative Tracker Job...")
        env.execute("Narrative Entity Tracker")
        
    except Exception as e:
        logger.error(f"❌ Job failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
