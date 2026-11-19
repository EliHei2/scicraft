import glob
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD

files = sorted(glob.glob("/data/clicks/part-*.parquet"))   # 1,800 shards, ~900M rows
df = pd.concat([pd.read_parquet(f) for f in files])
df = df[~df.is_bot]
mat = df.pivot_table(index="user_id", columns="item_id", values="ts", aggfunc="count", fill_value=0)
item_corr = np.corrcoef(mat.values.T)          # used later for item-item neighbours
svd = TruncatedSVD(n_components=128).fit(mat.values)
np.save("user_factors.npy", svd.transform(mat.values))
np.save("item_corr.npy", item_corr)
