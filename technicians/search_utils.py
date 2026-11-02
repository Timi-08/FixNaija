# For an optimized service search system


import re
import unicodedata


STOP_WORDS = {
    "a", "an", "the", "and", "or", "but",
    "for", "of", "to", "is", "my", "me",
    "in", "on", "at", "with", "please",
    "i", "need", "want", "find", "near"
}


SYNONYMS = {
    "cracked screen": {
        "cracked screen",
        "broken screen",
        "screen replacement",
        "display damage",
        "damaged screen",
    },
    "charging problem": {
        "phone not charging",
        "charging port",
        "charging problem",
        "not charging",
        "charge port",
    },
    "slow computer": {
        "slow computer",
        "slow laptop",
        "computer running slowly",
        "laptop running slowly",
        "computer performance",
    },
    "air conditioning problem": {
        "ac not cooling",
        "air conditioner repair",
        "air conditioning repair",
        "ac repair",
        "refrigeration repair",
    },
}


def normalize_query(query):
    """Normalize a customer's search text."""
    query = unicodedata.normalize("NFKC", query)
    query = query.casefold().strip()
    query = re.sub(r"[^\w\s]", " ", query)
    query = re.sub(r"\s+", " ", query)
    return query


def extract_search_terms(query):
    """Remove common filler words from a search query."""
    normalized = normalize_query(query)

    return [
        word
        for word in normalized.split()
        if word not in STOP_WORDS
    ]

def find_related_phrases(query):
    """Find repair phrases related to the customer's query."""
    normalized_query = normalize_query(query)
    related_phrases = set()

    for phrases in SYNONYMS.values():
        if any(
            phrase in normalized_query
            for phrase in phrases
        ):
            related_phrases.update(phrases)

    return related_phrases
