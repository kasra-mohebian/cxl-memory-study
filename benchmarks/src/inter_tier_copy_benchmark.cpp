#include "benchmark_common.hpp"
#include <numa.h>
#include <algorithm>
#include <chrono>
#include <cstring>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>

bool verify_residency(char* data, size_t size, int node) {
    constexpr size_t page_size = 4096, batch = 4096;
    std::vector<void*> pages;
    std::vector<int> status;
    for (size_t offset = 0; offset < size; ) {
        pages.clear();
        for (size_t i = 0; i < batch && offset < size; ++i, offset += page_size)
            pages.push_back(data + offset);
        status.assign(pages.size(), -1);
        if (numa_move_pages(0, pages.size(), pages.data(), nullptr, status.data(), 0) < 0) {
            std::cerr << "Cannot verify NUMA page residency: " << std::strerror(errno) << "\n";
            return false;
        }
        for (int actual : status)
            if (actual != node) { std::cerr << "NUMA page residency mismatch/error\n"; return false; }
    }
    return true;
}

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " <src_node> <dst_node> <size_mib>\n";
        return 1;
    }

    if (numa_available() < 0) {
        std::cerr << "NUMA is not available\n";
        return 1;
    }

    int src_node, dst_node;
    size_t size_mb;
    try { src_node = parse_node(argv[1]); dst_node = parse_node(argv[2]); size_mb = parse_mib(argv[3]); }
    catch (const std::exception& error) { std::cerr << error.what() << "\n"; return 2; }
    auto* allowed = numa_get_mems_allowed();
    bool nodes_ok = allowed && src_node <= numa_max_node() && dst_node <= numa_max_node()
        && numa_bitmask_isbitset(numa_all_nodes_ptr, src_node)
        && numa_bitmask_isbitset(numa_all_nodes_ptr, dst_node)
        && numa_bitmask_isbitset(allowed, src_node) && numa_bitmask_isbitset(allowed, dst_node);
    if (allowed) numa_bitmask_free(allowed);
    if (!nodes_ok) { std::cerr << "Invalid or disallowed NUMA node\n"; return 2; }

    const size_t page_size = 4096;
    const size_t size = size_mb * 1024ULL * 1024ULL;
    const size_t num_pages = size / page_size;

    std::cout << "Source NUMA node: " << src_node << "\n";
    std::cout << "Destination NUMA node: " << dst_node << "\n";
    std::cout << "Benchmark size: " << size_mb << " MiB\n";
    std::cout << "Page size: " << page_size << " bytes\n";
    std::cout << "Number of pages: " << num_pages << "\n";

    char* src = static_cast<char*>(numa_alloc_onnode(size, src_node));
    char* dst = static_cast<char*>(numa_alloc_onnode(size, dst_node));

    if (src == nullptr || dst == nullptr) {
        std::cerr << "Allocation failed\n";
        if (src) numa_free(src, size);
        if (dst) numa_free(dst, size);
        return 1;
    }

    fill_pattern(src, size);
    std::memset(dst, 0, size);
    if (!verify_residency(src, size, src_node) || !verify_residency(dst, size, dst_node)) {
        numa_free(src, size); numa_free(dst, size); return 4;
    }


    auto seq_start = std::chrono::steady_clock::now();

    for (size_t i = 0; i < num_pages; i++) {
        std::memcpy(dst + i * page_size, src + i * page_size, page_size);
    }

    auto seq_end = std::chrono::steady_clock::now();
    if (!verify_copy(src, dst, size)) {
        std::cerr << "seq full-copy verification failed\n";
        numa_free(src, size); numa_free(dst, size);
        return 3;
    }
    double seq_seconds = std::chrono::duration<double>(seq_end - seq_start).count();

    std::vector<size_t> page_indices(num_pages);
    std::iota(page_indices.begin(), page_indices.end(), 0);

    std::mt19937 rng(42);
    std::shuffle(page_indices.begin(), page_indices.end(), rng);

    std::memset(dst, 0, size);
    if (!verify_residency(src, size, src_node) || !verify_residency(dst, size, dst_node)) {
        numa_free(src, size); numa_free(dst, size); return 4;
    }

    auto rand_start = std::chrono::steady_clock::now();

    for (size_t page_index : page_indices) {
        std::memcpy(dst + page_index * page_size, src + page_index * page_size, page_size);
    }

    auto rand_end = std::chrono::steady_clock::now();
    if (!verify_copy(src, dst, size)) {
        std::cerr << "rand full-copy verification failed\n";
        numa_free(src, size); numa_free(dst, size);
        return 3;
    }
    double rand_seconds = std::chrono::duration<double>(rand_end - rand_start).count();


    if (!verify_residency(src, size, src_node) || !verify_residency(dst, size, dst_node)) {
        numa_free(src, size); numa_free(dst, size); return 4;
    }
    double size_gb = static_cast<double>(size) / (1024.0 * 1024.0 * 1024.0);

    double seq_copy_gbs = size_gb / seq_seconds;
    double rand_copy_gbs = size_gb / rand_seconds;

    double seq_page_mpps = static_cast<double>(num_pages) / seq_seconds / 1e6;
    double rand_page_mpps = static_cast<double>(num_pages) / rand_seconds / 1e6;



    std::cout << "Sequential inter-tier copy time: " << seq_seconds << " s\n";
    std::cout << "Sequential inter-tier copy bandwidth: " << seq_copy_gbs << " GiB/s\n";
    std::cout << "Sequential inter-tier copy: " << seq_page_mpps << " million pages/s\n";

    std::cout << "Random inter-tier copy time: " << rand_seconds << " s\n";
    std::cout << "Random inter-tier copy bandwidth: " << rand_copy_gbs << " GiB/s\n";
    std::cout << "Random inter-tier copy: " << rand_page_mpps << " million pages/s\n";

    std::cout << "Full-copy verification: passed (both passes)\n";

    numa_free(src, size);
    numa_free(dst, size);

    return 0;
}
