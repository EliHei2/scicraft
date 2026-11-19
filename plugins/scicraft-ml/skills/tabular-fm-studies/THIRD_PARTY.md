# Third-party material in this skill

| Piece | Where | Source | License |
|---|---|---|---|
| `patch_v2_hash_order` (a copy of `RandomDataset.sample` from tabicl 2.2.0 with one line changed to `sorted(...)`) | `scripts/sample_prior.py` | tabicl 2.2.0, `tabicl/prior/graph_lib/_dataset.py` | BSD 3-Clause, notice below |
| numpy ports of `outlier_removing` and `standard_scaling` | `scripts/canonical_table.py` | tabicl 2.2.0, `tabicl/prior/_reg2cls.py` | BSD 3-Clause, notice below |
| quoted signatures, defaults and short source excerpts of tabicl | `references/prior-sampling.md`, `references/model-interfaces.md` | tabicl 2.2.0 | BSD 3-Clause, notice below |
| PyTorch re-implementation of the Dataset2Vec architecture and subsampler, written from the released TF2 code | `scripts/d2v_embed.py` | github.com/hadijomaa/dataset2vec (Jomaa, Schmidt-Thieme, Grabocka, Data Min. Knowl. Disc. 35, 2021) | the original repository is CC-BY-NC-4.0; the weights are downloaded at run time and never shipped; use is non-commercial research with attribution |
| hook recipes for TabDPT and TabPFN | `scripts/dataset_vectors.py` | tabdpt 1.3.1 (Apache-2.0), tabpfn 9.1.0 (Apache-2.0 code) | calls public APIs; no code copied |
| URLs and column names of TabArena result files | `scripts/published_results.py` | TabArena (autogluon/tabarena) | facts; files are downloaded at run time |
| dataset names, row counts and task types of TabArena-v0.1 and BeyondArena | `evals/pool-two-suites/files/` | OpenML study 457 and the TabArena/BeyondArena Hugging Face metadata | public metadata, no data rows |
| short quotations from papers, README files and pull requests | references | as cited in place | quotation with attribution |

The "Mind the Gap?" code (github.com/alexodavies/TabDistances) has no license file; its feature definitions are
described in `references/preprocessing-and-metafeatures.md` and no code from it is included.

## tabicl notice

<!-- voice-lint: off -->
```
BSD 3-Clause License

Copyright (c) 2025, Soda team @ Inria

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```
<!-- voice-lint: on -->
