"""
Utility functions for NLP processing, vector operations, and shared logic
Provides reusable components for Flink jobs
"""

import json
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# NLP Model Loading
# ============================================

def load_embedding_model():
    """
    Load SentenceTransformer model for text vectorization
    Lazy loading to avoid import delays
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        logger.info("✅ Loaded embedding model: all-MiniLM-L6-v2")
        return model
    except Exception as e:
        logger.error(f"❌ Failed to load embedding model: {e}")
        return None


def load_spacy_model():
    """
    Load spaCy model for Named Entity Recognition
    Lazy loading to avoid import delays
    """
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        logger.info("✅ Loaded spaCy model: en_core_web_sm")
        return nlp
    except Exception as e:
        logger.warning(f"⚠️ Failed to load spaCy model: {e}")
        logger.warning("Run: python -m spacy download en_core_web_sm")
        return None


# ============================================
# Vector Operations
# ============================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0 to 1)
    """
    try:
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        
        similarity = dot_product / (norm_v1 * norm_v2)
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0


def find_most_similar_centroid(
    vector: List[float],
    centroids: Dict[str, List[float]]
) -> Tuple[Optional[str], float]:
    """
    Find the most similar centroid to a given vector
    
    Args:
        vector: Input vector
        centroids: Dictionary of event_id -> centroid vector
        
    Returns:
        Tuple of (best_event_id, max_similarity)
    """
    if not centroids:
        return None, 0.0
    
    max_similarity = 0.0
    best_event_id = None
    
    for event_id, centroid in centroids.items():
        similarity = cosine_similarity(vector, centroid)
        
        if similarity > max_similarity:
            max_similarity = similarity
            best_event_id = event_id
    
    return best_event_id, max_similarity


# ============================================
# Text Processing
# ============================================

def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    Extract keywords from text using simple frequency-based approach
    
    Args:
        text: Input text
        top_n: Number of keywords to extract
        
    Returns:
        List of keywords
    """
    try:
        # Simple tokenization and filtering
        words = text.lower().split()
        words = [w.strip('.,!?;:()[]{}"\'-') for w in words]
        words = [w for w in words if len(w) > 3 and w.isalnum()]
        
        # Remove common stop words (simplified)
        stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'will', 'their', 'there', 'about'}
        words = [w for w in words if w not in stop_words]
        
        # Return unique keywords
        unique_words = []
        seen = set()
        for w in words:
            if w not in seen:
                unique_words.append(w)
                seen.add(w)
        
        return unique_words[:top_n]
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return []


def extract_entities_spacy(text: str, nlp_model) -> Dict[str, List[str]]:
    """
    Extract named entities using spaCy
    
    Args:
        text: Input text
        nlp_model: Loaded spaCy model
        
    Returns:
        Dictionary with entity types and values
    """
    if nlp_model is None:
        return {"persons": [], "organizations": [], "locations": []}
    
    try:
        # Limit text length for performance
        doc = nlp_model(text[:1000])
        
        entities = {
            "persons": [],
            "organizations": [],
            "locations": []
        }
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities["persons"].append(ent.text)
            elif ent.label_ in ["ORG", "PRODUCT"]:
                entities["organizations"].append(ent.text)
            elif ent.label_ in ["GPE", "LOC"]:
                entities["locations"].append(ent.text)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))[:5]  # Limit to 5
        
        return entities
        
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        return {"persons": [], "organizations": [], "locations": []}


# ============================================
# Sentiment Analysis
# ============================================

def analyze_sentiment(text: str) -> float:
    """
    Analyze sentiment using VADER
    
    Args:
        text: Input text
        
    Returns:
        Compound sentiment score (-1 to 1)
    """
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        return scores['compound']
    except Exception as e:
        logger.warning(f"VADER not available, using simple sentiment: {e}")
        return simple_sentiment(text)


def simple_sentiment(text: str) -> float:
    """
    Simple keyword-based sentiment analysis (fallback)
    
    Args:
        text: Input text
        
    Returns:
        Sentiment score (-1 to 1)
    """
    text_lower = text.lower()
    
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 
                     'fantastic', 'best', 'love', 'happy', 'excited']
    negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'sad', 
                     'angry', 'disaster', 'crisis', 'tragedy']
    
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    
    return (pos_count - neg_count) / total


# ============================================
# JSON Serialization Helpers
# ============================================

def safe_json_loads(json_str: str) -> Optional[Dict]:
    """
    Safely parse JSON string
    
    Args:
        json_str: JSON string
        
    Returns:
        Parsed dictionary or None if invalid
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return None


def safe_json_dumps(obj: Dict) -> str:
    """
    Safely serialize object to JSON
    
    Args:
        obj: Python object
        
    Returns:
        JSON string
    """
    try:
        return json.dumps(obj, default=str)
    except Exception as e:
        logger.error(f"JSON encode error: {e}")
        return "{}"


# ============================================
# Event ID Generation
# ============================================

def generate_event_id() -> str:
    """
    Generate unique event ID
    
    Returns:
        Event ID string
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    import random
    random_suffix = random.randint(1000, 9999)
    return f"evt_{timestamp}_{random_suffix}"


# ============================================
# Text Matching
# ============================================

def contains_keywords(text: str, keywords: List[str]) -> bool:
    """
    Check if text contains any of the keywords (case-insensitive)
    
    Args:
        text: Input text
        keywords: List of keywords to search for
        
    Returns:
        True if any keyword found
    """
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def extract_matching_keywords(text: str, keywords: List[str]) -> List[str]:
    """
    Extract keywords from text that match given list
    
    Args:
        text: Input text
        keywords: List of keywords to search for
        
    Returns:
        List of matched keywords
    """
    text_lower = text.lower()
    matched = []
    
    for keyword in keywords:
        if keyword.lower() in text_lower:
            matched.append(keyword)
    
    return matched


# ============================================
# Mock NLP (for testing without models)
# ============================================

class MockEmbeddingModel:
    """Mock embedding model for testing"""
    
    def encode(self, texts):
        """Return random vectors"""
        if isinstance(texts, str):
            return np.random.rand(384).tolist()
        return [np.random.rand(384).tolist() for _ in texts]


class MockSpacyModel:
    """Mock spaCy model for testing"""
    
    def __call__(self, text):
        """Return mock doc with no entities"""
        class MockDoc:
            ents = []
        return MockDoc()


# ============================================
# Initialization Helper
# ============================================

def initialize_nlp_models(use_mock: bool = False):
    """
    Initialize all NLP models
    
    Args:
        use_mock: If True, use mock models for testing
        
    Returns:
        Tuple of (embedding_model, spacy_model)
    """
    if use_mock:
        logger.warning("⚠️ Using MOCK NLP models for testing")
        return MockEmbeddingModel(), MockSpacyModel()
    
    embedding_model = load_embedding_model()
    spacy_model = load_spacy_model()
    
    return embedding_model, spacy_model
