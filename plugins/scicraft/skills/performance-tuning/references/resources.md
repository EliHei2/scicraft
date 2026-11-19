# Honest resource requests

How much GPU memory, host memory, cores and time to ask for, read from measurement. Scheduler commands and queue
policy are in the `cluster-jobs` skill.

## Measure, then request

1. Run one representative unit of work (one split, one sample, 2,000 steps of the densest data) on one GPU under
   `run_meter.py`, or with `RunMeter` / `Instrument` inside the code.
2. Read peak VRAM from `torch.cuda.max_memory_allocated` (and the nvidia-smi sample, which also sees other
   allocators such as a RAPIDS pool), peak RAM from the process tree, and wall time.
3. Request the measured peak times a modest margin. "some margin is good, but that's too much!"
4. Record which card it ran on. Numbers move between card types.

With a measured peak of 4.3 GB, a request of about 10.7 GB fit many more common GPUs than top ones.
The smallest card that fits is the one that schedules fastest.

## Mistakes in the record

| Mistake | What was true | Rule |
|---|---|---|
| "20M rows need 25 GB" of VRAM, so the largest cards were requested | the 25 GB was the scheduler's host-RAM figure; VRAM was flat at 8 to 10 GB from 13M to 52M rows | read VRAM from the framework, never the scheduler |
| VRAM assumed linear in input size (an older note) | measured flat in that pipeline | measure the curve; the newer measurement wins |
| reserved VRAM (8.3 to 10.2 GB) used as the footprint | live peak 4.3 GB | size on allocated, not reserved |
| failures blamed on OOM | 36 of 36 failures were a library bug on one GPU model; two runs of nearly equal size had opposite outcomes | tabulate failures by card, node and size before naming a cause |
| memory hard-coded into job scripts | the queue for big cards was clogged | every resource is an explicit override, no default |
| 10 GPUs and exclusive mode requested without a reason | single-GPU jobs started in minutes | justify every flag |
| a job routed to a CPU queue for a GPU forward pass | about 10x slower | match each step to the hardware it needs |

## Extrapolating a tool you cannot instrument

Calibrate on a crop (20M items in the record), then estimate the full input as
`mem_full = peak_crop x (N / N_crop) x 1.3`, and check the estimate against a table of measured runs of that
tool, "rather than trusting either one alone".

## Parallel splits

- More, smaller jobs in parallel beat one large serial job when the work splits: about 7 to 8 h on 4 GPUs against
  13.3 h on 1.
- Balance splits by the count that drives cost (items), not by a label count: one label can be several percent
  of all items.
- When queues are busy, submit a spread of sizes (for example 5, 10, 20, 40 and 80 splits, on small and large
  cards), each writing to its own output folder, and keep whichever finishes.
- The wall time of a batch of parallel jobs is the slowest job, not the sum. `cost_table.py` prints it that way.

## Laptop and login nodes

Heavy code does not run on the laptop ("computer crashed last time because of the beig analysis"). Check free
memory before a large local job, run one region at a time, and send anything that needs a GPU or many gigabytes
to the cluster. Training never runs on CPU unless the author opts in explicitly; gate it behind a GPU check.

## Projections

Cross-check every projection of time, cost or memory by a second, independently derived route before reporting
it. One unit slip made a table 3 to 4x too optimistic; another used the throughput of the small model for the
large one and projected 39 days where the truth was about 147.

## Stating the envelope

Report the hardware envelope with any timing claim (for example single GPU, one CPU, [RAM], [time limit]),
and report where competing methods exceeded it. A timing claim covers only the methods that were timed, and its
wording is scoped to them.
