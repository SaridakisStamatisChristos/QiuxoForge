# QuixoForge external-memory exact 5x5 census architecture

## Rules and exactness contract

The optimized, separate implementation is tools/census5_dual_tier_external.cpp.
The original tools/census5_dual_tier.cpp stays unchanged as the reference
oracle. Both enumerate legal X-first, standard 5x5 Quixo board-and-turn
states. Both stop expanding terminal roots; D4 rotations/reflections
identify equivalent states without swapping colors or player-to-move.

A move taking an existing own-marked cube stays in the same
(number-X, number-O) tier. Taking a blank advances exactly one color
and hence raises the occupancy by one. No move can reduce occupancy.

## Fundamental search invariants

1. The exact combinatorial rank of every canonical board/turn pair
   determines one unique visited-set bit in one color-count tier.
2. The admission bit transitions from zero to one once. Every newly
   admitted same-tier canonical state is appended once to the FIFO.
3. The FIFO is processed until its read count equals its append count,
   closing arbitrary same-tier move cycles exactly.
4. Occupancy-increasing moves seed the next occupancy's color tiers.
   Earlier tiers cannot be reached after their occupancy is completed.
5. Even at the occupancy cap, moves that would add another cube are
   examined for an immediate winning action before their successor
   is excluded from the reachable-root count.
6. The final JSONL aggregate is written only after all requested
   tiers complete. An allocation, I/O, or scratch failure cannot
   produce a valid complete census summary.

## New storage ownership

The previous implementation preallocated visited bitsets for all
tiers through the cap and stored every discovered same-tier D4
canonical state in a large in-memory vector.

The new implementation instead:

- Allocates a bitmap only when a predecessor first discovers its tier.
- Uses a file-backed MAP_SHARED bitmap, with exact combinatorial ranks
  as bit positions. Files are preallocated with posix_fallocate, so
  unavailable scratch capacity is detected before mapping.
- Destroys bitmap mappings as soon as their tiers are fully processed.
- Uses a strict buffered external-memory FIFO. Two 32,768-element
  uint64 buffers require 512 KiB total of FIFO application memory.
  Read/write offsets, partial I/O and interrupted system calls are
  handled explicitly by checked pread/pwrite loops.
- Unlinks temporary files immediately after creation and closes them
  as they finish; the filesystem reclaims scratch space.

The entire algorithm is still exact, conditional on correct POSIX
filesystem behavior. Mapped pages may reside in the kernel page
cache: this is NOT a strict overall RAM usage cap. Scratch disk
capacity and run time now become the principal scale limits.

## Resource ceiling and capacity planning

The worst-case bitmap universe for one complete occupancy level k is

    2 * binomial(25, k) * 2^k bits.

Peak scratch must accommodate the active level, next-level seed
bitmaps, and up to eight bytes per distinct canonical state in the
active tier's FIFO. The disk-backed architecture alone does not make
a complete all-25 enumeration feasible on standard GitHub runners.

Linux/POSIX C++17 is required. The directory supplied as the second
argument must already exist and be writable.

    g++ -std=c++17 -O3 -Wall -Wextra -pedantic \
      tools/census5_dual_tier_external.cpp -o /tmp/quixo-ooc
    /usr/bin/time -v /tmp/quixo-ooc 7 /tmp > k7.jsonl
    python tools/check_dual_tier_census.py k7.jsonl

Use the exact structural scratch estimator before large runs:

    python tools/estimate_tier_scratch.py --cap 11

This reports worst-case file reservations, not typical physical memory,
reachable-state counts, or a performance prediction. A successful
preflight does not guarantee the disk will remain sufficient if
other workloads consume space.

The dedicated out-of-core GitHub workflow independently runs the
unchanged original and new implementation at K7 and K8 on the same
runner, compares all occupancy and aggregate counts exactly, and
captures measured time and peak resident memory.

## Still required for larger occupancy levels

Durable restartable checkpoints at occupancy boundaries, disk
capacity guards, parallel/distributed processing with safe
same-tier barriers, and denser D4-orbit bitmap indexing are
potential further optimizations. They have NOT been implemented
or tested in this branch. Do not treat K7/K8 parity as proof
that K25 is tractable.
