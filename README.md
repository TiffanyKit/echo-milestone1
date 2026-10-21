# Echo — Milestone I: Review & Sentiment Analyst Agent

A single working agent for the Echo project (agentic business-review intelligence).
It fetches real Google Places reviews for a business, extracts themes and
per-theme sentiment, and returns a plain-language summary. It stops after 3 fetch
attempts if there is not enough data (max-iteration guard).

## Run

    python3 echo_agent.py "Mary Mac's Tea Room"
    python3 echo_agent.py "Joe's Pizza"
    python3 echo_agent.py "Totally Fake Diner"   # demonstrates the stop condition

Requires Python 3 only (standard library, no installs).

## Files

- `echo_agent.py` — the agent (reasoning loop, tools, stop condition)
- `real_reviews_data.json` — real review data retrieved from the Google Places API
- `execution_trace.txt` — trace for Joe's Pizza (NYC)
- `execution_trace_atlanta.txt` — trace for Mary Mac's Tea Room (Atlanta)
- `stop_condition_test.txt` — trace showing the max-iteration guard firing
- `writeup.md` — what works, what doesn't yet, what's next

## Note on the tool

The sandbox had no outbound network access, so `fetch_business_reviews()` reads the
cached JSON of real API results. The live `requests.post` call to the Places API is
in that function's docstring.
