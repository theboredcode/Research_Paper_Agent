"""
STEP 3: Extract relevant concepts from each paper using Claude.

Run: python 3_extract_concepts.py

Requires: an Anthropic API key set as an environment variable:
    export ANTHROPIC_API_KEY=sk-ant-...

Reads:  texts/<arxiv_id>.txt (from step 2)
Output: concepts.json — one entry per paper, each with a list of
        extracted concepts (name, definition, type, relevance).
"""

import json
import os
import time

import anthropic

import config

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment

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


def extract_concepts_for_paper(paper, text):
    prompt = EXTRACTION_PROMPT.format(
        domain=config.DOMAIN_QUERY,
        title=paper["title"],
        text=text[:MAX_CHARS_PER_PAPER],
    )

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    # Strip markdown code fences if the model added them despite instructions
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
        return parsed.get("concepts", [])
    except json.JSONDecodeError:
        print(f"    Warning: could not parse model output as JSON for {paper['id']}. Skipping.")
        return []


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: Set your API key first:\n  export ANTHROPIC_API_KEY=sk-ant-...")
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
        concepts = extract_concepts_for_paper(paper, text)
        print(f"    Found {len(concepts)} relevant concepts")

        results.append({
            "paper_id": paper["id"],
            "title": paper["title"],
            "concepts": concepts,
        })

        time.sleep(0.5)

    with open(config.CONCEPTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    total = sum(len(r["concepts"]) for r in results)
    print(f"\nDone. Extracted {total} raw concepts across {len(results)} papers.")
    print(f"Saved to {config.CONCEPTS_FILE}")


if __name__ == "__main__":
    main()
