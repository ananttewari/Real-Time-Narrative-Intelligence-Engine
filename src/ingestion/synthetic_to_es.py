import json
import random
import uuid
from datetime import datetime, timedelta
import requests

ES_URL = "http://localhost:9200"
INDEX = "news_articles"
TOTAL_DOCS = 1000  # Increased for more data points

# Clickbait cluster for Hype vs. Substance analysis
CLICKBAIT_CLUSTER = {
    "id": 12,
    "topic": "CLICKBAIT - Sensationalized News",
    "sentiment": "neutral",
    "is_clickbait": True,
    "keywords": ["shocking", "breaking", "exclusive", "viral"],
    "titles": [
        "SHOCKING! Indian Startup Unicorn COLLAPSES Overnight - What They're Hiding From You!",
        "You Won't BELIEVE What This Billionaire Just Said About India's Future!",
        "BREAKING: Secret Government Meeting Reveals SHOCKING Plans for 2026!",
        "This One Simple Trick Could DESTROY India's Economy (Economists HATE It!)",
        "EXCLUSIVE: Celebrity CEO's SHOCKING Confession About Tech Industry!",
        "ALERT: Your Money is in DANGER! What Banks Don't Want You to Know!",
        "VIRAL: This Company's Stock Could Make You RICH Beyond Belief!",
        "BREAKING NEWS: Massive Changes Coming to Your Daily Life - Are You Ready?",
        "SHOCKING Discovery: The TRUTH About Popular App Finally EXPOSED!",
        "URGENT: This Economic Indicator Signals MAJOR Market Crash Coming Soon!",
    ],
    "phrases": [
        "industry insiders are keeping quiet",
        "experts are baffled by this development",
        "could change everything we know",
        "nobody is talking about this massive shift",
        "the establishment doesn't want you to see this",
    ],
    "entities": ["Anonymous Source", "Industry Insider", "Expert Analyst"],
    "entity_groups": [
        ["Anonymous Source"],
        ["Industry Insider"],
        ["Expert Analyst"],
    ],
}

# Pre-baked cluster templates with entity relationship groups
CLUSTERS = [
    {
        "id": 0,
        "topic": "India's Digital Transformation",
        "sentiment": "positive",
        "keywords": ["digital", "india", "technology", "reliance", "payments"],
        "titles": [
            "Reliance Jio and Google announce massive 5G infrastructure rollout",
            "Infosys partners with TCS on national digital identity platform",
            "NITI Aayog approves Wipro-Microsoft smart city initiative",
            "Paytm and PhonePe collaborate on UPI expansion with NPCI backing",
            "Reliance and Airtel bid jointly for spectrum with government support",
        ],
        "phrases": [
            "government partnership accelerates digital India mission",
            "strategic alliance to serve 500 million users",
            "NITI Aayog grants approval for nationwide deployment",
            "RBI endorses unified payment framework",
        ],
        "entities": ["Reliance Jio", "Infosys", "TCS", "Wipro", "Google", "Microsoft", "NITI Aayog", "Paytm", "PhonePe", "NPCI", "Airtel", "RBI"],
        "entity_groups": [
            ["Reliance Jio", "Google", "NITI Aayog"],
            ["Infosys", "TCS", "Microsoft"],
            ["Wipro", "Microsoft", "NITI Aayog"],
            ["Paytm", "PhonePe", "NPCI", "RBI"],
            ["Reliance Jio", "Airtel", "NITI Aayog"],
            ["TCS", "Wipro", "Infosys"],
        ],
    },
    {
        "id": 1,
        "topic": "Indian Pharma Leadership",
        "sentiment": "positive",
        "keywords": ["pharma", "vaccine", "export", "manufacturing"],
        "titles": [
            "Serum Institute partners with Pfizer on vaccine manufacturing",
            "Sun Pharma and Dr Reddy's jointly develop new therapy with WHO endorsement",
            "Cipla announces collaboration with Moderna for mRNA production",
            "DCGI fast-tracks approval for Biocon-Pfizer joint venture",
            "WHO designates India as global vaccine hub, credits Serum Institute",
        ],
        "phrases": [
            "WHO recognition strengthens India's pharma position",
            "DCGI expedites regulatory pathway",
            "joint development targets emerging markets",
            "government backing ensures export dominance",
        ],
        "entities": ["Serum Institute", "Sun Pharma", "Dr Reddy's", "Cipla", "Biocon", "Pfizer", "Moderna", "WHO", "DCGI", "ICMR"],
        "entity_groups": [
            ["Serum Institute", "Pfizer", "WHO"],
            ["Sun Pharma", "Dr Reddy's", "WHO", "DCGI"],
            ["Cipla", "Moderna", "ICMR"],
            ["Biocon", "Pfizer", "DCGI"],
            ["Serum Institute", "WHO", "ICMR"],
            ["Dr Reddy's", "Cipla", "Sun Pharma"],
        ],
    },
    {
        "id": 2,
        "topic": "India's Space Ambitions",
        "sentiment": "positive",
        "keywords": ["space", "isro", "satellite", "launch", "mission"],
        "titles": [
            "ISRO and NASA sign historic partnership for lunar exploration",
            "SpaceX to launch Indian satellites under ISRO agreement",
            "L&T and HAL win ISRO contract for Gaganyaan mission",
            "ISRO collaborates with ESA on Mars sample return mission",
            "Bharti Airtel partners with ISRO for satellite broadband",
        ],
        "phrases": [
            "bilateral space cooperation reaches new heights",
            "private sector participation strengthens mission",
            "international consortium formed for deep space exploration",
            "commercial satellite deployment accelerates",
        ],
        "entities": ["ISRO", "NASA", "SpaceX", "ESA", "L&T", "HAL", "Bharti Airtel", "DRDO", "Antrix"],
        "entity_groups": [
            ["ISRO", "NASA", "SpaceX"],
            ["ISRO", "L&T", "HAL"],
            ["ISRO", "ESA", "NASA"],
            ["ISRO", "Bharti Airtel", "Antrix"],
            ["L&T", "HAL", "DRDO"],
            ["SpaceX", "NASA", "ISRO"],
        ],
    },
    {
        "id": 3,
        "topic": "Indian Banking & Finance Surge",
        "sentiment": "positive",
        "keywords": ["banking", "rbi", "fintech", "digital", "lending"],
        "titles": [
            "RBI approves HDFC-ICICI merger creating banking giant",
            "SBI partners with NPCI on blockchain-based lending platform",
            "Axis Bank and Kotak Mahindra launch joint digital wallet with RBI nod",
            "SEBI greenlights NSE-BSE collaboration on unified trading",
            "RBI and NITI Aayog coordinate on fintech regulatory sandbox",
        ],
        "phrases": [
            "RBI approval creates India's largest private bank",
            "SEBI framework enables market integration",
            "regulatory innovation drives financial inclusion",
            "government-backed initiative reaches rural markets",
        ],
        "entities": ["RBI", "HDFC Bank", "ICICI Bank", "SBI", "NPCI", "Axis Bank", "Kotak Mahindra", "SEBI", "NSE", "BSE", "NITI Aayog"],
        "entity_groups": [
            ["RBI", "HDFC Bank", "ICICI Bank"],
            ["SBI", "NPCI", "RBI"],
            ["Axis Bank", "Kotak Mahindra", "RBI"],
            ["SEBI", "NSE", "BSE"],
            ["RBI", "NITI Aayog", "SEBI"],
            ["HDFC Bank", "SBI", "ICICI Bank"],
        ],
    },
    {
        "id": 4,
        "topic": "Renewable Energy India",
        "sentiment": "positive",
        "keywords": ["renewable", "solar", "adani", "tata", "energy"],
        "titles": [
            "Adani Green and Tata Power announce massive solar partnership",
            "NTPC collaborates with Reliance on hydrogen energy project",
            "Suzlon and Vestas win joint wind energy tender from government",
            "Adani Green partners with MNRE on 10GW solar initiative",
            "Tata Power and NTPC coordinate grid integration with POSOCO",
        ],
        "phrases": [
            "largest renewable energy alliance in Asia",
            "government target of 500GW by 2030 supported",
            "MNRE approval accelerates clean energy transition",
            "joint venture to power 50 million homes",
        ],
        "entities": ["Adani Green", "Tata Power", "NTPC", "Reliance", "Suzlon", "Vestas", "MNRE", "POSOCO", "SECI"],
        "entity_groups": [
            ["Adani Green", "Tata Power", "MNRE"],
            ["NTPC", "Reliance", "MNRE"],
            ["Suzlon", "Vestas", "SECI"],
            ["Adani Green", "MNRE", "SECI"],
            ["Tata Power", "NTPC", "POSOCO"],
            ["Adani Green", "NTPC", "Tata Power"],
        ],
    },
    {
        "id": 5,
        "topic": "Indian Infrastructure Boom",
        "sentiment": "positive",
        "keywords": ["infrastructure", "construction", "roads", "railways"],
        "titles": [
            "L&T and Larsen & Toubro partner with NHAI on highway expansion",
            "Indian Railways awards contract to L&T and Siemens consortium",
            "Adani Ports and DP World announce joint terminal development",
            "GMR and GVK win airport modernization tender from AAI",
            "NHAI coordinates with L&T on Delhi-Mumbai expressway completion",
        ],
        "phrases": [
            "government infrastructure push gains momentum",
            "PPP model delivers ahead of schedule",
            "NHAI approval unlocks major corridor development",
            "multi-agency coordination ensures timely delivery",
        ],
        "entities": ["L&T", "NHAI", "Indian Railways", "Siemens", "Adani Ports", "DP World", "GMR", "GVK", "AAI", "NITI Aayog"],
        "entity_groups": [
            ["L&T", "NHAI", "NITI Aayog"],
            ["Indian Railways", "L&T", "Siemens"],
            ["Adani Ports", "DP World", "NHAI"],
            ["GMR", "GVK", "AAI"],
            ["L&T", "Indian Railways", "NHAI"],
            ["GMR", "Adani Ports", "AAI"],
        ],
    },
    {
        "id": 6,
        "topic": "Indian Auto Revolution",
        "sentiment": "positive",
        "keywords": ["electric", "vehicle", "tata", "automotive"],
        "titles": [
            "Tata Motors and Mahindra jointly develop EV platform with government backing",
            "Maruti Suzuki partners with Toyota on hybrid technology for India",
            "Ola Electric collaborates with Bajaj Auto on battery swapping with NITI Aayog",
            "Hero MotoCorp and Honda announce strategic alliance for electric two-wheelers",
            "Tata Motors wins government tender with Ashok Leyland for electric buses",
        ],
        "phrases": [
            "government EV policy drives industry collaboration",
            "joint R&D to reduce battery costs by 40%",
            "NITI Aayog framework enables infrastructure sharing",
            "historic partnership transforms mobility sector",
        ],
        "entities": ["Tata Motors", "Mahindra", "Maruti Suzuki", "Toyota", "Ola Electric", "Bajaj Auto", "Hero MotoCorp", "Honda", "Ashok Leyland", "NITI Aayog", "MoRTH"],
        "entity_groups": [
            ["Tata Motors", "Mahindra", "NITI Aayog"],
            ["Maruti Suzuki", "Toyota", "MoRTH"],
            ["Ola Electric", "Bajaj Auto", "NITI Aayog"],
            ["Hero MotoCorp", "Honda", "MoRTH"],
            ["Tata Motors", "Ashok Leyland", "NITI Aayog"],
            ["Mahindra", "Bajaj Auto", "Tata Motors"],
        ],
    },
    {
        "id": 7,
        "topic": "Indian EdTech & Startups",
        "sentiment": "positive",
        "keywords": ["startup", "edtech", "investment", "unicorn"],
        "titles": [
            "Byju's and Unacademy merge operations with Sequoia backing",
            "Paytm partners with PhonePe on fintech infrastructure sharing",
            "Flipkart and Myntra integrate platforms under Walmart guidance",
            "Ola and Uber coordinate with government on EV fleet transition",
            "Zomato announces merger with Swiggy creating food delivery giant",
        ],
        "phrases": [
            "consolidation creates India's largest edtech platform",
            "strategic merger valued at $10 billion",
            "government startup policy enables collaboration",
            "investors Sequoia and Tiger Global coordinate backing",
        ],
        "entities": ["Byju's", "Unacademy", "Sequoia", "Tiger Global", "Paytm", "PhonePe", "Flipkart", "Myntra", "Walmart", "Ola", "Uber", "Zomato", "Swiggy"],
        "entity_groups": [
            ["Byju's", "Unacademy", "Sequoia"],
            ["Paytm", "PhonePe", "Tiger Global"],
            ["Flipkart", "Myntra", "Walmart"],
            ["Ola", "Uber", "NITI Aayog"],
            ["Zomato", "Swiggy", "Sequoia"],
            ["Sequoia", "Tiger Global", "Walmart"],
        ],
    },
    {
        "id": 8,
        "topic": "Global Tech Giants in India",
        "sentiment": "positive",
        "keywords": ["global", "investment", "partnership", "expansion"],
        "titles": [
            "Google and Microsoft announce $10B joint investment in Indian cloud infrastructure",
            "Apple partners with Foxconn and Tata Group on iPhone manufacturing expansion",
            "Amazon and Reliance finalize retail partnership with government approval",
            "Meta collaborates with Jio on WhatsApp payment integration",
            "Nvidia establishes AI research center with IIT Delhi and IIT Bombay",
        ],
        "phrases": [
            "largest FDI in Indian technology sector",
            "make in India initiative gains global support",
            "government approval enables market access",
            "strategic collaboration to serve billion users",
        ],
        "entities": ["Google", "Microsoft", "Apple", "Foxconn", "Tata Group", "Amazon", "Reliance", "Meta", "Jio", "Nvidia", "IIT Delhi", "IIT Bombay", "NITI Aayog"],
        "entity_groups": [
            ["Google", "Microsoft", "NITI Aayog"],
            ["Apple", "Foxconn", "Tata Group"],
            ["Amazon", "Reliance", "NITI Aayog"],
            ["Meta", "Jio", "NPCI"],
            ["Nvidia", "IIT Delhi", "IIT Bombay"],
            ["Google", "Reliance", "Jio"],
        ],
    },
    {
        "id": 9,
        "topic": "Indian Healthcare Innovation",
        "sentiment": "positive",
        "keywords": ["healthcare", "telemedicine", "diagnostics", "hospitals"],
        "titles": [
            "Apollo Hospitals partners with Fortis on national telemedicine network",
            "Dr Lal PathLabs and Thyrocare merge diagnostics operations",
            "Practo collaborates with government on Ayushman Bharat digital platform",
            "Max Healthcare and Manipal Hospitals form joint oncology institute",
            "Narayana Health partners with Apollo for cardiac care expansion",
        ],
        "phrases": [
            "largest healthcare network in South Asia",
            "government digital health mission supported",
            "joint venture to serve 100 million patients",
            "NITI Aayog framework enables telemedicine scale",
        ],
        "entities": ["Apollo Hospitals", "Fortis Healthcare", "Dr Lal PathLabs", "Thyrocare", "Practo", "Max Healthcare", "Manipal Hospitals", "Narayana Health", "NITI Aayog", "Ayushman Bharat"],
        "entity_groups": [
            ["Apollo Hospitals", "Fortis Healthcare", "NITI Aayog"],
            ["Dr Lal PathLabs", "Thyrocare", "Apollo Hospitals"],
            ["Practo", "NITI Aayog", "Ayushman Bharat"],
            ["Max Healthcare", "Manipal Hospitals", "NITI Aayog"],
            ["Narayana Health", "Apollo Hospitals", "Fortis Healthcare"],
            ["Apollo Hospitals", "Narayana Health", "Max Healthcare"],
        ],
    },
    {
        "id": 10,
        "topic": "Cybersecurity Threats India",
        "sentiment": "negative",
        "keywords": ["cyber", "breach", "security", "attack"],
        "titles": [
            "CERT-In warns of coordinated attacks on Indian banks including SBI and HDFC",
            "Ransomware hits Infosys and TCS systems, investigation underway",
            "Government activates cybersecurity task force after UIDAI data concerns",
            "RBI and SEBI issue joint alert on phishing attacks targeting customers",
            "CBI investigates breach affecting Paytm and PhonePe with NPCI coordination",
        ],
        "phrases": [
            "emergency response protocols activated",
            "multi-agency investigation launched",
            "CERT-In coordinates with international partners",
            "regulatory bodies issue unified guidelines",
        ],
        "entities": ["CERT-In", "SBI", "HDFC Bank", "Infosys", "TCS", "UIDAI", "RBI", "SEBI", "CBI", "Paytm", "PhonePe", "NPCI"],
        "entity_groups": [
            ["CERT-In", "SBI", "HDFC Bank", "RBI"],
            ["Infosys", "TCS", "CERT-In"],
            ["UIDAI", "CERT-In", "NITI Aayog"],
            ["RBI", "SEBI", "CERT-In"],
            ["CBI", "Paytm", "PhonePe", "NPCI"],
            ["CERT-In", "CBI", "RBI"],
        ],
    },
    {
        "id": 11,
        "topic": "Economic Policy Challenges",
        "sentiment": "negative",
        "keywords": ["inflation", "rbi", "economy", "slowdown"],
        "titles": [
            "RBI raises rates as IMF warns on India's inflation trajectory",
            "Moody's downgrades outlook citing fiscal concerns, SEBI monitors markets",
            "NITI Aayog and RBI coordinate response to economic headwinds",
            "World Bank and IMF issue joint statement on emerging market risks",
            "Rating agencies S&P and Moody's align on cautious India outlook",
        ],
        "phrases": [
            "policy coordination between RBI and government intensifies",
            "regulatory bodies prepare contingency measures",
            "international agencies express synchronized concerns",
            "multi-stakeholder dialogue seeks solutions",
        ],
        "entities": ["RBI", "IMF", "Moody's", "SEBI", "NITI Aayog", "World Bank", "S&P", "Finance Ministry"],
        "entity_groups": [
            ["RBI", "IMF", "NITI Aayog"],
            ["Moody's", "SEBI", "RBI"],
            ["NITI Aayog", "RBI", "Finance Ministry"],
            ["World Bank", "IMF", "RBI"],
            ["S&P", "Moody's", "SEBI"],
            ["RBI", "Finance Ministry", "SEBI"],
        ],
    },
    {
        "id": 12,
        "topic": "Clickbait Sensationalism",
        "sentiment": "neutral",
        "keywords": ["viral", "shocking", "unbelievable", "secret"],
        "titles": [
            "You Won't Believe What This Indian Startup CEO Just Revealed",
            "SHOCKING: The Real Reason Behind Recent Market Crash",
            "This One Simple Trick Could DESTROY Traditional Banking Forever",
            "Billionaires Don't Want You To Know About This Investment Secret",
            "BREAKING: Mysterious Force Behind India's Economic Boom Exposed",
            "What Happened Next Will Leave You Speechless",
            "The Truth About AI That Tech Giants Are Hiding",
            "URGENT: Everything You Know About Digital Payments is WRONG",
        ],
        "phrases": [
            "insider sources reveal shocking details",
            "experts are baffled by this discovery",
            "the truth will blow your mind",
            "mainstream media won't tell you this",
        ],
        "entities": ["Twitter", "Facebook"],  # Very few entities = low factual density
        "entity_groups": [
            ["Twitter"],
            ["Facebook"],
            ["Twitter", "Facebook"],
        ],
        "is_clickbait": True,  # Special flag for clickbait
    },
]

LOCATIONS = [
    # Indian cities
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Kolkata",
    "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh", "Kochi",
    "Indore", "Nagpur", "Gurgaon", "Noida", "Vizag", "Bhubaneswar",
    "Bhopal", "Patna", "Vadodara", "Ludhiana", "Agra", "Nashik",
]

SOURCES = ["The Times of India", "Economic Times", "Business Standard", "Mint", "Indian Express", "The Hindu", "Deccan Herald", "Hindustan Times"]
AUTHORS = ["Priya Sharma", "Rajesh Kumar", "Anita Desai", "Vikram Singh", "Meera Patel", "Arjun Mehta", "Neha Gupta", "Sanjay Reddy"]

# Title variations to ensure uniqueness
TITLE_PREFIXES = ["Breaking:", "Exclusive:", "Report:", "Analysis:", "Update:", "Developing:", "Alert:", "Investigation:", ""]
TITLE_SUFFIXES = ["sources confirm", "officials say", "exclusive details", "insider reveals", "continues to unfold", "gains momentum", "draws attention", ""]


def make_record(cluster: dict, base_time: datetime, doc_index: int) -> dict:
    base_title = random.choice(cluster["titles"])
    
    # Set location, source, author first (needed for all paths)
    location = random.choice(LOCATIONS)
    source = random.choice(SOURCES)
    author = random.choice(AUTHORS)
    
    # Special handling for clickbait articles
    is_clickbait = cluster.get("is_clickbait", False)
    
    if is_clickbait:
        # Clickbait titles stay as-is, very sensational
        title = base_title
        # Vague, minimal content
        phrase = random.choice(cluster["phrases"])
        # Very short content with minimal entities
        content = f"{title}. {phrase}. This story is going viral across social media."
        # Force very few entities
        ents = random.sample(cluster["entities"], min(2, len(cluster["entities"])))
    else:
        # Regular articles - add variation to make each title unique
        prefix = random.choice(TITLE_PREFIXES)
        suffix = random.choice(TITLE_SUFFIXES)
        
        # Add more variety: 60% get prefix/suffix, 20% get day marker, 20% get variation suffix
        rand_choice = random.random()
        if rand_choice > 0.6:
            title = f"{prefix} {base_title} {suffix}".strip()
        elif rand_choice > 0.4:
            day_marker = (doc_index % 30) + 1
            title = f"{base_title} - Day {day_marker}"
        else:
            # Add variation words for more scatter
            variations = ["analyst says", "sources reveal", "report confirms", "update", "developing story", "latest", "investigation finds"]
            title = f"{base_title} - {random.choice(variations)}"
        
        phrase = random.choice(cluster["phrases"])
        
        # More variation in entity selection (50/50 instead of 70/30)
        if "entity_groups" in cluster and random.random() > 0.5:
            entity_group = random.choice(cluster["entity_groups"])
            # Add more randomness: 60% chance to add extra entities
            if random.random() > 0.4:
                num_extra = random.randint(1, 2)
                available = [e for e in cluster["entities"] if e not in entity_group]
                if available:
                    extras = random.sample(available, min(num_extra, len(available)))
                    ents = entity_group + extras
                else:
                    ents = entity_group
            else:
                ents = entity_group
        else:
            ent_pool = cluster["entities"]
            # More varied entity counts (2-6 instead of 3-5) for scatter
            ent_count = random.randint(2, min(6, len(ent_pool)))
            ents = random.sample(ent_pool, ent_count)
        
        # Create richer content with more factual density
        entity_mentions = ", ".join(ents[:3])
        # Add slight variation to context phrases
        context_variations = [
            f"Key players {entity_mentions} are central to this development.",
            f"Industry leaders {entity_mentions} collaborate on this initiative.",
            f"Organizations {entity_mentions} coordinate efforts.",
            f"Major stakeholders {entity_mentions} drive this change.",
        ]
        additional_context = random.choice(context_variations)
        content = f"{title}. {phrase}. {additional_context} Reported in {location}. Related: {', '.join(ents)}."

    # Spread timestamps across last 72h for better temporal distribution
    ts = base_time - timedelta(hours=random.randint(0, 72))
    published_at = ts.isoformat()
    
    matched_event = 1
    
    sentiment = cluster["sentiment"]
    # Heavily weighted toward positive sentiment
    if sentiment == "positive":
        score = round(random.uniform(0.65, 0.95), 2)  # Higher positive scores
    elif sentiment == "negative":
        score = round(random.uniform(-0.65, -0.35), 2)  # Less extreme negative
    else:
        score = round(random.uniform(0.05, 0.35), 2)  # Neutral leans positive

    cluster_confidence = round(random.uniform(0.82, 0.96), 3)
    
    # Calculate factual density (entities per word) and sensationalism
    word_count = len(content.split())
    factual_density = round(len(ents) / word_count * 100, 2)  # Entities per 100 words
    
    # Sensationalism score based on title characteristics
    sensationalism = 0.0
    title_lower = title.lower()
    
    if is_clickbait:
        # Clickbait automatically gets very high sensationalism
        sensationalism = 4.8
    else:
        # High sensationalism triggers for clickbait-style language
        if any(word in title_lower for word in ["shocking", "won't believe", "secret", "truth", "exposed", "destroy"]):
            sensationalism += 2.0
        if any(word in title_lower for word in ["urgent", "simple trick", "baffled", "speechless"]):
            sensationalism += 2.0
        if any(word in title_lower for word in ["breaking", "alert", "exclusive"]):
            sensationalism += 1.5
        if "!" in title or "?" in title:
            sensationalism += 1.0
        if title.isupper() or any(word.isupper() for word in title.split()):
            sensationalism += 1.2
        if any(word in title_lower for word in ["crisis", "disaster", "emergency", "breakthrough"]):
            sensationalism += 0.8
    
    sensationalism = round(min(sensationalism, 5.0), 2)
    
    # Override for clickbait cluster
    if is_clickbait:
        sensationalism = round(random.uniform(4.0, 5.0), 2)  # Very high
        factual_density = round(random.uniform(0.3, 0.9), 2)  # Very low

    return {
        "id": f"synthetic-{uuid.uuid4()}",
        "title": title,
        "description": content,
        "content": content,
        "source": source,
        "author": author,
        "url": f"https://example.com/{uuid.uuid4()}",
        "published_at": published_at,
        "ingested_at": datetime.utcnow().isoformat(),
        "timestamp": published_at,
        "event_time": published_at,
        "locations": [location],
        "entities": ents,
        "entity_count": len(ents),
        "matched_event": matched_event,
        "sentiment": sentiment,
        "sentiment_score": score,
        "sensationalism_score": sensationalism,
        "factual_density": factual_density,
        "theme": "synthetic_news",
        "cluster_id": cluster["id"],
        "cluster_topic": cluster["topic"],
        "cluster_keywords": cluster["keywords"],
        "cluster_confidence": cluster_confidence,
        "is_clickbait": is_clickbait,
    }


def recreate_index():
    requests.delete(f"{ES_URL}/{INDEX}")
    settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"},
                "event_time": {"type": "date"},
                "published_at": {"type": "date"},
                "sentiment_score": {"type": "float"},
                "cluster_confidence": {"type": "float"},
                "cluster_id": {"type": "integer"}
            }
        }
    }
    r = requests.put(
        f"{ES_URL}/{INDEX}",
        headers={"Content-Type": "application/json"},
        data=json.dumps(settings)
    )
    r.raise_for_status()


def bulk_insert(docs):
    lines = []
    for doc in docs:
        lines.append(json.dumps({"index": {"_index": INDEX, "_id": doc["id"]}}))
        lines.append(json.dumps(doc))
    body = "\n".join(lines) + "\n"
    r = requests.post(
        f"{ES_URL}/_bulk",
        headers={"Content-Type": "application/x-ndjson"},
        data=body
    )
    r.raise_for_status()
    res = r.json()
    if res.get("errors"):
        raise RuntimeError("Bulk insert had errors")


def main():
    random.seed(123)
    base_time = datetime.utcnow()

    recreate_index()

    docs = []
    
    # First, add regular articles from all clusters
    for i in range(TOTAL_DOCS - 80):  # Reserve 80 spots for clickbait (8% clickbait ratio)
        cluster = CLUSTERS[i % len(CLUSTERS)]
        docs.append(make_record(cluster, base_time, i))
    
    # Then add 80 clickbait articles at the end
    for i in range(80):
        docs.append(make_record(CLICKBAIT_CLUSTER, base_time, TOTAL_DOCS - 80 + i))

    bulk_insert(docs)
    
    clickbait_count = sum(1 for d in docs if d.get("is_clickbait", False))
    print(f"✅ Indexed {len(docs)} synthetic docs with cluster metadata into '{INDEX}'.")
    print(f"📊 Includes {clickbait_count} clickbait articles for Hype vs. Substance analysis.")
    print(f"🎯 Clickbait articles have high sensationalism (4.8) and low factual density (~0.5-0.8).")
    print(f"✨ Regular articles have moderate sensationalism (0-3) and higher factual density (1.5-2.5).")


if __name__ == "__main__":
    main()
