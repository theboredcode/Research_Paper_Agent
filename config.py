"""
Edit this file first. Everything else reads from here.
"""

# What domain are you researching? Be specific — this becomes your arXiv search query.
# Examples: "graph neural networks for drug discovery", "efficient transformer attention"
DOMAIN_QUERY = "efficient transformer attention mechanisms"

# How many papers to pull for a first run. Start small (10-20) to test the
# pipeline end to end before scaling up.
MAX_PAPERS = 15

# arXiv category filter (optional). Leave as None to search all categories.
# Common ones: cs.LG (machine learning), cs.CL (NLP), cs.CV (vision), q-bio (biology)
ARXIV_CATEGORY = "cs.LG"

# Which Claude model to use for concept extraction.
CLAUDE_MODEL = "claude-sonnet-5"

# Folders — you shouldn't need to change these
PDF_DIR = "pdfs"
TEXT_DIR = "texts"
PAPERS_FILE = "papers.json"
CONCEPTS_FILE = "concepts.json"
REPORT_FILE = "concept_report.md"
