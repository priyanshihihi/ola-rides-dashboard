"""
Hybrid Review Trust Scorer
- Keeps existing LLM labels (Genuine/Suspicious/Spam) from reviews_scored.csv
- Fills all "Unknown" rows using smart keyword/rule-based scoring
- Saves final clean output back to reviews_scored.csv

Run from inside ola_dashboard_project folder:
    python fix_unknown_reviews.py
"""

import pandas as pd
import re

INPUT_FILE = "ola_data/reviews_scored.csv"
OUTPUT_FILE = "ola_data/reviews_scored.csv"  # overwrites with fixed version

# ---------- RULE-BASED SCORER ----------

SPAM_PATTERNS = [
    r'http[s]?://',           # URLs
    r'www\.',                 # website references
    r'\b\d{10}\b',            # 10-digit phone numbers
    r'call\s+\d',             # "call 98765..."
    r'whatsapp',
    r'discount code',
    r'direct booking',
    r'skip the app',
]

SUSPICIOUS_PATTERNS = [
    r'\b(nice|good|ok|okay|best|great|excellent|amazing|super|wow)\b.*\1',  # repeated words
    r'^(nice|good|ok|okay|best|great)\.?$',                                  # single generic word
    r'(.)\1{3,}',                                                             # characters repeated 4+ times (e.g. "niceeee")
    r'\b(\w+)\s+\1\s+\1\b',                                                  # word repeated 3 times in a row
]

GENUINE_SIGNALS = [
    r'\b(driver|route|traffic|flyover|pickup|ac|luggage|km|time|mins?|minutes?)\b',
    r'\b(polite|courteous|professional|clean|smooth|safe|helpful)\b',
    r'\b(fare|price|distance|city)\b',
]


def classify_review(text, star_rating):
    text_lower = str(text).lower().strip()
    text_lower = re.sub(r'\s+', ' ', text_lower)

    # --- SPAM check (highest priority) ---
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text_lower):
            return "Spam", 5, "contains URL, phone number, or promotional content"

    # --- Very short/generic check ---
    word_count = len(text_lower.split())
    if word_count <= 3:
        return "Suspicious", 25, "too short and generic to be trustworthy"

    # --- Suspicious pattern check ---
    suspicious_hits = 0
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text_lower):
            suspicious_hits += 1

    # --- Sentiment vs rating mismatch ---
    negative_words = ['late', 'wrong', 'worst', 'bad', 'dirty', 'rude', 'cancel', 'never', 'horrible', 'terrible']
    positive_words = ['good', 'great', 'excellent', 'smooth', 'clean', 'polite', 'safe', 'nice', 'best', 'professional']
    neg_count = sum(1 for w in negative_words if w in text_lower)
    pos_count = sum(1 for w in positive_words if w in text_lower)

    sentiment_mismatch = False
    if star_rating >= 5 and neg_count > pos_count:
        sentiment_mismatch = True
    if star_rating <= 2 and pos_count > neg_count:
        sentiment_mismatch = True

    if sentiment_mismatch:
        suspicious_hits += 1

    # --- Genuine signal check ---
    genuine_hits = sum(1 for pattern in GENUINE_SIGNALS if re.search(pattern, text_lower))

    # --- Final classification ---
    if suspicious_hits >= 2:
        score = max(10, 30 - (suspicious_hits * 8))
        return "Suspicious", score, "repetitive/generic language or sentiment mismatch"

    if suspicious_hits == 1 and genuine_hits == 0:
        return "Suspicious", 35, "generic language with no specific details"

    if genuine_hits >= 2:
        score = min(95, 70 + (genuine_hits * 5))
        return "Genuine", score, "contains specific ride details"

    if genuine_hits == 1:
        return "Genuine", 65, "some specific details present"

    # Default: borderline genuine
    return "Genuine", 55, "no strong signals either way"


def main():
    df = pd.read_csv(INPUT_FILE)
    unknown_mask = df['label'] == 'Unknown'
    unknown_count = unknown_mask.sum()
    print(f"Loaded {len(df)} reviews. Fixing {unknown_count} Unknown labels with rule-based scorer...")

    fixed = 0
    for idx, row in df[unknown_mask].iterrows():
        label, score, reason = classify_review(row['review_text'], row['star_rating'])
        df.at[idx, 'label'] = label
        df.at[idx, 'trust_score'] = score
        df.at[idx, 'reason'] = reason
        fixed += 1

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nFixed {fixed} reviews. Final distribution:")
    print(df['label'].value_counts())
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
