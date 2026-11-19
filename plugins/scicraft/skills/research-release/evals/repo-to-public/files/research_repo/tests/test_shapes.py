import numpy as np
from fieldnet import embed

def test_shape():
    assert embed(np.ones((5, 3)) + np.arange(3)).shape == (5, 8)
