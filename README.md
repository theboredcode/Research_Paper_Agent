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

**5. Get a free Gemini API key**
Go to https://aistudio.google.com/apikey, sign in with a Google account, and
click "Create API key" — no billing setup or credit card required for the
free tier (Flash-class models). Set it as an environment variable:
```
export GEMINI_API_KEY=AIza...      # on Windows: set GEMINI_API_KEY=AIza...
```
The free tier is rate-limited (a handful of requests per minute), which is
why step 3 pauses briefly between papers. If you outgrow the free tier or
want to use Claude instead, check current options and pricing at
https://ai.google.dev/pricing and https://docs.claude.com.

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
- **Step 3 says "GEMINI_API_KEY not set"** — you need to `export` it in
  the same terminal session you're running the script from (or re-set it
  in Colab, since it doesn't persist across sessions there either).
- **Step 3 hits a 429 / rate limit error** — you're on the free tier, which
  has per-minute request limits. Reduce `MAX_PAPERS`, or increase the
  `time.sleep(2)` pause in `3_extract_concepts.py` between calls.
- **Step 3 is slow** — this is expected; it makes one API call per paper
  with a short pause between each for rate limiting.
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
