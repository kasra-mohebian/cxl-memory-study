#!/usr/bin/env bash
set -euo pipefail
: "${CPU_NODE:?Set CPU_NODE for this system}"
: "${RAM_NODE:?Set RAM_NODE for this system}"
: "${HBM_NODE:?Set HBM_NODE for this system}"
: "${CXL_NODE:?Set CXL_NODE for this system}"
: "${RUN_DIR:?Set RUN_DIR to a new output directory}"
# Resolve relative output against the caller, before changing directories.
RUN_DIR=$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$RUN_DIR")
cd "$(dirname "$0")/.."

if [[ -e "$RUN_DIR" ]]; then echo "RUN_DIR already exists; choose a new directory." >&2; exit 1; fi
for bin in memory_benchmark page_benchmark page_copy_benchmark inter_tier_copy_benchmark; do
 if [[ ! -x "build/$bin" ]]; then echo "Missing build/$bin; run scripts/build.sh first." >&2; exit 1; fi
done
mkdir -p "$RUN_DIR/raw"
{
  git rev-parse HEAD 2>/dev/null || echo "source: not a git checkout"
  "${CXX:-g++}" --version
  uname -a
  date -u +%FT%TZ
  numactl -H || echo "numactl topology unavailable; benchmark commands still require numactl"
  for path in /sys/kernel/mm/transparent_hugepage/enabled /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; do
    if [[ -r "$path" ]]; then printf '%s: ' "$path"; cat "$path"; fi
  done
} > "$RUN_DIR/environment.txt" 2>&1
capture() {
  local prefix="$RUN_DIR/raw/${OUT##*/}"
  prefix="${prefix%.csv}-$1"; shift
  if ! "$@" > "$prefix.stdout" 2> "$prefix.stderr"; then
    echo "Run failed; see $prefix.stderr" >&2
    return 1
  fi
  cat "$prefix.stdout"
}

# run_memory_benchmarks_csv.sh


OUT="$RUN_DIR/memory_benchmark.csv"

echo "run,tier,size_mb,write_gbs,read_gbs" > "$OUT"

run_benchmark() {
    local run="$1"
    local tier="$2"
    local cpu_node="$3"
    local mem_node="$4"
    local size_mb="$5"

    output=$(capture "$run-$tier-$size_mb" numactl --cpunodebind="$cpu_node" --membind="$mem_node" ./build/memory_benchmark "$size_mb")

    write_gbs=$(echo "$output" | awk '/Sequential write bandwidth/ {print $4}')
    read_gbs=$(echo "$output" | awk '/Sequential read bandwidth/ {print $4}')

    echo "$run,$tier,$size_mb,$write_gbs,$read_gbs" >> "$OUT"
}

for run in 1 2 3 4 5; do
    run_benchmark "$run" "RAM" "$CPU_NODE" "$RAM_NODE" 1024
    run_benchmark "$run" "HBM" "$CPU_NODE" "$HBM_NODE" 1024
    run_benchmark "$run" "CXL" "$CPU_NODE" "$CXL_NODE" 1024
done

echo "Done. CSV results saved to $OUT"


# run_page_benchmarks_csv.sh


OUT="$RUN_DIR/page_benchmark.csv"

echo "run,tier,size_mb,seq_page_mpps,rand_page_mpps" > "$OUT"

run_benchmark() {
    local run="$1"
    local tier="$2"
    local cpu_node="$3"
    local mem_node="$4"
    local size_mb="$5"

    output=$(capture "$run-$tier-$size_mb" numactl --cpunodebind="$cpu_node" --membind="$mem_node" ./build/page_benchmark "$size_mb")

    seq_mpps=$(echo "$output" | awk '/Sequential page read:/ {print $4}')
    rand_mpps=$(echo "$output" | awk '/Random page read:/ {print $4}')

    echo "$run,$tier,$size_mb,$seq_mpps,$rand_mpps" >> "$OUT"
}

for run in 1 2 3 4 5; do
    run_benchmark "$run" "RAM" "$CPU_NODE" "$RAM_NODE" 1024
    run_benchmark "$run" "HBM" "$CPU_NODE" "$HBM_NODE" 1024
    run_benchmark "$run" "CXL" "$CPU_NODE" "$CXL_NODE" 1024
done

echo "Done. CSV results saved to $OUT"


# run_page_copy_benchmarks_csv.sh

OUT="$RUN_DIR/page_copy_benchmark.csv"

echo "run,tier,size_mb,seq_copy_gbs,seq_copy_mpps,rand_copy_gbs,rand_copy_mpps" > "$OUT"

run_benchmark() {
    local run="$1"
    local tier="$2"
    local cpu_node="$3"
    local mem_node="$4"
    local size_mb="$5"

    output=$(capture "$run-$tier-$size_mb" numactl --cpunodebind="$cpu_node" --membind="$mem_node" ./build/page_copy_benchmark "$size_mb")

    seq_copy_gbs=$(echo "$output" | awk '/Sequential page copy bandwidth/ {print $5}')
    seq_copy_mpps=$(echo "$output" | awk '/Sequential page copy:/ {print $4}')
    rand_copy_gbs=$(echo "$output" | awk '/Random page copy bandwidth/ {print $5}')
    rand_copy_mpps=$(echo "$output" | awk '/Random page copy:/ {print $4}')

    echo "$run,$tier,$size_mb,$seq_copy_gbs,$seq_copy_mpps,$rand_copy_gbs,$rand_copy_mpps" >> "$OUT"
}

for run in 1 2 3 4 5; do
    run_benchmark "$run" "RAM" "$CPU_NODE" "$RAM_NODE" 1024
    run_benchmark "$run" "HBM" "$CPU_NODE" "$HBM_NODE" 1024
    run_benchmark "$run" "CXL" "$CPU_NODE" "$CXL_NODE" 1024
done

echo "Done. CSV results saved to $OUT"


# run_page_copy_size_sweep.sh

OUT="$RUN_DIR/page_copy_size_sweep.csv"

echo "run,tier,size_mb,seq_copy_gbs,seq_copy_mpps,rand_copy_gbs,rand_copy_mpps" > "$OUT"

run_benchmark() {
    local run="$1"
    local tier="$2"
    local cpu_node="$3"
    local mem_node="$4"
    local size_mb="$5"

    output=$(capture "$run-$tier-$size_mb" numactl --cpunodebind="$cpu_node" --membind="$mem_node" ./build/page_copy_benchmark "$size_mb")

    seq_copy_gbs=$(echo "$output" | awk '/Sequential page copy bandwidth/ {print $5}')
    seq_copy_mpps=$(echo "$output" | awk '/Sequential page copy:/ {print $4}')
    rand_copy_gbs=$(echo "$output" | awk '/Random page copy bandwidth/ {print $5}')
    rand_copy_mpps=$(echo "$output" | awk '/Random page copy:/ {print $4}')

    echo "$run,$tier,$size_mb,$seq_copy_gbs,$seq_copy_mpps,$rand_copy_gbs,$rand_copy_mpps" >> "$OUT"
}

for size_mb in 1024 4096 8192; do
    for run in 1 2 3; do
        run_benchmark "$run" "RAM" "$CPU_NODE" "$RAM_NODE" "$size_mb"
        run_benchmark "$run" "HBM" "$CPU_NODE" "$HBM_NODE" "$size_mb"
        run_benchmark "$run" "CXL" "$CPU_NODE" "$CXL_NODE" "$size_mb"
    done
done

echo "Done. CSV results saved to $OUT"


# run_inter_tier_copy_benchmark_csv.sh

BIN="./build/inter_tier_copy_benchmark"
OUT="$RUN_DIR/inter_tier_copy_benchmark.csv"



echo "run,src_tier,dst_tier,size_mb,seq_copy_gbs,seq_copy_mpps,rand_copy_gbs,rand_copy_mpps" > "$OUT"

run_benchmark() {
    run="$1"
    src_tier="$2"
    src_node="$3"
    dst_tier="$4"
    dst_node="$5"
    size_mb="$6"

    output=$(capture "$run-$src_tier-$dst_tier-$size_mb" numactl --cpunodebind="$CPU_NODE" "$BIN" "$src_node" "$dst_node" "$size_mb")

    seq_copy_gbs=$(echo "$output" | awk '/Sequential inter-tier copy bandwidth/ {print $5}')
    seq_copy_mpps=$(echo "$output" | awk '/Sequential inter-tier copy:/ {print $4}')
    rand_copy_gbs=$(echo "$output" | awk '/Random inter-tier copy bandwidth/ {print $5}')
    rand_copy_mpps=$(echo "$output" | awk '/Random inter-tier copy:/ {print $4}')

    echo "$run,$src_tier,$dst_tier,$size_mb,$seq_copy_gbs,$seq_copy_mpps,$rand_copy_gbs,$rand_copy_mpps" >> "$OUT"
}

for run in 1 2 3; do
    run_benchmark "$run" "RAM" "$RAM_NODE" "CXL" "$CXL_NODE" 1024
    run_benchmark "$run" "CXL" "$CXL_NODE" "RAM" "$RAM_NODE" 1024
    run_benchmark "$run" "RAM" "$RAM_NODE" "HBM" "$HBM_NODE" 1024
    run_benchmark "$run" "HBM" "$HBM_NODE" "RAM" "$RAM_NODE" 1024
    run_benchmark "$run" "HBM" "$HBM_NODE" "CXL" "$CXL_NODE" 1024
    run_benchmark "$run" "CXL" "$CXL_NODE" "HBM" "$HBM_NODE" 1024
done

echo "Done. CSV results saved to $OUT"
