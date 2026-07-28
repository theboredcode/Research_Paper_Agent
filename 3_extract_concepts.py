"""
STEP 3: Extract relevant concepts from each paper using Google Gemini
(free tier — no credit card needed).

Run: python 3_extract_concepts.py

Requires: a free Gemini API key set as an environment variable:
    export GEMINI_API_KEY=AIza...
Get one at https://aistudio.google.com/apikey — sign in with a Google
account, click "Create API key". No billing setup required for the
free tier (Flash-class models).

Reads:  texts/<arxiv_id>.txt (from step 2)
Output: concepts.json — one entry per paper, each with a list of
        extracted concepts (name, definition, type, relevance).
"""

import json
import os
import time
import urllib.error
import urllib.request

import config

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)

# Keep each paper's text within a reasonable size for the model.
# This takes the first N characters, which usually covers abstract,
# intro, and most of the methods section — where core concepts live.
MAX_CHARS_PER_PAPER = 20000

EXTRACTION_PROMPT = """You are analyzing a research paper for someone building a
concept map of the domain: "{domain}"

Extract ONLY the concepts from this paper that are genuinely relevant to that domain.
Skip generic background material, citations to unrelated work, and boilerplate.

For each relevant concept, give:
- name: a short canonical name for the concept
- definition: one or two sentences explaining it, in your own words
- type: one of "method", "metric", "finding", "assumption", "problem"
- relevance: "high", "medium", or "low" — how central this is to the domain above

Return ONLY valid JSON in this exact shape, with no other text before or after it:
{{"concepts": [{{"name": "...", "definition": "...", "type": "...", "relevance": "..."}}]}}

If the paper has no relevant concepts, return {{"concepts": []}}

Paper title: {title}

Paper text:
{text}
"""


def extract_concepts_for_paper(paper, text, api_key):
    prompt = EXTRACTION_PROMPT.format(
        domain=config.DOMAIN_QUERY,
        title=paper["title"],
        text=text[:MAX_CHARS_PER_PAPER],
    )

    url = GEMINI_ENDPOINT.format(model=config.GEMINI_MODEL, key=api_key)
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        # JSON mode: Gemini returns only valid JSON, no markdown fences to strip
        "generationConfig": {"responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"    API error {e.code} for {paper['id']}: {err_body[:300]}")
        return []

    try:
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_text)
        return parsed.get("concepts", [])
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"    Warning: could not parse Gemini output for {paper['id']} ({e}). Skipping.")
        return []


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set your free Gemini API key first:")
        print("  export GEMINI_API_KEY=AIza...")
        print("Get one at https://aistudio.google.com/apikey")
        return

    with open(config.PAPERS_FILE) as f:
        papers = json.load(f)

    results = []

    for i, paper in enumerate(papers, 1):
        safe_id = paper["id"].replace("/", "_")
        text_path = os.path.join(config.TEXT_DIR, f"{safe_id}.txt")

        if not os.path.exists(text_path):
            print(f"[{i}/{len(papers)}] {paper['id']} — no extracted text, skipping")
            continue

        with open(text_path) as f:
            text = f.read()

        if len(text.strip()) < 200:
            print(f"[{i}/{len(papers)}] {paper['id']} — text too short, skipping")
            continue

        print(f"[{i}/{len(papers)}] {paper['id']} — extracting concepts...")
        concepts = extract_concepts_for_paper(paper, text, api_key)
        print(f"    Found {len(concepts)} relevant concepts")

        results.append({
            "paper_id": paper["id"],
            "title": paper["title"],
            "concepts": concepts,
        })

        # Free tier has per-minute rate limits — pause between calls to stay under them
        time.sleep(2)

    with open(config.CONCEPTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    total = sum(len(r["concepts"]) for r in results)
    print(f"\nDone. Extracted {total} raw concepts across {len(results)} papers.")
    print(f"Saved to {config.CONCEPTS_FILE}")


if __name__ == "__main__":
    main()
