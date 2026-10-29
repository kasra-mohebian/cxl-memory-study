#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build
for name in memory_benchmark page_benchmark page_copy_benchmark tier_decision_simulation; do
  "${CXX:-g++}" -O3 -std=c++17 "src/$name.cpp" -o "build/$name"
done
if printf '#include <numa.h>\nint main() { return numa_available(); }\n' | "${CXX:-g++}" -x c++ -std=c++17 - -lnuma -o build/.numa_probe 2>/dev/null; then
  "${CXX:-g++}" -O3 -std=c++17 src/inter_tier_copy_benchmark.cpp -lnuma -o build/inter_tier_copy_benchmark
else
  rm -f build/inter_tier_copy_benchmark
  echo "Skipping inter-tier program: Linux libnuma headers/library unavailable." >&2
fi
