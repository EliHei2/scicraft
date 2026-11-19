# Chat export: workshop abstract

**User (turn 1):** write me a workshop abstract for our retrieval benchmark paper, 150 words max

**Assistant (turn 2):**
In today's fast-moving landscape of retrieval-augmented generation, robust evaluation is more crucial than ever. We present RetroBench, a comprehensive and novel benchmark that seamlessly unifies ten datasets — spanning law, medicine and code — into a single powerful evaluation suite. Our extensive experiments reveal that current retrievers struggle significantly, paving the way for future research.

**User (turn 3):** no, way too much. here is mine:
Retrieval-augmented models are evaluated on datasets that share their training distribution, so reported gains say little about new domains. We collect ten retrieval datasets from law, medicine and source code that no public retriever was trained on and score eleven retrievers on them with one protocol. Dense retrievers lose a third of their in-domain recall on average, while BM25 loses a tenth.

**Assistant (turn 4):** Thanks, that reads much better. Want me to tighten it?

**User (turn 5):** ok final from me, I added the last part:
Retrieval-augmented models are evaluated on datasets that share their training distribution, so reported gains say little about new domains. We collect ten retrieval datasets from law, medicine and source code that no public retriever was trained on and score eleven retrievers on them with one protocol. Dense retrievers lose a third of their in-domain recall on average, while BM25 looses a tenth. The gap closes when the dense retriever is given 500 in-domain query-document pairs for fine-tuning, which recovers most of the lost recall on every domain we tested. The ranking of retrievers by in-domain recall does not predict their ranking out of domain. We think this is an important finding for the comunity. The benchmark, the protocol and all retriever outputs are released.
