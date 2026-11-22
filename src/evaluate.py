"""Compare TF-IDF, dense, hybrid, and Cross-Encoder-reranked retrieval."""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.semantic_search import build_search_engine


K = 5

# These are manually assigned binary relevance labels. Review them against
# the current 80-product catalogue before using the numbers in a final report.
TEST_CASES = [
    {"query": "Something warm to wear in winter", "relevant_ids": {1, 2, 3, 5, 8, 33, 73}},
    {"query": "I need something for carrying my laptop", "relevant_ids": {12}},
    {"query": "Music without using cables", "relevant_ids": {10, 11}},
    {"query": "Protect my eyes from sunlight", "relevant_ids": {15}},
    {"query": "Something to sleep in outdoors during cold nights", "relevant_ids": {20, 25, 65}},
    {"query": "Keep my hands warm in freezing temperatures", "relevant_ids": {21, 34}},
    {"query": "Charge my phone while travelling", "relevant_ids": {24}},
    {"query": "Shoes for walking in snow", "relevant_ids": {8, 26, 27, 28}},
    {"query": "Something to keep me dry in rainy weather", "relevant_ids": {4, 31, 59, 60}},
    {"query": "Equipment for yoga and stretching at home", "relevant_ids": {18}},
    {"query": "A portable device to heat my room", "relevant_ids": {16}},
    {"query": "A reusable bottle that keeps drinks cold", "relevant_ids": {14}},
    {"query": "I need a laptop for programming", "relevant_ids": {36}},
    {"query": "Equipment for night trekking", "relevant_ids": {62, 63}},
    {"query": "Something to remove dust from floors and furniture", "relevant_ids": {55}},
    {"query": "A comfortable chair for sitting and studying", "relevant_ids": {46}},
    {"query": "A quick way to boil water for tea", "relevant_ids": {53}},
]


class TfidfSearch:
    """Traditional sparse retrieval baseline."""

    def __init__(self, products):
        self.products = products.reset_index(drop=True).copy()
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
        )
        self.product_vectors = self.vectorizer.fit_transform(
            self.products["search_text"].fillna("").astype(str)
        )

    def search(self, query, top_k=5):
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.product_vectors).ravel()
        indices = np.argsort(-scores, kind="stable")[:top_k]
        results = self.products.iloc[indices].copy()
        results["similarity_score"] = scores[indices]
        results["ranking_method"] = "tfidf"
        return results.reset_index(drop=True)


def calculate_metrics(results, relevant_ids, k=5):
    """Calculate binary Precision, Recall, HitRate, MRR, MAP and NDCG at K."""
    if not relevant_ids:
        raise ValueError("Each test case must have at least one relevant product ID.")
    if k < 1:
        raise ValueError("k must be a positive integer.")

    retrieved_ids = results["product_id"].astype(int).tolist()[:k]
    relevance = [1 if product_id in relevant_ids else 0 for product_id in retrieved_ids]
    relevant_found = sum(relevance)

    precision = relevant_found / k
    recall = relevant_found / len(relevant_ids)
    hit_rate = 1.0 if relevant_found else 0.0

    relevant_ranks = [rank for rank, is_relevant in enumerate(relevance, start=1) if is_relevant]
    mrr = 1.0 / relevant_ranks[0] if relevant_ranks else 0.0

    # Average Precision@K: average precision at each relevant rank.
    precision_sum = 0.0
    hits = 0
    for rank, is_relevant in enumerate(relevance, start=1):
        if is_relevant:
            hits += 1
            precision_sum += hits / rank
    map_at_k = precision_sum / min(len(relevant_ids), k)

    # NDCG@K with binary relevance grades (0 or 1).
    dcg = sum(
        rel / np.log2(rank + 1)
        for rank, rel in enumerate(relevance, start=1)
    )
    ideal_relevance = [1] * min(len(relevant_ids), k)
    idcg = sum(
        rel / np.log2(rank + 1)
        for rank, rel in enumerate(ideal_relevance, start=1)
    )
    ndcg = dcg / idcg if idcg else 0.0

    return {
        f"Precision@{k}": precision,
        f"Recall@{k}": recall,
        f"HitRate@{k}": hit_rate,
        f"MRR@{k}": mrr,
        f"MAP@{k}": map_at_k,
        f"NDCG@{k}": ndcg,
    }


def evaluate_method(name, search_function, test_cases, k=5):
    print("\n" + "=" * 78)
    print(f"EVALUATING: {name}")
    print("=" * 78)

    per_query_metrics = []
    for test in test_cases:
        query = test["query"]
        results = search_function(query, top_k=k)
        metrics = calculate_metrics(results, test["relevant_ids"], k)
        per_query_metrics.append(metrics)

        names = ", ".join(results["product_name"].astype(str).tolist())
        print(f"\nQuery: {query}")
        print(f"Retrieved: {names}")
        print(" | ".join(f"{key}={value:.3f}" for key, value in metrics.items()))

    summary = {
        metric: float(np.mean([row[metric] for row in per_query_metrics]))
        for metric in per_query_metrics[0]
    }
    print("\nAVERAGE")
    for metric, value in summary.items():
        print(f"{metric}: {value:.4f}")

    return {"Method": name, **summary}


def main():
    print("Starting FINDLY AI retrieval evaluation...")
    engine = build_search_engine()
    products = engine.products

    available_ids = set(products["product_id"].astype(int))
    for case in TEST_CASES:
        missing = case["relevant_ids"] - available_ids
        if missing:
            raise ValueError(
                f"Ground-truth IDs {sorted(missing)} for query "
                f"{case['query']!r} are not present in products.csv. "
                "Update TEST_CASES to match your catalogue."
            )

    tfidf_engine = TfidfSearch(products)
    reports = []

    reports.append(evaluate_method(
        "TF-IDF keyword search", tfidf_engine.search, TEST_CASES, K
    ))
    reports.append(evaluate_method(
        "Dense semantic search", engine.search_semantic, TEST_CASES, K
    ))
    reports.append(evaluate_method(
        "Hybrid search", engine.search, TEST_CASES, K
    ))

    print("\nCross-Encoder evaluation will download its model on first use.")
    try:
        candidate_k = min(len(products), max(30, K * 10))
        reports.append(evaluate_method(
            "Hybrid + Cross-Encoder reranking",
            lambda query, top_k=K: engine.search_reranked(
                query, top_k=top_k, candidate_k=candidate_k
            ),
            TEST_CASES,
            K,
        ))
    except Exception as exc:
        print("\nCross-Encoder evaluation was skipped:")
        print(f"{type(exc).__name__}: {exc}")
        print("Check internet access and the Cross-Encoder model download, then rerun.")

    comparison = pd.DataFrame(reports)
    print("\n" + "=" * 100)
    print("FINAL RETRIEVAL METHOD COMPARISON")
    print("=" * 100)
    print(comparison.to_string(index=False, float_format=lambda value: f"{value:.4f}"))

    output_path = "evaluation_comparison.csv"
    comparison.to_csv(output_path, index=False)
    print(f"\nSaved comparison to: {output_path}")
    print("Evaluation completed. Review manual relevance labels before reporting results.")


if __name__ == "__main__":
    main()
