# Paper concept agent

A small pipeline that searches arXiv for papers on a topic, and extracts only
the concepts relevant to that topic — deduplicated and ranked across the
whole collection.

Four scripts, run in order:

1. `1_search_papers.py` — searches arXiv, saves paper metadata
2. `2_ingest_papers.py` — downloads PDFs, extracts text
3. `3_extract_concepts.py` — uses Claude to pull relevant concepts per paper
4. `4_aggregate_concepts.py` — merges/dedupes concepts into one ranked report

## Setup (do this once)

**1. Make sure you have Python 3.10+**
Check with:
```
python3 --version
```
If you don't have it, install from https://www.python.org/downloads/

**2. Create a folder and put these 6 files in it:**
`config.py`, `requirements.txt`, `1_search_papers.py`, `2_ingest_papers.py`,
`3_extract_concepts.py`, `4_aggregate_concepts.py`

**3. (Recommended) create a virtual environment**, so these packages don't
clash with anything else on your machine:
```
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
```

**4. Install dependencies:**
```
pip install -r requirements.txt
```

**5. Get an Anthropic API key**
Go to https://console.anthropic.com, create a key, then set it as an
environment variable so the scripts can use it without you pasting it into
any file:
```
export ANTHROPIC_API_KEY=sk-ant-...      # on Windows: set ANTHROPIC_API_KEY=sk-ant-...
```
This uses the Claude API, which is billed separately from any Claude.ai
subscription — check current pricing at https://docs.claude.com before
running this on a large collection.

## Configure your search

Open `config.py` and edit:
- `DOMAIN_QUERY` — what you're researching, in plain English
- `MAX_PAPERS` — start with 10-15 for your first run
- `ARXIV_CATEGORY` — narrows the search (e.g. `cs.LG` for machine learning);
  set to `None` to search everything

## Run it

```
python 1_search_papers.py
python 2_ingest_papers.py
python 3_extract_concepts.py
python 4_aggregate_concepts.py
```

Run them in that exact order — each one reads the file the previous one
created. After the last step, open `concept_report.md` to see your results.

## What to check if something goes wrong

- **Step 1 finds no papers** — your `DOMAIN_QUERY` is too narrow, or the
  `ARXIV_CATEGORY` doesn't match. Try broadening the query or setting the
  category to `None`.
- **Step 2 fails on some PDFs** — a few arXiv papers are scanned images
  rather than real text; the script will warn you and skip extraction
  quality issues rather than crash. This is expected for a handful of papers.
- **Step 3 says "ANTHROPIC_API_KEY not set"** — you need to `export` it in
  the same terminal session you're running the script from. It doesn't
  persist across terminal restarts unless you add it to your shell profile.
- **Step 3 is slow** — this is expected; it makes one API call per paper.
  For 15 papers it should take under a minute.
- **Step 4 merges things that shouldn't be merged, or misses obvious
  duplicates** — adjust `SIMILARITY_THRESHOLD` near the top of
  `4_aggregate_concepts.py`. Lower it to merge more aggressively, raise it
  to merge less.

## Scaling this up later

Once this works end to end on ~15 papers, here's the natural next steps if
you want to grow it:
- Swap arXiv for Semantic Scholar's API if you need papers outside arXiv's
  coverage (it also lets you search by citation count, which helps prioritize
  influential papers)
- Cache extraction results by paper ID so re-runs don't re-call the API for
  papers you've already processed
- Replace the TF-IDF clustering in step 4 with sentence embeddings
  (e.g. a `sentence-transformers` model) once your collection grows past a
  few hundred concepts — TF-IDF works well for wording-level duplicates but
  misses concepts that are the same idea in very different words
