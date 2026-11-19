# Extracting activations from a frozen model

Every probe downstream trusts the vector it is given. In the source study three of the first bugs found by
running code were in extraction, and each one produced a plausible number. Map the model on a toy input before
any real item is embedded.

## The ten-minute map, before the first real item

Run on a toy input whose answer you know. The source study used
`sklearn.datasets.make_classification(n_samples=512, n_features=20, n_informative=6, n_classes=3, random_state=0)`
for tables; use the equivalent small, seeded input in your field (a few sentences, a handful of images).

1. **Print the module tree** and pick the candidate modules to read. Record each one's output shape on the toy
   input, for example `(members, context rows + query rows, d)`.
2. **Find the reserved positions.** CLS slots, padding, learned "thinking" rows, register tokens. In one model
   the column embedding carried 4 reserved CLS slots at `[:, :, :4]` with placeholders of about +-100; another
   prepended 64 learned rows before the context rows. Exclude them from pooling.
3. **Find which inputs reach which positions.** Feed two inputs that differ only in the query rows and compare
   the context-row tensors. In the source models they were bit-identical, which licenses pooling over
   `[:, :n_context]` and triggering the pass with a single dummy query.
4. **Find the label path.** Shuffle the labels and compare each candidate module (section "Label path").
5. **Count hook calls per forward pass.** Hooks fired once per normalization-method batch in one model;
   concatenate along the first dimension instead of keeping the last call.
6. **Measure invariances** (section "Invariances").
7. **Measure determinism and precision** (sections below).
8. **Time it** on the target hardware, warm and cold. Every `fit()` reloaded the checkpoint in one library (0.3
   to 0.7 s); a subclass that loads once per process removed it.

## The hook recipe

```python
def make_hook(store, name):
    def hook(module, inputs, output):  # must return None: a returned value replaces the module output
        out = output[0] if isinstance(output, (tuple, list)) else output
        store.setdefault(name, []).append(out.detach().clone().float().cpu())
    return hook

handles = [m.register_forward_hook(make_hook(store, n)) for n, m in modules.items()]
try:
    with torch.no_grad():
        model_call()
finally:
    for h in handles:
        h.remove()
```

`scripts/capture.py` packages this as a context manager (`with capture({"row": model.row_encoder}) as got:`)
and its `--selftest` shows both failures on a toy model whose forward pass writes into a submodule's output in
place: the un-cloned copy differs from the true output by 4.1 (max abs), and a hook that returns a value
changes the model's output by 0.79.

Why each part:

- **`.clone()`**: `detach()` shares storage. One model computed `R[:, :n] = R[:, :n] + label_embedding` on the
  tensor its row module had returned; another wrote CLS tokens into reserved slots of the column embedder's
  output. Before cloning, label-free row vectors showed a spurious 1.4% label effect.
- **returns None**: `register_forward_hook` replaces the output with any non-None return. A
  `lambda m, i, o: d.setdefault(k, o)` returns `o` (or an older stored tensor), which "silently corrupted the
  results in one of my tests".
- **`.float().cpu()`**: one dtype and one device in the store, so later arithmetic does not differ by backend.
- **`try/finally`**: a forgotten hook keeps firing on the next model call and appends vectors from a different
  item.
- **Residual streams**: when a layer's useful state is input plus output (a pre-norm transformer block), read
  `inputs[0] + output` in the hook, as one extraction did for its last layer.

## Label path

For each candidate module: embed with true labels, embed with labels shuffled by `content_shuffle`, compare.

```python
def content_shuffle(X, y, seed):
    """Shuffle labels with a permutation defined on row content, so the result is row-order invariant."""
    order = np.lexsort(np.nan_to_num(X, nan=-1e30).T[::-1])
    perm = np.random.default_rng(seed).permutation(len(y))
    out = np.empty_like(y)
    out[order] = y[order][perm]
    return out
```

Measured on the toy table (relative change ||z - z'|| / ||z||; read within one encoder only):

| Model family, stage | Label shuffle | 75% row subsample |
|---|---|---|
| label-aware in-context model, row stage | 0.53 | 0.09 |
| label-aware in-context model, column stage | 0.56 | 0.08 |
| label-free sibling, row stage | 0.000 | 0.03 |
| label-free sibling, column stage | 0.000 | 0.05 |
| label-free sibling, prediction stage | 1.08 | 0.07 |
| set encoder trained on "same dataset?" | 0.001 | 0.004 |

The label-free sibling is exact zero up to the prediction stage, which makes it the negative control. A library
call documented as returning per-row embeddings read each row's own target token for training rows, so its
"train" embeddings contained their labels; read the source, not the docstring.

## Invariances

Test every invariance the pooling assumes, with a tolerance taken from the measurement:

- **Row (or token) order.** Pooled relative difference 4.5e-7 in one model, 1e-7 in two others, 1e-3 in a
  fourth. Tests use a tolerance (1e-3 in the source study), never exact equality.
- **Column (or channel) order.** Not invariant: 0.18 with one ensemble member, 0.09 with four. Average over
  members or explicit permutations, and record how many.
- **Batch composition.** Embed one item alone and inside a batch; batch-norm or padding can leak.

## Determinism

- Same seed, repeated calls, fresh process: bitwise identical, or the size of the difference is logged.
- One model needed an explicitly seeded `generator` to be deterministic.
- A generator that iterated over a Python `set` depended on `PYTHONHASHSEED`; sorting the iteration fixed it.
  When an encoder or data generator is not deterministic across processes, check hash-order dependence first.
- Parallelize across items in your own pool, never inside the model or generator: worker processes crashed or
  deadlocked, and forked workers inherit identical random state.

## Precision and device

| Comparison | Size of the difference |
|---|---|
| mixed precision against fp32, pooled vector, same device | about 2e-3 |
| mixed precision against fp32, predicted probabilities | about 4e-3 |
| fp32 on GPU-like backend against fp32 on CPU | 9e-7 |
| fp32 with mixed precision off, CPU workers against GPU workers | identical to 1e-6 |

- Turn mixed precision off for any vector that will be compared or pooled across machines.
- Use one device per comparison, or measure agreement between devices on a few items before sharing a store
  (`capture.compare` returns max absolute and relative difference). A later project found encodes on two GPU card
  types differed by 0.04 to 0.075, so it used one hardware type per comparison row.
- Pass the device explicitly; automatic selection chose a backend the rest of the pipeline did not expect.
- Some backends reject float64 input ("Cannot convert a ... Tensor to float64"); cast to float32 once.

## Per-view metadata

Write one record per view, the first time it is encoded, and keep it beside the vectors:

```
view: <name>
checkpoint: <file name and version or hash>
module: <dotted path>, input + output if residual
pooling: mean and std over context rows, mean over <k> members or permutations
excluded: <reserved slots, query rows>
input copy: <raw or the model's own preprocessing>, targets <raw or binned>
device, precision: <cpu, fp32, mixed precision off>
seeds: <encoder seed, shuffle seeds>
```

Per-view metadata is written per view: one shared metadata call once overwrote another view's feature groups.

## Running encoders at scale

- Fail softly: a failed item is stored as a NaN row flagged as failed, with a log line, and a retry flag
  recomputes only those.
- Resume: skip items already present in every view; flush every 10 to 50 items.
- Share one store across workers with atomic claim files (`O_CREAT | O_EXCL`), not static shards (a static
  split left the fast worker idle).
- Encode once per model, then pool for every probe and figure; re-encoding per analysis cost about 14x.
