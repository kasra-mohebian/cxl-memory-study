# Corrected code and remaining benchmark limitations

## Version boundary

The recorded course results were produced by an earlier source revision, retained privately with the original coursework. Current code is a corrected tool revision, not the source of those historical values. No new RAM/HBM/CXL comparison has been collected.

## Implementation corrections

- Strict decimal parsing rejects signs, trailing text, zero size and byte-count overflow before allocation.
- Interval timing uses `steady_clock`.
- Copy buffers contain an index-dependent pattern. Complete destination contents are checked after each pass, outside timing, and the destination is reset before the random pass.
- NUMA nodes must be online and allowed. All touched pages are queried in bounded batches; placement mismatch or an unavailable query fails closed. CPU binding and raw stdout/stderr are retained by the runner.
- The build skips the inter-tier target explicitly when libnuma is unavailable. The simulation uses page ID to break frequency ties deterministically.

These changes address implementation defects; they do not repair the old measurements. The former wrapping checksum could not establish full-copy integrity, and allocation success did not prove NUMA residency.

## Experimental limits still open

The page-read program touches one cache line per 4 KiB page. A 1 GiB region therefore touches about 16 MiB of cache lines, potentially fitting in a large last-level cache. Initialization and fixed sequential-before-random passes can leave cache state warm. These timings cannot isolate uncached memory-tier latency or bandwidth without hardware counters and a controlled cache experiment.

Repetitions are few, some distributions are broad or bimodal, and tier/run order is fixed. A higher observed mean is not proof of a stable technology ranking. Reviewed plots show dispersion and flag the HBM 8 GiB two-buffer capacity case; historical files are retained unchanged. Future measurements need warm-up, counter-balanced order, frequency/topology records and separately stored results.

The simulation ranks pages and evaluates placement on the same synthetic trace. Its hit shares are in-sample allocation summaries, not held-out predictions or query-speedup estimates. Manual inter-tier/capacity-check files lack complete provenance; unknown run time or pinning has not been invented, and they are not pooled into the automated comparison.

## Validation scope

One local macOS review exercised the four portable programs without libnuma placement. A separate Linux review compiled all five programs and exercised the NUMA program on a single-node machine. Neither reviewed the original multi-tier server. The new regression suite checks portable argument/copy behaviour and Linux CI builds the NUMA program and checks invalid-node rejection. A successful build or single-node run is not a validation on the original RAM/HBM/CXL server. Real multi-tier residency/performance still needs suitable hardware and permissions.

Historical plots are unchanged. In particular, their generic "Read bandwidth" label describes a sampled read (one byte per 64-byte stride), expressed as address range per second. Reviewed plots use the explicit label instead.
