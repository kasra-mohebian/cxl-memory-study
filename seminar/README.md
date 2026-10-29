# Seminar: CXL memory for database systems

I reviewed and presented **CXL Memory Performance for In-Memory Data Processing** by Weisgut et al. (PVLDB 2025). The seminar covered memory access patterns, database operators and workload-aware placement across CPU-local and CXL memory.

The main topics I discussed were:

- How sequential and random accesses respond to memory latency, bandwidth and prefetching.
- Why column scans, B+tree operations and full query workloads can behave differently.
- How the paper's Hyrise TPC-H experiment used column placement to keep frequently accessed data local.

Those experiments and findings belong to the paper's authors. I did not run them for the seminar. The discussion led to my own [course benchmarks](../benchmarks/README.md), which measure smaller page-oriented operations on a different system.

This README is a short description of what I reviewed. The submitted seminar report, slides, complete presentation text and speaker notes are not included.

**Source:** Weisgut et al., *CXL Memory Performance for In-Memory Data Processing*, PVLDB 18(9), 3119–3133, 2025. [DOI](https://doi.org/10.14778/3746405.3746432) · [Publisher's paper](https://www.vldb.org/pvldb/vol18/p3119-weisgut.pdf) · [References](../REFERENCES.md).
