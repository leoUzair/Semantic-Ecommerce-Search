"""Hybrid semantic search with optional Cross-Encoder re-ranking."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from .data_loader import load_products
    from .preprocess import prepare_search_text
except ImportError:
    from data_loader import load_products
    from preprocess import prepare_search_text


# First-stage bi-encoder: fast, independently encodes queries and products.
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Second-stage cross-encoder: jointly scores each (query, product) pair.
CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"


class SemanticSearchEngine:
    """Build dense and sparse indexes, then retrieve and optionally rerank."""

    def __init__(self, products: pd.DataFrame, model_name: str = MODEL_NAME):
        self.products = products.reset_index(drop=True).copy()
        if "search_text" not in self.products.columns:
            raise ValueError("Products must contain a 'search_text' column.")
        if self.products.empty:
            raise ValueError("The product catalogue is empty.")

        product_texts = self.products["search_text"].fillna("").astype(str).tolist()

        print("\nLoading sentence embedding model...")
        self.model = SentenceTransformer(model_name)

        print("\nGenerating product embeddings...")
        self.product_embeddings = self.model.encode_document(
            product_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        print("Product embeddings generated!")
        print("Embedding shape:", self.product_embeddings.shape)

        print("\nBuilding TF-IDF keyword index...")
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
        )
        self.product_tfidf = self.vectorizer.fit_transform(product_texts)
        print("TF-IDF index ready!")

        # Loaded only when search_reranked() is first used.
        self._cross_encoder = None

    @staticmethod
    def _validate_query_and_k(query: str, top_k: int) -> str:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Please enter a valid search query.")
        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")
        return query.strip()

    def _calculate_base_scores(self, query: str):
        """Calculate dense semantic and sparse TF-IDF scores for all items."""
        query_embedding = self.model.encode_query(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        semantic_scores = cosine_similarity(
            query_embedding, self.product_embeddings
        )[0]

        query_vector = self.vectorizer.transform([query])
        keyword_scores = cosine_similarity(
            query_vector, self.product_tfidf
        )[0]

        hybrid_scores = 0.75 * semantic_scores + 0.25 * keyword_scores
        return semantic_scores, keyword_scores, hybrid_scores

    def search_semantic(self, query: str, top_k: int = 5) -> pd.DataFrame:
        """First-stage dense retrieval only (useful for evaluation)."""
        query = self._validate_query_and_k(query, top_k)
        semantic_scores, keyword_scores, _ = self._calculate_base_scores(query)

        results = self.products.copy()
        results["semantic_score"] = semantic_scores
        results["keyword_score"] = keyword_scores
        results["similarity_score"] = semantic_scores
        results["ranking_method"] = "semantic"
        return results.sort_values(
            "similarity_score", ascending=False, kind="stable"
        ).head(top_k).reset_index(drop=True)

    def search(self, query: str, top_k: int = 5) -> pd.DataFrame:
        """Hybrid retrieval: 75% semantic score + 25% TF-IDF score."""
        query = self._validate_query_and_k(query, top_k)
        semantic_scores, keyword_scores, hybrid_scores = self._calculate_base_scores(query)

        results = self.products.copy()
        results["semantic_score"] = semantic_scores
        results["keyword_score"] = keyword_scores
        results["similarity_score"] = hybrid_scores
        results["ranking_method"] = "hybrid"
        return results.sort_values(
            "similarity_score", ascending=False, kind="stable"
        ).head(top_k).reset_index(drop=True)

    def _get_cross_encoder(self):
        """Lazy-load the cross-encoder only when re-ranking is requested."""
        if self._cross_encoder is None:
            from sentence_transformers import CrossEncoder

            print("\nLoading Cross-Encoder re-ranker...")
            self._cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL_NAME)
            print("Cross-Encoder ready!")
        return self._cross_encoder

    def search_reranked(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = 30,
        batch_size: int = 16,
    ) -> pd.DataFrame:
        """Retrieve candidates with hybrid search, then rerank query/product pairs.

        The MS MARCO Cross-Encoder returns ranking logits. They are used only
        to order candidates; they are not probabilities or calibrated confidence.
        """
        query = self._validate_query_and_k(query, top_k)
        if not isinstance(candidate_k, int) or candidate_k < 1:
            raise ValueError("candidate_k must be a positive integer.")
        if not isinstance(batch_size, int) or batch_size < 1:
            raise ValueError("batch_size must be a positive integer.")

        candidate_count = min(len(self.products), max(candidate_k, top_k))
        candidates = self.search(query, top_k=candidate_count).copy()

        reranker = self._get_cross_encoder()
        documents = candidates["search_text"].fillna("").astype(str).tolist()
        pairs = [(query, document) for document in documents]

        raw_scores = reranker.predict(
            pairs,
            batch_size=batch_size,
            show_progress_bar=False,
        )
        rerank_scores = np.asarray(raw_scores).reshape(-1)
        if len(rerank_scores) != len(candidates):
            raise RuntimeError(
                "Cross-Encoder returned a different number of scores "
                "than candidate products."
            )

        candidates["rerank_score"] = rerank_scores
        candidates["retrieval_rank"] = np.arange(1, len(candidates) + 1)
        candidates["ranking_method"] = "hybrid+cross-encoder"

        return candidates.sort_values(
            "rerank_score", ascending=False, kind="stable"
        ).head(top_k).reset_index(drop=True)


def build_search_engine() -> SemanticSearchEngine:
    """Load, preprocess, and index the configured product catalogue."""
    products = load_products()
    processed_products = prepare_search_text(products)
    return SemanticSearchEngine(processed_products)


if __name__ == "__main__":
    engine = build_search_engine()
    print("\nFINDLY AI – Hybrid E-Commerce Search")
    print("Enter 'exit' to close. Add ':rerank' to use Cross-Encoder reranking.")

    while True:
        raw_query = input("\nSearch: ").strip()
        if raw_query.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if not raw_query:
            print("Please enter a query.")
            continue

        use_reranker = raw_query.lower().endswith(":rerank")
        query = raw_query[:-7].strip() if use_reranker else raw_query
        results = (
            engine.search_reranked(query, top_k=5, candidate_k=len(engine.products))
            if use_reranker
            else engine.search(query, top_k=5)
        )

        print("\nTop results:")
        for rank, (_, row) in enumerate(results.iterrows(), start=1):
            print(
                f"{rank}. {row['product_name']} | {row['category']} | "
                f"₹{row['price']} | Hybrid: {row['similarity_score']:.4f}"
            )
            if "rerank_score" in row.index:
                print(f"   Cross-Encoder logit: {row['rerank_score']:.4f}")
