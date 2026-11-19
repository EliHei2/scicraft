---
type: llm
focus: trace
weight: 1
---

The col_embedder pooling excludes the 4 reserved CLS slots (or the answer explicitly explains that including them makes the vector partly encode the column count and decides deliberately).
