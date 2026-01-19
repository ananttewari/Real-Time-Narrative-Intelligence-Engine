"""
Enhanced Entity Extraction & Validation Module
Designed to eliminate placeholder/gibberish entities from network analysis
"""

import re
from collections import Counter, defaultdict
import networkx as nx

# === KNOWN INDIAN ENTITIES (WHITELIST) ===
# Organizations
VALID_ORGANIZATIONS = {
    'NITI Aayog', 'RBI', 'ISRO', 'DRDO', 'SEBI', 'Reserve Bank of India',
    'Reliance Industries', 'Tata Group', 'Tata', 'Infosys', 'Wipro', 
    'HDFC Bank', 'HDFC', 'Indian Oil', 'Coal India', 'SBI',
    'State Bank of India', 'Google', 'Microsoft', 'Amazon',
    'Indian Space Research Organisation', 'Defence Research and Development Organisation'
}

# Geopolitical Entities
VALID_LOCATIONS = {
    'Mumbai', 'Delhi', 'Bengaluru', 'Bangalore', 'Hyderabad', 'Chennai', 
    'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Surat', 'Lucknow',
    'India', 'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Gujarat',
    'Rajasthan', 'West Bengal', 'Uttar Pradesh', 'New Delhi'
}

# Common placeholder/gibberish patterns to reject
GIBBERISH_PATTERNS = [
    r'lorem', r'ipsum', r'dolor', r'sit', r'amet', r'consectetur',
    r'adipiscing', r'elit', r'natus', r'temporibus', r'eiusmod',
    r'incididunt', r'labore', r'magna', r'aliqua', r'enim',
    r'minim', r'veniam', r'quis', r'nostrud', r'exercitation'
]

# Expanded stopwords
EXPANDED_STOPWORDS = {
    'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'natus', 'temporibus',
    'consectetur', 'adipiscing', 'elit', 'sed', 'eiusmod', 'the', 'a', 'an',
    'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'
}


def extract_validate_entities(content, nlp):
    """
    Extract and validate entities with aggressive filtering
    
    Args:
        content: Article text
        nlp: spaCy model
        
    Returns:
        List of validated (entity_text, entity_label) tuples
    """
    doc = nlp(content)
    validated = []
    
    for ent in doc.ents:
        # Filter 1: Entity type must be ORG, GPE, or PERSON
        if ent.label_ not in {'ORG', 'GPE', 'PERSON'}:
            continue
            
        ent_text = ent.text.strip()
        
        # Filter 2: Minimum length
        if len(ent_text) < 3:
            continue
            
        # Filter 3: Must be proper noun (all tokens PROPN)
        if not all(token.pos_ == 'PROPN' for token in ent):
            continue
            
        # Filter 4: Check against stopwords
        if ent_text.lower() in EXPANDED_STOPWORDS:
            continue
            
        # Filter 5: Check for gibberish patterns
        is_gibberish = any(
            re.search(pattern, ent_text.lower()) 
            for pattern in GIBBERISH_PATTERNS
        )
        if is_gibberish:
            continue
            
        # Filter 6: Must contain only letters and spaces
        if not re.match(r'^[A-Za-z\s]+$', ent_text):
            continue
            
        # Filter 7: Whitelist validation (prioritize known entities)
        is_whitelisted = (
            ent_text in VALID_ORGANIZATIONS or 
            ent_text in VALID_LOCATIONS or
            any(known in ent_text for known in VALID_ORGANIZATIONS) or
            any(known in ent_text for known in VALID_LOCATIONS)
        )
        
        # Accept if whitelisted OR if it passes basic quality checks
        if is_whitelisted:
            validated.append((ent_text, ent.label_))
        elif ent.label_ in {'ORG', 'GPE'}:  # Only accept non-whitelisted ORG/GPE with caution
            # Additional check: must have at least 2 capital letters
            if sum(1 for c in ent_text if c.isupper()) >= 2:
                validated.append((ent_text, ent.label_))
    
    return validated


def generate_clean_anchor_graph(df, nlp):
    """
    Generate a clean narrative anchor graph with validated entities
    
    Args:
        df: DataFrame with articles
        nlp: spaCy model
        
    Returns:
        NetworkX graph, entity frequencies, anchor scores
    """
    print("   Extracting and validating entities...")
    
    # Re-extract all entities with validation
    validated_entities = []
    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"      Processed {idx}/{len(df)} articles...")
        entities = extract_validate_entities(row['content'], nlp)
        validated_entities.append(entities)
    
    # Count entity frequencies
    all_entities = [text for sublist in validated_entities for text, _ in sublist]
    entity_freq = Counter(all_entities)
    
    # Filter to entities with minimum frequency
    MIN_FREQUENCY = 5
    high_freq_entities = {ent for ent, count in entity_freq.items() if count >= MIN_FREQUENCY}
    
    print(f"   Retained {len(high_freq_entities)} high-frequency entities")
    
    # Build co-occurrence tracking
    cooccurrence_articles = defaultdict(set)
    
    for idx, entities_list in enumerate(validated_entities):
        entities = [text for text, _ in entities_list if text in high_freq_entities]
        
        if len(entities) < 2:
            continue
            
        # Create edges
        for i in range(len(entities)):
            for j in range(i+1, len(entities)):
                u, v = sorted([entities[i], entities[j]])
                cooccurrence_articles[(u, v)].add(idx)
    
    # Apply co-occurrence threshold: N >= 3
    CO_OCCURRENCE_THRESHOLD = 3
    
    G = nx.Graph()
    for (u, v), article_set in cooccurrence_articles.items():
        if len(article_set) >= CO_OCCURRENCE_THRESHOLD:
            G.add_edge(u, v, weight=len(article_set))
    
    print(f"   Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Prune leaf nodes with low frequency
    nodes_to_remove = [
        node for node in G.nodes() 
        if G.degree(node) == 1 and entity_freq[node] < 10
    ]
    G.remove_nodes_from(nodes_to_remove)
    
    print(f"   Pruned {len(nodes_to_remove)} leaf nodes")
    
    if G.number_of_nodes() == 0:
        print("   ⚠️ No entities met the criteria")
        return None, None, None
    
    # Calculate centrality metrics
    degree_centrality = nx.degree_centrality(G)
    
    # Weighted degree centrality (frequency × connections)
    anchor_scores = {}
    for node in G.nodes():
        freq_norm = entity_freq[node] / max(entity_freq.values())
        degree_norm = degree_centrality[node]
        anchor_scores[node] = freq_norm * degree_norm
    
    # Get entity types
    entity_types = {}
    for entities_list in validated_entities:
        for text, label in entities_list:
            if text in G.nodes():
                entity_types[text] = label
    
    return G, entity_freq, anchor_scores, entity_types
