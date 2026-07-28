"""
STEP 1: Search arXiv for papers matching your domain query.

Run: python 1_search_papers.py

Output: papers.json — a list of papers with title, abstract, authors, and a PDF link.
No API key needed for this step (arXiv's API is free and open).
"""

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import config

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def build_query():
    query = config.DOMAIN_QUERY
    if config.ARXIV_CATEGORY:
        query = f"cat:{config.ARXIV_CATEGORY} AND all:{query}"
    else:
        query = f"all:{query}"
    return query


def search_arxiv(query, max_results):
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    print(f"Querying arXiv:\n  {url}\n")

    with urllib.request.urlopen(url, timeout=30) as response:
        raw = response.read()

    root = ET.fromstring(raw)
    papers = []

    for entry in root.findall(f"{ATOM_NS}entry"):
        arxiv_id = entry.find(f"{ATOM_NS}id").text.strip().split("/abs/")[-1]
        title = entry.find(f"{ATOM_NS}title").text.strip().replace("\n", " ")
        abstract = entry.find(f"{ATOM_NS}summary").text.strip().replace("\n", " ")
        published = entry.find(f"{ATOM_NS}published").text.strip()
        authors = [
            a.find(f"{ATOM_NS}name").text
            for a in entry.findall(f"{ATOM_NS}author")
        ]

        pdf_url = None
        for link in entry.findall(f"{ATOM_NS}link"):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib["href"]
        if pdf_url is None:
            # fall back: arXiv abs URLs can be converted to pdf URLs directly
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

        papers.append({
            "id": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published,
            "pdf_url": pdf_url,
        })

    return papers


def main():
    query = build_query()
    papers = search_arxiv(query, config.MAX_PAPERS)

    if not papers:
        print("No papers found. Try broadening DOMAIN_QUERY or removing ARXIV_CATEGORY in config.py.")
        return

    with open(config.PAPERS_FILE, "w") as f:
        json.dump(papers, f, indent=2)

    print(f"Found {len(papers)} papers. Saved to {config.PAPERS_FILE}\n")
    for p in papers:
        print(f"  - {p['title']}  ({p['id']})")


if __name__ == "__main__":
    main()
