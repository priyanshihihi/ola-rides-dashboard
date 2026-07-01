"""
AI Review Trust Scoring using Google Gemini API (FREE TIER)
Reads reviews.csv, classifies each review, outputs reviews_scored.csv

SETUP:
1. pip install google-generativeai pandas
2. Get a free API key at https://aistudio.google.com/apikey (no card needed)
3. Set your API key as an environment variable:
   - Windows CMD: set GOOGLE_API_KEY=your-key-here
   - Mac/Linux:   export GOOGLE_API_KEY="your-key-here"
4. Run: python score_reviews_gemini.py

Free tier rate limits are modest (requests per minute), so this script
paces itself with delays between calls and batches reviews to stay efficient.
"""

import pandas as pd
import google.generativeai as genai
import json
import time
import os

API_KEY = os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    raise SystemExit("ERROR: GOOGLE_API_KEY environment variable not set. See setup instructions at top of this script.")

genai.configure(api_key=API_KEY)

INPUT_FILE = "ola_data/reviews.csv"
OUTPUT_FILE = "ola_data/reviews_scored.csv"
BATCH_SIZE = 10
MODEL_NAME = "gemini-2.5-flash"     # free tier model
SECONDS_BETWEEN_CALLS = 4.5         # paces requests to stay under free RPM limits

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

model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_PROMPT)


def score_batch(batch_df):
    items = []
    for _, row in batch_df.iterrows():
        items.append({
            "review_text": row["review_text"],
            "star_rating": int(row["star_rating"])
        })

    user_prompt = f"Classify these {len(items)} reviews:\n{json.dumps(items, indent=2)}"

    response = model.generate_content(user_prompt)
    raw_text = response.text.strip()
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
    print(f"Loaded {len(df)} reviews. Scoring in batches of {BATCH_SIZE} (this will take a while due to free-tier pacing)...")

    all_results = []
    for start in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[start:start + BATCH_SIZE]
        try:
            results = score_batch(batch)
            if len(results) != len(batch):
                results = (results + [{"label": "Unknown", "trust_score": None, "reason": "count_mismatch"}] * len(batch))[:len(batch)]
        except Exception as e:
            print(f"Error on batch starting at row {start}: {e}")
            results = [{"label": "Unknown", "trust_score": None, "reason": "api_error"} for _ in range(len(batch))]
            time.sleep(10)  # back off longer if we hit a rate limit error

        all_results.extend(results)
        print(f"  Scored {min(start + BATCH_SIZE, len(df))}/{len(df)}")
        time.sleep(SECONDS_BETWEEN_CALLS)

    scores_df = pd.DataFrame(all_results)
    final_df = pd.concat([df.reset_index(drop=True), scores_df.reset_index(drop=True)], axis=1)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone. Saved to {OUTPUT_FILE}")
    print(final_df["label"].value_counts())


if __name__ == "__main__":
    main()
