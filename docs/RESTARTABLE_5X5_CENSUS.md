# Durable exact occupancy checkpoints for 5×5 Quixo

The external-memory D4 census can stop at a **completed occupancy**
and continue without replaying previous occupancy strata. A snapshot
contains every (X-count,O-count) tier's already-discovered canonical
visited bitmap for the **next** occupancy, plus the exact running
raw, orbit, terminal, win-in-one, and unique-win-in-one totals.

## Example: two intentional interruptions

```sh
c++ -O3 -std=c++17 -Wall -Wextra -pedantic \
  tools/census5_dual_tier_external.cpp -o /tmp/qf-resume
mkdir -p /scratch/quixo/checkpoints

# cap=11 is unchanged across all commands. k=8 closes and seeds k=9.
# Partial output has NO completed-census aggregate.
 /tmp/qf-resume 11 /scratch/quixo \
  --checkpoint /scratch/quixo/checkpoints \
  --checkpoint-at 8 --stop-after 8 > prefix.jsonl

# Restore the exact k=9 frontier, continue and checkpoint after k=10.
 /tmp/qf-resume 11 /scratch/quixo \
  --resume /scratch/quixo/checkpoints/checkpoint-9 \
  --checkpoint /scratch/quixo/checkpoints \
  --checkpoint-at 10 --stop-after 10 > middle.jsonl

# Complete k=11 and combine the three result streams.
 /tmp/qf-resume 11 /scratch/quixo \
  --resume /scratch/quixo/checkpoints/checkpoint-11 > suffix.jsonl

cat prefix.jsonl middle.jsonl suffix.jsonl > completed.jsonl
python tools/check_dual_tier_census.py completed.jsonl
```

The example describes the supported commands; it is not a claim that
K11 has been completed. Check that scratch space is sufficient first
with `python tools/estimate_tier_scratch.py --cap 11`.

## Crash consistency and identity contract

1. Each snapshot generation occupies a uniquely named directory
   `checkpoint-N`, where N is its next unprocessed occupancy.
2. The process writes all next-tier bitmaps into a staging directory.
   Files are written with checked partial-write retry, and `fsync`.
   Their exact byte lengths and FNV-1a64 checksums are listed in
   `manifest.txt` alongside format version, board size, cap,
   continuation occupancy and aggregate counts.
3. After the manifest and staging directory are synchronized,
   the staging directory is atomically renamed to `checkpoint-N`,
   and the containing directory is synchronized.
4. Resume rejects missing files, symlinked bitmaps, size changes,
   corrupted contents, incomplete manifests, invalid schema and cap
   mismatches before processing *any* state.
5. A stopped or crashed run does NOT emit a final complete-census
   aggregate record. The original independent `check_dual_tier_census.py`
   rejects an incomplete JSONL transcript.
6. Snapshots require a **matching executable, algorithm/rules and
   architecture**. Checksums protect against accidental corruption;
   FNV-1a is **not** a cryptographic authenticity mechanism. Snapshots
   should only be loaded from trusted user-controlled directories.

The checkpoint manifest fixes the exact cap across resumes. To extend
from K11 to K12, begin the K11 run with a target cap of **at least 12**,
then checkpoint after K11. It is not valid to resume a cap=11 snapshot
under cap=12 without recomputing the frontier: the cap=11 run skips
occupancy-increasing edges out of K11.

## Correctness verification

The dedicated CI workflow `census-checkpoints.yml` compares the
original exhaustive reference K6 count with both:
- an uninterrupted out-of-core run, and
- a run interrupted after K3, resumed and interrupted after K4,
  and resumed again through K6.

The entire occupancy-by-occupancy JSONL streams and totals must
match exactly. CI independently corrupts a snapshot and changes
the requested cap and verifies that both attempts fail closed.

**Scope:** This provides exact occupancy-boundary checkpoints, NOT
checkpoints in the middle of an enormous same-tier cycle closure.
Interrupting mid-tier still loses progress made *since the last
completed occupancy*. Filesystem availability, disk space, and
runtime remain computational constraints.
