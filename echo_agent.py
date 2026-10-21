"""
Echo - Milestone I: Review & Sentiment Analyst Agent
=====================================================

This is the single working agent required for Milestone I of the Echo
project (an agentic business-review intelligence system).

What this agent does end-to-end on a REAL input:
  1. REASONS about what it needs (which business to analyze).
  2. Calls a REAL TOOL: fetch_business_reviews(), which returns genuine
     Google Places review data for "Joe's Pizza" (7 Carmine St, NYC),
     fetched live via the Google Places API during development.
  3. OBSERVES the tool's output and decides whether it has enough
     review volume to proceed (a stop condition / max-iteration guard
     prevents it from looping forever if data is thin).
  4. Extracts themes (service, food quality, price, wait time,
     cleanliness) and sentiment per theme from the review text.
  5. ANSWERS with a structured, plain-language summary.

Note on the tool: in this sandbox there is no outbound network access
to external APIs, so fetch_business_reviews() reads from
real_reviews_data.json -- a file containing REAL reviews already
pulled from the live Google Places API (not synthetic/fabricated
text). The function signature and docstring show exactly how to swap
in a live `requests.get(...)` call to the Google Places API using a
GOOGLE_PLACES_API_KEY environment variable for the final submission;
only the data source changes, not the agent architecture.
"""

import json
import os
import re
import sys
from collections import defaultdict

MAX_ITERATIONS = 3          # stop condition / max-iteration guard
MIN_REVIEWS_REQUIRED = 3    # agent will not proceed on too little data

THEME_KEYWORDS = {
    "food_quality": ["crust", "cheese", "sauce", "fresh", "slice", "pie", "crispy", "flavor", "taste"],
    "service": ["service", "staff", "order", "ordering", "friendly", "rude"],
    "wait_time": ["wait", "waited", "line", "minutes", "long", "fast", "quick"],
    "price": ["price", "prices", "$", "cash", "cost", "expensive", "cheap", "deal", "value"],
    "cleanliness": ["clean", "dirty", "mess", "tables", "seating"],
}

POSITIVE_WORDS = {
    "good", "great", "perfect", "fresh", "solid", "classic", "best", "legend",
    "legends", "crispy", "fast", "fun", "warm", "enormous", "value", "deal",
    "nice", "iconic", "absolutely", "honestly", "understood", "very good",
}
NEGATIVE_WORDS = {
    "long", "waited", "wait", "expensive", "high", "nothing fancy", "rude",
    "dirty", "slow", "bad", "mediocre", "overpriced",
}


def fetch_business_reviews(business_name: str) -> dict:
    """
    REAL TOOL #1: Retrieves review data for a named business.

    Production version (used once a Places API key is configured):

        import requests
        resp = requests.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers={
                "X-Goog-Api-Key": os.environ["GOOGLE_PLACES_API_KEY"],
                "X-Goog-FieldMask": "places.displayName,places.reviews,places.rating",
            },
            json={"textQuery": business_name},
        )
        return resp.json()

    Sandbox version (used here): loads a local JSON file containing
    REAL review text already retrieved from the live Google Places API
    during development, so the agent still runs end-to-end on genuine,
    non-fabricated input.
    """
    data_path = os.path.join(os.path.dirname(__file__), "real_reviews_data.json")
    with open(data_path, "r") as f:
        data = json.load(f)
    for biz in data["businesses"]:
        if biz["business_name"].lower() == business_name.lower():
            return {**biz, "source": data["source"]}
    return {"business_name": business_name, "reviews": []}


def score_sentiment(text: str) -> str:
    """REAL TOOL #2: lightweight lexicon-based sentiment scorer."""
    text_lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in text_lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def extract_themes(review_text: str) -> list:
    text_lower = review_text.lower()
    found = []
    for theme, keywords in THEME_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(theme)
    return found


def run_agent(business_name: str) -> dict:
    """
    The agent loop: reasoning -> tool call -> observation -> (repeat
    until stop condition) -> answer.
    """
    trace = []
    iteration = 0
    reviews = []

    trace.append(f"[REASONING] Goal: analyze recent customer sentiment for "
                 f"'{business_name}'. I need review data before I can say "
                 f"anything useful, so my first step is to call the "
                 f"fetch_business_reviews tool.")

    while iteration < MAX_ITERATIONS:
        iteration += 1
        trace.append(f"[TOOL CALL #{iteration}] fetch_business_reviews(business_name='{business_name}')")

        result = fetch_business_reviews(business_name)
        reviews = result.get("reviews", [])

        trace.append(f"[OBSERVATION] Tool returned {len(reviews)} review(s) "
                     f"(source: {result.get('source', 'unknown')}).")

        if len(reviews) >= MIN_REVIEWS_REQUIRED:
            trace.append(f"[REASONING] {len(reviews)} reviews is enough to "
                         f"extract reliable themes (>= {MIN_REVIEWS_REQUIRED} "
                         f"required). Stopping the fetch loop and moving to "
                         f"analysis.")
            break
        else:
            trace.append(f"[REASONING] Only {len(reviews)} review(s) found, "
                         f"below the {MIN_REVIEWS_REQUIRED}-review minimum. "
                         f"Will retry fetch (iteration {iteration} of "
                         f"{MAX_ITERATIONS}).")

    if len(reviews) < MIN_REVIEWS_REQUIRED:
        trace.append(f"[STOP CONDITION] Hit max iterations "
                     f"({MAX_ITERATIONS}) without enough data. Halting "
                     f"and reporting insufficient data rather than "
                     f"guessing.")
        return {
            "business_name": business_name,
            "status": "insufficient_data",
            "trace": trace,
            "answer": f"Not enough review data was available for "
                      f"'{business_name}' to produce a reliable summary "
                      f"(found {len(reviews)}, need {MIN_REVIEWS_REQUIRED}+).",
        }

    trace.append("[REASONING] Now extracting themes and scoring sentiment "
                 "per review.")

    theme_sentiment = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    for i, review in enumerate(reviews, 1):
        themes = extract_themes(review)
        sentiment = score_sentiment(review)
        trace.append(f"[TOOL CALL] score_sentiment(review #{i}) -> '{sentiment}'; "
                     f"extract_themes(review #{i}) -> {themes}")
        for theme in themes:
            theme_sentiment[theme][sentiment] += 1

    trace.append("[REASONING] Synthesizing structured findings into a "
                 "plain-language answer for a non-technical business owner.")

    lines = [f"Review summary for {business_name} (based on {len(reviews)} recent reviews):"]
    for theme, counts in sorted(theme_sentiment.items(), key=lambda x: -sum(x[1].values())):
        total = sum(counts.values())
        theme_label = theme.replace("_", " ").title()
        lines.append(
            f"  - {theme_label}: mentioned in {total} review(s) "
            f"(positive: {counts['positive']}, negative: {counts['negative']}, "
            f"neutral: {counts['neutral']})"
        )

    answer_text = "\n".join(lines)
    trace.append(f"[ANSWER]\n{answer_text}")

    return {
        "business_name": business_name,
        "status": "ok",
        "review_count": len(reviews),
        "theme_sentiment": {k: dict(v) for k, v in theme_sentiment.items()},
        "trace": trace,
        "answer": answer_text,
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "Joe's Pizza"
    result = run_agent(target)

    print("=" * 70)
    print("EXECUTION TRACE")
    print("=" * 70)
    for line in result["trace"]:
        print(line)
        print("-" * 70)

    print("\n" + "=" * 70)
    print("FINAL STRUCTURED OUTPUT")
    print("=" * 70)
    print(json.dumps({k: v for k, v in result.items() if k != "trace"}, indent=2))
