# License and IP: the questions to settle before anything is public

This file lists questions. It gives no legal advice and decides nothing. The binding answers come from the
institute's technology-transfer office and, where needed, an attorney. The agent's job is to collect the facts
with their sources, show what is open, and keep every public step blocked until the author says the questions are
settled.

**Nothing is published (code host, model hub, package index, demo, data deposit) until these are answered.** A
permissive release cannot be taken back: "One can open up later, never close again."

A fillable copy is `assets/license_ip_checklist.md`.

## Ownership

1. Who owns the code, the weights and the data products? Employees' work often belongs to the employer; students,
   guests and contractors may differ. Several institutions may share ownership.
2. What does the institute's software and open-source policy require (approval, a notice to the technology-transfer
   office, a preferred license)? What is its response window?
3. Did a grant, a consortium agreement or an industry partner attach conditions to the results?

## Disclosure and patents

4. What has already been disclosed publicly (a public submission or preprint, talks, posters, a hosted demo used
   by outsiders)? Grace periods differ by jurisdiction: none in Europe, 12 months in the US. Get the current rule
   for each jurisdiction that matters from the office.
5. What would the code disclose that the paper does not? List it in `NOT_IN_PAPER.md` before deciding: training
   recipes, data processing, architectures tried. Code reveals more than the paper.
6. Is anything left that the institute may want to protect before disclosure (an invention disclosure first)?
7. Are there granted patents by others on the method family that could restrict use (freedom to operate)?

## Third-party terms

8. What licenses do the dependencies carry? Code under a non-commercial or copyleft license cannot be folded into
   a permissively licensed package.
9. What terms govern every training and evaluation dataset (commercial use, redistribution, attribution, consent and
   data-protection conditions)? Do the weights inherit any of them? Credit public datasets without naming a license
   until the license is confirmed.
10. Do any example files shipped with the package or the demo need their own license line (`data/SOURCES.md`)?

## Choosing licenses, per artifact

11. Code, weights, data products and documentation can carry different licenses. A permissive code license such as
    Apache-2.0 includes a patent grant to every user and cannot be withdrawn for a released version. Weights may be
    released under research-only or gated terms, or held back.
12. Which artifacts stay private (an internal checkpoint, outputs on in-house data)?
13. Until decided, the license is one open parameter in every brief and draft, with no sentence that promises free
    or commercial use.

## When decided

14. Set the license in every place it appears: LICENSE, the README line, the docs, the model card and its metadata,
    `pyproject.toml`, `CITATION.cff`, `THIRD_PARTY.md`.
15. Record who decided, on what date, with which office, in the project's decisions file.
