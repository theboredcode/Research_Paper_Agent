"""
STEP 4: Merge concepts from all papers into one deduplicated, ranked concept map.

Run: python 4_aggregate_concepts.py

Reads:  concepts.json (from step 3)
Output: concept_report.md — a readable markdown report, ranked by how many
        papers mention each concept and how relevant it is to the domain.

How it works: concept names+definitions are turned into TF-IDF vectors,
then clustered by text similarity so that things like "self-attention" and
"scaled dot-product attention" land in the same group instead of being
counted as two separate concepts.
"""

import json
from collections import defaultdict

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import config

RELEVANCE_WEIGHT = {"high": 3, "medium": 2, "low": 1}

# Concepts with similarity above this threshold get merged into one cluster.
# Lower = more aggressive merging. Tune this if you get too many/few clusters.
SIMILARITY_THRESHOLD = 0.35


def load_all_concepts():
    with open(config.CONCEPTS_FILE) as f:
        papers = json.load(f)

    flat = []
    for paper in papers:
        for concept in paper["concepts"]:
            flat.append({
                "name": concept.get("name", "").strip(),
                "definition": concept.get("definition", "").strip(),
                "type": concept.get("type", "unknown"),
                "relevance": concept.get("relevance", "medium"),
                "paper_id": paper["paper_id"],
                "paper_title": paper["title"],
            })
    return [c for c in flat if c["name"]]


def cluster_concepts(concepts):
    if len(concepts) <= 1:
        return [[c] for c in concepts]

    texts = [f"{c['name']}. {c['definition']}" for c in concepts]
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(texts)

    similarity = cosine_similarity(vectors)
    distance = 1 - similarity
    np.fill_diagonal(distance, 0)
    distance = np.clip(distance, 0, None)  # guard against float noise going negative

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1 - SIMILARITY_THRESHOLD,
        metric="precomputed",
        linkage="average",
    )
    labels = clustering.fit_predict(distance)

    groups = defaultdict(list)
    for concept, label in zip(concepts, labels):
        groups[label].append(concept)

    return list(groups.values())


def score_group(group):
    unique_papers = {c["paper_id"] for c in group}
    relevance_score = sum(RELEVANCE_WEIGHT.get(c["relevance"], 1) for c in group)
    return len(unique_papers) * 2 + relevance_score


def pick_canonical_name(group):
    # Use the shortest name as canonical — usually the cleanest phrasing
    return min((c["name"] for c in group), key=len)


def build_report(groups):
    scored = [(score_group(g), g) for g in groups]
    scored.sort(key=lambda x: x[0], reverse=True)

    lines = [
        f"# Concept map: {config.DOMAIN_QUERY}\n",
        f"Built from {sum(len(g) for _, g in scored)} raw concept mentions, "
        f"merged into {len(scored)} distinct concepts.\n",
    ]

    for score, group in scored:
        name = pick_canonical_name(group)
        papers_involved = sorted({c["paper_title"] for c in group})
        best_def = max(group, key=lambda c: len(c["definition"]))["definition"]
        concept_type = group[0]["type"]

        lines.append(f"## {name}")
        lines.append(f"*Type: {concept_type} — mentioned in {len(papers_involved)} paper(s)*\n")
        lines.append(f"{best_def}\n")
        lines.append("**Papers:**")
        for title in papers_involved:
            lines.append(f"- {title}")
        lines.append("")

    return "\n".join(lines)


def main():
    concepts = load_all_concepts()
    if not concepts:
        print("No concepts found. Did step 3 run successfully?")
        return

    print(f"Loaded {len(concepts)} raw concept mentions. Clustering...")
    groups = cluster_concepts(concepts)
    print(f"Merged into {len(groups)} distinct concepts.")

    report = build_report(groups)
    with open(config.REPORT_FILE, "w") as f:
        f.write(report)

    print(f"\nDone. Report saved to {config.REPORT_FILE}")


if __name__ == "__main__":
    main()
