"""Test template for research code: shapes, determinism, tiny golden values, joins, defaults.

Copy into the project's tests/ folder, replace the two stand-in functions under [REPLACE] with imports
from the package, and adapt the expected values. Runs on CPU in well under a minute with numpy and pytest.

Each test is named as the claim it checks. A test counts only if it fails without the fix it guards:
after writing one, break the code on purpose (flip a sign, drop the sort, join by position) and watch it
go red before keeping it.
"""
import numpy as np
import pytest

# [REPLACE] with: from yourpkg.module import score_rows, attach_labels
# The stand-ins below make the template run as shipped.


def score_rows(x: np.ndarray, w: np.ndarray, min_score=None, seed: int = 0):
    """Stand-in: (N, D) @ (D,) -> scores (N,) and a keep flag (N,). Rows are never dropped."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(scale=1e-3, size=x.shape[0])  # a seeded random source, so determinism is testable
    s = x @ w + noise  # (N,)
    keep = np.ones_like(s, dtype=bool) if min_score is None else s >= min_score
    return s, keep


def attach_labels(raw_ids: np.ndarray, qv: np.ndarray, label_ids: np.ndarray, labels: np.ndarray, min_qv=20):
    """Stand-in: filter raw rows by quality, then attach labels by a stable key (never by position)."""
    row_index = np.arange(raw_ids.shape[0])  # assigned on the raw table, before any filter
    kept = row_index[qv >= min_qv]
    lookup = dict(zip(label_ids.tolist(), labels.tolist()))
    return kept, np.array([lookup.get(int(raw_ids[i]), -1) for i in kept])


# ---------------------------------------------------------------------------------------------------
# 1. Shapes and dtypes
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("n,d", [(1, 3), (7, 3), (64, 16)])
def test_scores_have_one_value_and_one_flag_per_row(n, d):
    x = np.ones((n, d), dtype=np.float32)
    s, keep = score_rows(x, np.ones(d, dtype=np.float32))
    assert s.shape == (n,)
    assert keep.shape == (n,) and keep.dtype == bool


def test_empty_input_returns_empty_output_with_the_same_schema():
    s, keep = score_rows(np.zeros((0, 3)), np.ones(3))
    assert s.shape == (0,) and keep.shape == (0,)


# ---------------------------------------------------------------------------------------------------
# 2. Determinism: same seed, same bytes; different seed, different draw
# ---------------------------------------------------------------------------------------------------
def test_same_seed_gives_identical_output():
    x = np.random.default_rng(1).normal(size=(50, 4))
    w = np.arange(4.0)
    a, _ = score_rows(x, w, seed=0)
    b, _ = score_rows(x, w, seed=0)
    assert np.array_equal(a, b)


def test_seed_reaches_the_random_source():
    x = np.random.default_rng(1).normal(size=(50, 4))
    a, _ = score_rows(x, np.arange(4.0), seed=0)
    b, _ = score_rows(x, np.arange(4.0), seed=1)
    assert not np.array_equal(a, b)  # a seed that changes nothing is a seed that is not wired in


# ---------------------------------------------------------------------------------------------------
# 3. Tiny golden values: computed once by hand or by the trusted version, committed as literals
# ---------------------------------------------------------------------------------------------------
def test_scores_match_hand_computed_values():
    x = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    w = np.array([2.0, -1.0])
    s, _ = score_rows(x, w)
    np.testing.assert_allclose(s, [2.0, -1.0, 1.0], atol=1e-2)  # tolerance covers the 1e-3 seeded noise


# ---------------------------------------------------------------------------------------------------
# 4. New options default to the old behavior
# ---------------------------------------------------------------------------------------------------
def test_default_keeps_every_row_like_the_version_before_the_option():
    x = np.random.default_rng(2).normal(size=(20, 3))
    s_default, keep = score_rows(x, np.ones(3))
    assert keep.all()
    s_explicit, _ = score_rows(x, np.ones(3), min_score=-np.inf)
    assert np.array_equal(s_default, s_explicit)


def test_threshold_flags_rows_and_drops_none():
    x = np.array([[1.0], [-1.0], [3.0]])
    s, keep = score_rows(x, np.array([1.0]), min_score=0.5)
    assert s.shape == (3,)  # the raw output keeps every row
    assert keep.tolist() == [True, False, True]


# ---------------------------------------------------------------------------------------------------
# 5. Joins: a stable key, with filtered rows interleaved so raw and filtered positions differ
# ---------------------------------------------------------------------------------------------------
def test_labels_land_on_their_own_rows_when_low_quality_rows_are_interleaved():
    raw_ids = np.array([10, 11, 12, 13, 14, 15])
    qv = np.array([30, 5, 30, 5, 30, 30])  # rows 1 and 3 are filtered out
    label_ids = np.array([15, 14, 12, 10])  # shuffled on purpose
    labels = np.array([5, 4, 2, 0])
    kept, got = attach_labels(raw_ids, qv, label_ids, labels)
    assert kept.tolist() == [0, 2, 4, 5]  # indices into the raw table, assigned before the filter
    assert got.tolist() == [0, 2, 4, 5]  # label i belongs to raw id 10 + i
    assert len(set(kept.tolist())) == len(kept)  # exactly one output row per kept input row


def test_no_output_row_points_at_a_filtered_input_row():
    raw_ids = np.arange(100)
    qv = np.where(np.arange(100) % 3 == 0, 5, 30)
    kept, _ = attach_labels(raw_ids, qv, raw_ids, raw_ids)
    assert int((qv[kept] < 20).sum()) == 0  # an exact invariant, never a ratio bound
