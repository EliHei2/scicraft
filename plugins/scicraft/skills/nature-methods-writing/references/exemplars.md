# Exemplar papers and governing documents

Read the Methods of the paper that matches the job before drafting. Each one is a template for one thing. All are
published and public. They are biology and computational-biology method papers, because that is where the author
wrote for Nature journals; the structural lessons transfer to any method paper.

| Paper | Template for | Where |
|---|---|---|
| BIDCell (Nat Commun 2024), deep-learning cell segmentation | the cleanest method-data split; several losses with the total objective as one weighted sum; per-dataset preprocessing as items (i) to (v); a separate reference-mapping subsection; a "Settings used for other methods" subsection; a pinned commit hash | https://www.nature.com/articles/s41467-023-44560-w and https://pmc.ncbi.nlm.nih.gov/articles/PMC10787788/ |
| scVI (Nat Methods 2018), deep generative model for single-cell data | the canonical order: model, inference, downstream tasks, "Modeling choices", datasets, statistics, evaluation, availability; equations once with cross-references to the Notes; code-named datasets; "only three dataset-specific hyperparameters" | https://escholarship.org/uc/item/5777r2c7 |
| Xenium benchmarking study (Nat Methods 2025) | many datasets by many tools by many analyses: one subsection per benchmarking task, data processed once and reused, explicit per-analysis deltas and reasons for each subset | https://pmc.ncbi.nlm.nih.gov/articles/PMC11978515/ |
| Cellpose 3 (Nat Methods 2025) | the economy of deep-learning Methods: architecture in one sentence, each loss in one sentence, hyperparameters as short declaratives, seeds in captions | https://pmc.ncbi.nlm.nih.gov/articles/PMC11903308/ |
| SCimilarity (Nature 2024/25) | multi-task metric-learning losses (triplet plus reconstruction), each named with one purpose clause and a combined-loss equation; layered availability (package, container, repository, separate DOIs for weights and data) | https://pmc.ncbi.nlm.nih.gov/articles/PMC11864978/ |
| ResolVI (bioRxiv 2025) | method as delta: one shared downstream recipe with per-dataset deltas. Also a counter-example: missing version pins, seeds and formal availability | https://www.biorxiv.org/content/10.1101/2025.01.20.634005v1.full |
| ComSeg (Commun Biol 2024), graph-based segmentation | an algorithm "decomposed into five steps"; an explicit "the only hyper-parameters exposed to the user are"; per-tissue reference subsections; metric equations inline | https://pmc.ncbi.nlm.nih.gov/articles/PMC11227573/ |
| SpatialData (Nat Methods 2025) | version pinning inline for every tool ("(v.1.9)"); well-scoped Notes that keep Methods focused; the code license named | https://pmc.ncbi.nlm.nih.gov/articles/PMC11725494/ |

## Governing documents

- Nature formatting guide: https://www.nature.com/nature/for-authors/formatting-guide
- Nature Portfolio reporting standards: https://www.nature.com/nature-portfolio/editorial-policies/reporting-standards
- Code and software submission guidelines: https://www.nature.com/documents/GuidelinesCodePublication.pdf
- Data availability statement templates: https://www.springernature.com/gp/authors/research-data-policy/data-availability-statements/12330880
- Ten Simple Rules for Reproducible Computational Research (PLOS Comput Biol): https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285

The URLs were collected when the skill was first written and were not re-opened for this version.
