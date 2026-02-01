"""

Kafka Consumer for Elasticsearch Indexing (Windows Compatible)

Consumes news from Kafka and indexes into Elasticsearch with enrichment

Uses confluent-kafka which is Windows-compatible

"""



import json

import time

from datetime import datetime

from confluent_kafka import Consumer, KafkaError

from elasticsearch import Elasticsearch, helpers

import spacy



# Configuration

KAFKA_BROKER = 'localhost:9092'

KAFKA_TOPIC = 'raw_news'

ES_URL = 'http://localhost:9200'

ES_INDEX = 'news_articles'



print("🔧 Initializing Elasticsearch consumer...")



# Initialize Elasticsearch

es = Elasticsearch([ES_URL])



# Test connection

if es.ping():

    print("✅ Connected to Elasticsearch")

    # Create index if it doesn't exist

    if not es.indices.exists(index=ES_INDEX):

        es.indices.create(index=ES_INDEX)

        print(f"✅ Created index: {ES_INDEX}")

else:

    print("❌ Failed to connect to Elasticsearch")

    exit(1)



# Initialize spaCy for entity extraction

print("🔧 Loading spaCy model...")

try:

    nlp = spacy.load('en_core_web_sm')

    print("✅ spaCy model loaded")

except:

    print("⚠️ spaCy model not found. Install with: python -m spacy download en_core_web_sm")

    nlp = None



# Initialize Kafka Consumer (confluent-kafka)

print("🔧 Connecting to Kafka...")

consumer = Consumer({

    'bootstrap.servers': KAFKA_BROKER,

    'group.id': 'narrative-demo-consumer',

    'auto.offset.reset': 'earliest',

    'enable.auto.commit': True

})



consumer.subscribe([KAFKA_TOPIC])

print(f"✅ Kafka consumer connected. Listening to topic: {KAFKA_TOPIC}")

print("🔄 Starting to consume messages...\n")



def extract_entities(text):

    """Extract entities using spaCy with filtering"""

    if not text or nlp is None:

        return [], []

    

    try:

        doc = nlp(text[:1000])  # Limit to first 1000 chars

        

        # Filter out generic/invalid entities

        generic_entities = {'earth', 'world', 'covid', 'ai', 'a.i.', 'com', 'the', 'new', 'news'}

        

        # Extract entities with filtering

        entities = [

            ent.text for ent in doc.ents 

            if ent.label_ in ['PERSON', 'ORG', 'EVENT'] 

            and ent.text.lower() not in generic_entities

            and len(ent.text) > 1  # Remove single-letter entities

        ]

        

        locations = [

            ent.text for ent in doc.ents 

            if ent.label_ in ['GPE', 'LOC']

            and ent.text.lower() not in generic_entities

            and len(ent.text) > 1

        ]

        

        return entities, locations

    except:

        return [], []



def analyze_sentiment(text):

    """Enhanced sentiment analysis with comprehensive keyword lists"""

    if not text:

        return 'neutral', 0.0

    

    text_lower = text.lower()

    

    # Comprehensive positive keywords

    positive_words = [

        'good', 'great', 'excellent', 'positive', 'success', 'wonderful', 

        'fantastic', 'amazing', 'brilliant', 'outstanding', 'superb',  

        'triumph', 'victory', 'achievement', 'progress', 'improve', 'improvement',

        'breakthrough', 'gains', 'surge', 'boost', 'rise', 'growth', 'increase',

        'recover', 'recovery', 'celebrate', 'joy', 'happy', 'thrilled', 'excited',

        'record-breaking', 'historic', 'milestone', 'win', 'winner', 'succeed'

    ]

    

    # Comprehensive negative keywords  

    negative_words = [

        'bad', 'terrible', 'negative', 'fail', 'failed', 'failure', 'worst', 

        'crisis', 'disaster', 'awful', 'horrible', 'tragic', 'tragedy', 

        'catastrophe', 'death', 'deaths', 'die', 'died', 'kill', 'killed', 'killing',

        'war', 'attack', 'attacked', 'threat', 'threaten', 'danger', 'dangerous',

        'collapse', 'collapsed', 'crash', 'crashed', 'decline', 'declining',

        'fall', 'falling', 'fell', 'drop', 'dropped', 'plunge', 'plunged',

        'scandal', 'corruption', 'fraud', 'scam', 'misleading', 'mislead',

        'exhaustion', 'bleak', 'bleakest', 'grim', 'dire', 'uncertain', 'uncertainty',

        'concern', 'concerned', 'worry', 'worried', 'fear', 'feared', 'afraid',

        'shock', 'shocking', 'shocked', 'disturbing', 'disturbed', 'alarming',

        'devastate', 'devastated', 'destroy', 'destroyed', 'damage', 'damaged',

        'loss', 'losses', 'lost', 'suffer', 'suffering', 'pain', 'painful',

        'violence', 'violent', 'crime', 'criminal', 'arrest', 'arrested',

        'injure', 'injured', 'injury', 'harm', 'harmful', 'hurt',

        'protest', 'riot', 'chaos', 'turmoil', 'instability', 'unstable'

    ]

    

    # Negation words that flip sentiment

    negations = ['not', 'no', 'never', 'neither', "n't", 'cannot', 'without', "won't", "don't", "doesn't"]

    

    # Split into words for proper boundary checking

    words = text_lower.split()

    

    pos_count = 0

    neg_count = 0

    

    for i, word in enumerate(words):



        # Remove punctuation for matching



        clean_word = word.strip('.,!?;:')

        

        # Check if previous word is a negation

        is_negated = (i > 0 and words[i-1].strip('.,!?;:') in negations)







        

        # Count positive words (flip if negated)

        if clean_word in positive_words:

            if is_negated:

                neg_count += 1  # "not good" = negative

            else:

                pos_count += 1

        

        # Count negative words (flip if negated)

        elif clean_word in negative_words:

            if is_negated:

                pos_count += 0.5  # "not bad" = slightly positive  

            else:

                neg_count += 1

    

    # Simpler, more accurate decision logic
    # Require at least 2 sentiment words to classify as positive/negative
    if pos_count > neg_count and pos_count >= 2:
        # Proportional positive score
        sentiment_score = min(0.8, (pos_count - neg_count) * 0.15)
        return 'positive', sentiment_score
    elif neg_count > pos_count and neg_count >= 2:
        # Proportional negative score  
        sentiment_score = max(-0.8, -(neg_count - pos_count) * 0.15)
        return 'negative', sentiment_score
    else:
        return 'neutral', 0.0



def contains_inappropriate_content(text):

    """Filter out adult/inappropriate content"""

    if not text:

        return False

    

    text_lower = text.lower()

    

    # Adult content keywords to block

    blocked_keywords = [

        'porn', 'pornhub', 'xxx', 'hentai', 'camgirl'

    ]

    

    # Check if any blocked keyword appears in the text

    for keyword in blocked_keywords:

        if keyword in text_lower:

            return True

    

    return False



# Process messages

message_count = 0

batch = []

batch_size = 10



try:

    while True:

        msg = consumer.poll(timeout=1.0)

        

        if msg is None:

            continue

        if msg.error():

            if msg.error().code() == KafkaError._PARTITION_EOF:

                continue

            else:

                print(f"❌ Kafka error: {msg.error()}")

                continue

        

        try:

            # Decode message

            article = json.loads(msg.value().decode('utf-8'))

            

            # Get content for analysis

            content = article.get('description', '') or article.get('content', '')

            title = article.get('title', '')

            

            # CONTENT FILTER: Block inappropriate content

            if contains_inappropriate_content(title) or contains_inappropriate_content(content):

                print(f"⛔ Blocked inappropriate content: {title[:50]}...")

                continue

            

            # Enrich article with entities and sentiment

            entities, locations = extract_entities(content)

            sentiment, sentiment_score = analyze_sentiment(content)

            

            # Prepare document for Elasticsearch

            doc = {

                'id': article.get('id', f"{article.get('title', '')[:20]}_{int(time.time())}"),

                'title': article.get('title', ''),

                'description': article.get('description', ''),

                'content': content,

                'source': article.get('source', {}).get('name', 'Unknown') if isinstance(article.get('source'), dict) else article.get('source', 'Unknown'),

                'author': article.get('author', 'Unknown'),

                'url': article.get('url', ''),

                'published_at': article.get('publishedAt', article.get('published_at', datetime.now().isoformat())),

                'ingested_at': datetime.now().isoformat(),

                'timestamp': article.get('publishedAt', article.get('published_at', datetime.now().isoformat())),

                'event_time': datetime.now().isoformat(),

                'entities': entities,

                'entity_count': len(entities),

                'locations': locations,

                'sentiment': sentiment,

                'sentiment_score': sentiment_score,

                'theme': 'live_news'

            }

            

            batch.append({

                '_index': ES_INDEX,

                '_id': doc['id'],

                '_source': doc

            })

            

            message_count += 1

            

            # Bulk index when batch is full

            if len(batch) >= batch_size:

                success, failed = helpers.bulk(es, batch, raise_on_error=False)

                print(f"✅ Indexed batch: {success} docs | Total: {message_count} | Failed: {len(failed)}")

                batch = []

            

            # Show progress

            if message_count % 5 == 0:

                print(f"📊 Processed {message_count} articles from Kafka")

                

        except Exception as e:

            print(f"❌ Error processing message: {e}")

            continue

            

except KeyboardInterrupt:

    print("\n⏹️ Stopping consumer...")

    

    # Index remaining documents

    if batch:

        success, failed = helpers.bulk(es, batch, raise_on_error=False)

        print(f"✅ Final batch indexed: {success} docs | Failed: {len(failed)}")

    

    print(f"\n📊 Total messages processed: {message_count}")

    consumer.close()

    print("✅ Consumer closed")

