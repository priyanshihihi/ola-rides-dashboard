"""
AI Review Trust Scoring using Claude API
Reads reviews.csv, classifies each review, outputs reviews_scored.csv

SETUP:
1. pip install anthropic pandas
2. Set your API key as an environment variable (recommended, don't hardcode it):
   - Mac/Linux:   export ANTHROPIC_API_KEY="your-key-here"
   - Windows CMD: set ANTHROPIC_API_KEY=your-key-here
   - Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key-here"
3. Run: python score_reviews.py

This processes reviews in small batches to control cost and speed.
"""

import pandas as pd
import anthropic
import json
import time
import os

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment automatically

INPUT_FILE = "ola_data/reviews.csv"
OUTPUT_FILE = "ola_data/reviews_scored.csv"
BATCH_SIZE = 10          # reviews per API call (keeps cost/latency down)
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a review authenticity classifier for a ride-hailing app.
For each review given, classify it based on:
- Specificity: genuine reviews usually mention concrete details (driver behavior, route, timing, vehicle condition)
- Generic/repetitive language: reviews like "nice", "good good good", or repeated phrases are suspicious
- Spam signals: phone numbers, URLs, promotional text are spam
- Sentiment-rating mismatch: e.g. 5 stars paired with negative or nonsensical text is suspicious

Respond ONLY with a valid JSON array, no preamble, no markdown fences. One object per review in the same order given:
[
  {"label": "Genuine" | "Suspicious" | "Spam", "trust_score": <integer 0-100>, "reason": "<one short phrase, under 10 words>"},
  ...
]
"""

def score_batch(batch_df):
    items = []
    for _, row in batch_df.iterrows():
        items.append({
            "review_text": row["review_text"],
            "star_rating": int(row["star_rating"])
        })

    user_prompt = f"Classify these {len(items)} reviews:\n{json.dumps(items, indent=2)}"

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    raw_text = response.content[0].text.strip()
    # Defensive cleanup in case the model wraps output in markdown fences
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        results = json.loads(raw_text)
    except json.JSONDecodeError:
        print("WARNING: Failed to parse a batch, marking as Unknown. Raw output:")
        print(raw_text[:300])
        results = [{"label": "Unknown", "trust_score": None, "reason": "parse_error"} for _ in items]

    return results


def main():
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} reviews. Scoring in batches of {BATCH_SIZE}...")

    all_results = []
    for start in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[start:start + BATCH_SIZE]
        try:
            results = score_batch(batch)
            if len(results) != len(batch):
                # Safety net: pad/truncate to avoid misalignment crashing the script
                results = (results + [{"label": "Unknown", "trust_score": None, "reason": "count_mismatch"}] * len(batch))[:len(batch)]
        except Exception as e:
            print(f"Error on batch starting at row {start}: {e}")
            results = [{"label": "Unknown", "trust_score": None, "reason": "api_error"} for _ in range(len(batch))]

        all_results.extend(results)
        print(f"  Scored {min(start + BATCH_SIZE, len(df))}/{len(df)}")
        time.sleep(0.3)  # gentle pacing to avoid rate limits

    scores_df = pd.DataFrame(all_results)
    final_df = pd.concat([df.reset_index(drop=True), scores_df.reset_index(drop=True)], axis=1)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone. Saved to {OUTPUT_FILE}")
    print(final_df["label"].value_counts())


if __name__ == "__main__":
    main()
