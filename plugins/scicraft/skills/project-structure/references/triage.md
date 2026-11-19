# Triage of a cluttered root

The case this comes from: a project root with about 50 result folders (36 or more timestamped runs of one benchmark,
smoke, schema, style and submit tests, numbered temporary checks, compatibility shims, superseded iterations, a
"final" folder from early on), numbered zips of one repository, a 65 GB tarball, a 2.8 GB table, LaTeX build files
and three virtual environments. A triage document sorted every folder before anything moved.

## Steps

1. **List.** `python3 <skill>/scripts/triage.py <root> --out docs/FOLDER_TRIAGE.md`. It gives size, file count,
   last change and a suggested class for every top-level entry. On a very large tree add `--no-size` first, then
   measure the few big folders with `du -sh`.
2. **Find the live chain.** Which folder feeds the current deliverable? Read the scripts that build it. The table
   marks every entry whose name appears in code under `scripts/ src/ code/ configs/ experiments/ notebooks/
   workflow/` as `KEEP?` with the file that names it (`--refs` changes the folders). A path built at run time from
   parts will not be found this way: read the builder. Mark the chain `KEEP`.
3. **Classify every row** with the owner. Classes used in the real triage:

   | Class | Holds | Before acting |
   |---|---|---|
   | KEEP | the canonical lineage, the freshest external bundle, raw inputs | nothing; move into the new tree if one is made |
   | ARCHIVE | superseded but worth keeping: older bundles, early "final" folders, collaborator copies | `archive.py` to `archived/<date>_<reason>/` with a reason |
   | DELETE | smoke and check folders, empty stubs, compatibility shims, superseded iterations that are fully regenerable | confirm nothing reads them (`grep`), then the owner's yes |
   | OUT OF SCOPE | material for another deliverable | leave, and name its owner |
   | VERIFY FIRST | giant archives and tables that may mirror raw inputs | find the authoritative copy and compare by checksum |

4. **Do not trust dates or names alone.** The folder called "final" was an early one; the newest timestamp may be a
   failed run. The script's `KEEP?` on the newest sibling is a hint.
5. **Act in this order:** archive, then verify duplicates, then delete. `archive.py` prints a plan without
   `--apply`. For a full disk, `--symlink` leaves links so existing paths still work.
6. **Delete only verified duplicates.** Match by size, then by streamed checksum:

   ```bash
   shasum -a 256 big_dump.tar.gz /archive/copy/big_dump.tar.gz
   cmp -s a b && echo identical
   ```

   Ask before deleting anything large. Never delete unpublished data in a tidy-up, and never delete a result because
   it disagrees with the current one: archive it with its reason.
7. **Leave a rule behind.** Add the canonical-lineage rule to the index file and a `RUN_MAP.md` so the sprawl does not
   come back. The triage document stays in `docs/` as the record of what was moved where.

## When a new repository is the better answer

If the root cannot be sorted in place (the canonical chain is spread over many folders, history is full of data),
build a fresh repository with the scaffold, copy in only the live chain with provenance rows, and leave the old root
as read-only. This is how the benchmark rebuild ended: one canonical sweep root plus one freshest external bundle,
"everything else archives or deletes."
