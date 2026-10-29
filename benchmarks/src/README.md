# Code walkthrough

This directory contains all five C++ source files found in the completed course-project snapshot. The current implementations are a post-course correction; the measurement-era sources are retained privately with the original coursework. The executable experiments, recorded data and plotting path are connected below so a reviewer can inspect the implementation rather than relying on the report alone.

| Source | Implementation | Recorded evidence |
| --- | --- | --- |
| [memory_benchmark.cpp](memory_benchmark.cpp) | Allocates a buffer, times sequential writes and reads one byte per 64-byte stride; reports bandwidth over the covered range | [Raw CSV](../results/memory_benchmark.csv) |
| [page_benchmark.cpp](page_benchmark.cpp) | Reads one byte per 4 KiB page in sequential and shuffled order; uses a volatile accumulator | [Raw CSV](../results/page_benchmark.csv) |
| [page_copy_benchmark.cpp](page_copy_benchmark.cpp) | Copies complete 4 KiB pages with memcpy between two buffers, sequentially and after shuffling page indices | [Raw CSV](../results/page_copy_benchmark.csv), [size sweep](../results/page_copy_size_sweep.csv) |
| [inter_tier_copy_benchmark.cpp](inter_tier_copy_benchmark.cpp) | Allocates source and destination with libnuma on the requested nodes, then measures sequential/shuffled page copies | [Raw CSV](../results/inter_tier_copy_benchmark.csv) |
| [tier_decision_simulation.cpp](tier_decision_simulation.cpp) | Generates a skewed access trace, sorts pages by observed frequency, assigns fixed HBM/RAM capacities and counts accesses served | [Recorded outputs](../results/) |

## Follow one experiment end to end

1. Read `page_copy_benchmark.cpp`: allocation and initialization precede timing; the timed loops copy 4 KiB pages; the random pass follows the sequential pass.
2. Inspect [run_benchmarks.sh](../scripts/run_benchmarks.sh): it builds the experiment matrix, selects CPU/memory placement for single-tier tests, repeats runs and parses program output into CSV rows.
3. Open the raw page-copy CSV and its summary in [results](../results/). Basic local-copy experiments have five repetitions; the size sweep and inter-tier experiments have three.
4. Inspect [plot_results.py](../scripts/plot_results.py) to see how saved data becomes figures. The [experiment guide](../README.md) and [reviewed plots](../plots-reviewed/) explain those measurements without distributing the full report.

## Build and inspect without special memory hardware

From `benchmarks/`, the following builds the four programs that do not link libnuma. Use a C++17 compiler; these small runs inspect program execution, not CXL performance.

```bash
mkdir -p build
for name in memory_benchmark page_benchmark page_copy_benchmark tier_decision_simulation; do
  "${CXX:-c++}" -O3 -std=c++17 "src/$name.cpp" -o "build/$name"
done
./build/memory_benchmark 1
./build/page_benchmark 1
./build/page_copy_benchmark 1
./build/tier_decision_simulation
```

The numeric argument is the buffer size in MiB. Copy tests allocate two buffers. The simulation takes no arguments. Use positive, modest sizes. Invalid arguments are rejected; copy programs compare all destination bytes against the source outside both timed intervals. Read the [confirmed limitations](../KNOWN-LIMITATIONS.md) before interpreting a new run.

For the full Linux build, libnuma requirements and hardware-dependent runs, follow the [experiment guide](../README.md). The inter-tier program accepts source node, destination node and size in MiB. The public runner requires explicit local node configuration and a new output directory. New inter-tier runs bind the CPU node explicitly and query page residency. This changes the historical method and does not retroactively validate the saved measurements.

## What this implementation demonstrates

The code makes memory-access order, page granularity, working-set size, allocation placement and copy direction explicit. The simulation connects observed access frequencies to a simple placement decision. It does not implement a complete database buffer pool, online migration policy or query engine. Recorded hardware measurements are distinct from a portable smoke run, and fixed RNG seeds do not promise identical shuffles across standard libraries.

The original separate shell runners are consolidated into the public runner with configurable topology and protection against overwriting saved results. Source changes and new tests are documented in the correction notes; archived numerical results are unchanged.
