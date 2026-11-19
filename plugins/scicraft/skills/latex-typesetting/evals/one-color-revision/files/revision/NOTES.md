Notes from our call (third round of the revision):

- reviewer 3 wants runtime. add after the results table: "Retrieval adds 4.1 ms per query on one GPU, against 2.7 ms for the encoder alone."
- and a new table with it: rows "Encoder alone" 2.7 ms and "Encoder + retrieval" 4.1 ms, column "Latency per query (ms)". caption: "Latency per query on one GPU. Mean over 1,000 queries."
- cite LeCun 1998 for the convolution baseline we mention in the same sentence? -> actually just add the citation after "encoder alone" (lecun1998gradient is in refs.bib)
