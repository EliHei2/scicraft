"""Evaluate retrieval models on the held-out test pairs (100,000 query-document pairs)."""
import numpy as np

MODELS = ["ours", "baseline_bm25_dense", "baseline_e5_like", "baseline_contriever_like"]
N_SUB = 2000

rng = np.random.default_rng(0)


def load_pairs(model):
    """Returns query and document embeddings of the test pairs for one model (row i of q pairs with row i of d)."""
    q = np.load(f"emb/{model}_queries.npy")
    d = np.load(f"emb/{model}_docs.npy")
    return q, d


def alignment(q, d):
    """Mean cosine similarity between each query and its own paired document."""
    qn = q / np.linalg.norm(q, axis=1, keepdims=True)
    dn = d / np.linalg.norm(d, axis=1, keepdims=True)
    return float((qn * dn).sum(1).mean())


def recall_at_10(q, d):
    qn = q / np.linalg.norm(q, axis=1, keepdims=True)
    dn = d / np.linalg.norm(d, axis=1, keepdims=True)
    sims = qn @ dn.T
    top = np.argsort(-sims, axis=1)[:, :10]
    return float(np.mean([i in top[i] for i in range(len(q))]))


if __name__ == "__main__":
    for m in MODELS:
        q, d = load_pairs(m)
        idx = rng.choice(len(q), N_SUB, replace=False)   # subsample for speed
        print(m, "alignment", alignment(q[idx], d[idx]), "recall@10", recall_at_10(q[idx], d[idx]))
