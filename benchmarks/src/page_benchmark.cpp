#include "benchmark_common.hpp"
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>

int main(int argc, char** argv) {
    size_t size_mb = 1024; // legacy name; value is MiB (default: 1 GiB)
    size_t page_size = 4096; // 4 KiB pages

    if (argc > 2) { std::cerr << "Usage: " << argv[0] << " [size_mib]\n"; return 2; }
    try { if (argc == 2) size_mb = parse_mib(argv[1]); }
    catch (const std::exception& error) { std::cerr << error.what() << "\n"; return 2; }

    const size_t size = size_mb * 1024ULL * 1024ULL;
    const size_t num_pages = size / page_size;

    std::cout << "Benchmark size: " << size_mb << " MiB\n";
    std::cout << "Page size: " << page_size << " bytes\n";
    std::cout << "Number of pages: " << num_pages << "\n";

    char* buffer = nullptr;
    int ret = posix_memalign(reinterpret_cast<void**>(&buffer), page_size, size);
    if (ret != 0 || buffer == nullptr) {
        std::cerr << "Allocation failed\n";
        return 1;
    }

    // Touch all pages first to force NUMA allocation.
    for (size_t i = 0; i < num_pages; i++) {
        buffer[i * page_size] = static_cast<char>(i);
    }

    volatile uint64_t sum = 0;

    // Sequential page read
    auto seq_start = std::chrono::steady_clock::now();
    for (size_t i = 0; i < num_pages; i++) {
        sum += static_cast<unsigned char>(buffer[i * page_size]);
    }
    auto seq_end = std::chrono::steady_clock::now();

    double seq_seconds = std::chrono::duration<double>(seq_end - seq_start).count();
    double seq_mpps = static_cast<double>(num_pages) / seq_seconds / 1'000'000.0;

    // Random page read
    std::vector<size_t> pages(num_pages);
    std::iota(pages.begin(), pages.end(), 0);

    std::mt19937_64 rng(42);
    std::shuffle(pages.begin(), pages.end(), rng);

    auto rand_start = std::chrono::steady_clock::now();
    for (size_t idx : pages) {
        sum += static_cast<unsigned char>(buffer[idx * page_size]);
    }
    auto rand_end = std::chrono::steady_clock::now();

    double rand_seconds = std::chrono::duration<double>(rand_end - rand_start).count();
    double rand_mpps = static_cast<double>(num_pages) / rand_seconds / 1'000'000.0;

    std::cout << "Sequential page read time: " << seq_seconds << " s\n";
    std::cout << "Sequential page read: " << seq_mpps << " million pages/s\n";
    std::cout << "Random page read time: " << rand_seconds << " s\n";
    std::cout << "Random page read: " << rand_mpps << " million pages/s\n";
    std::cout << "Checksum: " << sum << "\n";

    free(buffer);
    return 0;
}
