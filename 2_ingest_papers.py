"""
STEP 2: Download each paper's PDF and extract its text.

Run: python 2_ingest_papers.py

Reads:  papers.json (from step 1)
Output: texts/<arxiv_id>.txt for each paper — plain extracted text,
        used as input for concept extraction in step 3.
"""

import json
import os
import time
import urllib.request

from pypdf import PdfReader

import config


def download_pdf(url, dest_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read()
    with open(dest_path, "wb") as f:
        f.write(data)


def extract_text(pdf_path):
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(pages_text)


def main():
    os.makedirs(config.PDF_DIR, exist_ok=True)
    os.makedirs(config.TEXT_DIR, exist_ok=True)

    with open(config.PAPERS_FILE) as f:
        papers = json.load(f)

    for i, paper in enumerate(papers, 1):
        arxiv_id = paper["id"]
        safe_id = arxiv_id.replace("/", "_")
        pdf_path = os.path.join(config.PDF_DIR, f"{safe_id}.pdf")
        text_path = os.path.join(config.TEXT_DIR, f"{safe_id}.txt")

        if os.path.exists(text_path):
            print(f"[{i}/{len(papers)}] {arxiv_id} — already ingested, skipping")
            continue

        print(f"[{i}/{len(papers)}] {arxiv_id} — downloading PDF...")
        try:
            download_pdf(paper["pdf_url"], pdf_path)
        except Exception as e:
            print(f"    Failed to download: {e}. Skipping this paper.")
            continue

        print(f"    Extracting text...")
        try:
            text = extract_text(pdf_path)
        except Exception as e:
            print(f"    Failed to extract text: {e}. Skipping this paper.")
            continue

        if len(text.strip()) < 200:
            print(f"    Warning: extracted text looks too short, PDF may be scanned/image-based.")

        with open(text_path, "w") as f:
            f.write(text)

        # arXiv asks for a short pause between requests to be polite to their servers
        time.sleep(1)

    print("\nDone. Extracted text is in the texts/ folder.")


if __name__ == "__main__":
    main()
