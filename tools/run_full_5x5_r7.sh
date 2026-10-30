#!/bin/sh
# One-command reproducible full-board 5x5 research verification (Linux/POSIX).
# Requires C++17 and Python >=3.10. Python runtime dependencies: none.
set -eu
cd "$(dirname "$0")/.."
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/census5_native.cpp -o "$work/qf-native"
c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/verify5_native_raw.cpp -o "$work/qf-raw"
c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/verify7_dense_raw.cpp -o "$work/qf-raw7"
c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/verify8_dense_raw.cpp -o "$work/qf-raw8"
"$work/qf-native" 5 > "$work/k5.json"
"$work/qf-native" 6 > "$work/k6.json"
"$work/qf-native" 7 20000000 > "$work/k7.json"
"$work/qf-native" 8 100000000 > "$work/k8.json"
"$work/qf-raw" 6 > "$work/raw6.json"
"$work/qf-raw7" 7 125000000 > "$work/raw7.json"
"$work/qf-raw8" 8 700000000 > "$work/raw8.json"
python tools/check_native_census.py --k5 "$work/k5.json" --k6 "$work/k6.json" --k7 "$work/k7.json" --k8 "$work/k8.json" --raw6 "$work/raw6.json" --raw7 "$work/raw7.json" --raw8 "$work/raw8.json"
PYTHONPATH="src" python -m quixoforge.census5_forced3 --verify
sha256sum -c SHA256SUMS
echo "PASS: exact declared-domain 5x5 R7 census and independent six-, seven- and eight-cube raw reachability and full-scope one-ply tactic verification"
