# Proving a reimplemented encoder

A port of a published encoder (to another framework, without a heavy dependency, or to read released weights)
is a claim that it computes the same function. The proof is a match to the authors' own outputs under the
authors' own protocol.

## Procedure

1. **Treat the code as ground truth.** When the paper and the released code differ, the code produced the
   released weights and the published numbers. Follow it.
2. **Write the paper-against-code table** before porting. One row per item, file and line cited, commit pinned:

   | Item | Paper | Code (released weights) |
   |---|---|---|
   | parameters | 45,424 | 75,072 |
   | output dimension | 64 | 32 |
   | network blocks | [as written] | [as implemented] |
   | subsampler, negative pairs, loss weight | [as written] | [as implemented] |

   These first two rows are from a real port; the paper also differed from the code in the network
   blocks, the subsampler, the negative pair and the loss weight.
3. **Load the released weights without the original framework if needed**, and count them: the port loaded
   75,072 of 75,072 parameters. A partial load that runs is the most common silent failure.
4. **Find released intermediate outputs**: published embedding files, result CSVs, logged vectors. One repository
   shipped per-dataset embeddings for a fixed split, min-max normalized per dimension.
5. **Reproduce the exact protocol** that produced them: the same items (63 datasets whose files the repository
   included), the same subsampling (160 subsamples from each dataset's train fold and 160 from its validation
   fold, each 256 rows x 16 features x 3 targets, then averaged), the same normalization.
6. **Compare** with `probes.py parity`:

   ```bash
   python3 scripts/probes.py parity --ours ours.npy --theirs published.npy --minmax --threshold 0.9999
   ```

   It reports the minimum per-dimension Pearson r (and which dimension), the Spearman correlation of all
   pairwise distances, the number of constant dimensions and the largest absolute difference, and exits 1 below
   the threshold. The real port reached 1.0000 on both.
7. **Re-run from the documented snippet.** Copy the code block out of the notes or README into a fresh
   environment and run it; the documented block gave r = 1.0000 on 12 datasets. The scratch file that first
   matched is not the artifact users get.
8. **Port small numeric functions with a tolerance test.** A numpy copy of a library's preprocessing matched the
   torch functions to 4.8e-7, tested at 1e-4.

## Reproducing a configuration, not only code

When the encoder or a data generator is the object of study, reproduce the configuration that produced the
artifact you compare against, and diff defaults across versions. One library release silently changed a default
so that generated tables had nearly independent features (mean |r| 0.025 against 0.12 before), without a
changelog line; another default allowed tables whose target was independent of the inputs. Read the authors'
training scripts at a pinned commit, pass every flag explicitly, and label outputs with any caveat ("port not
experimentally verified").

## Names

- **Label each component**: exact reproduction, approximate reproduction, or new extension. Keep the label in the
  status table and in captions.
- **Never give a substitute the original's name.** A fallback encoder is not called by the original's name. A
  public package with the original's name that was not faithful was recorded as "Not faithful; do not call it"
  by that name.

## Licenses and redistribution

| Situation | What to do |
|---|---|
| code under an open license | port, keep the notice, record it in THIRD_PARTY.md |
| code with no license | "port the ideas and do not copy the code"; write it fresh and say so |
| weights under a non-commercial license | download at run time, never redistribute, state the license where the encoder is used |
| weights behind a gate (accepted license, token) | document the gate; headless runs need the token set in the environment, read from a file the user keeps |
| weight host gone | record it with the date; the encoder is unavailable, not "failed" |

## Before calling it done

- [ ] parameter count matches
- [ ] min per-dimension r and distance Spearman at or above 0.9999 on the authors' outputs
- [ ] re-run from the documented snippet in a fresh environment
- [ ] paper-against-code table written
- [ ] component labeled exact, approximate or extension
- [ ] license of code and weights recorded
