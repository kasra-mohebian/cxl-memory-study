#include "benchmark_common.hpp"
#include <chrono>
#include <cstring>
#include <iostream>
#include <random>
#include <vector>
#include <algorithm>
#include <cstdlib>

int main(int argc, char** argv) {
    size_t size_mb = 1024;

    if (argc > 2) { std::cerr << "Usage: " << argv[0] << " [size_mib]\n"; return 2; }
    try { if (argc == 2) size_mb = parse_mib(argv[1]); }
    catch (const std::exception& error) { std::cerr << error.what() << "\n"; return 2; }

    const size_t page_size = 4096;
    const size_t size = size_mb * 1024ULL * 1024ULL;
    const size_t num_pages = size / page_size;

    std::cout << "Benchmark size: " << size_mb << " MiB\n";
    std::cout << "Page size: " << page_size << " bytes\n";
    std::cout << "Number of pages: " << num_pages << "\n";

    char* src = nullptr;
    char* dst = nullptr;

    if (posix_memalign(reinterpret_cast<void**>(&src), page_size, size) != 0) {
        std::cerr << "Failed to allocate source buffer\n";
        return 1;
    }

    if (posix_memalign(reinterpret_cast<void**>(&dst), page_size, size) != 0) {
        std::cerr << "Failed to allocate destination buffer\n";
        free(src);
        return 1;
    }

    fill_pattern(src, size);
    std::memset(dst, 0, size);

    auto seq_start = std::chrono::steady_clock::now();

    for (size_t i = 0; i < num_pages; ++i) {
        std::memcpy(dst + i * page_size, src + i * page_size, page_size);
    }

    auto seq_end = std::chrono::steady_clock::now();
    if (!verify_copy(src, dst, size)) {
        std::cerr << "seq full-copy verification failed\n";
        free(src); free(dst);
        return 3;
    }

    double seq_seconds = std::chrono::duration<double>(seq_end - seq_start).count();
    double copied_gb = static_cast<double>(size) / (1024.0 * 1024.0 * 1024.0);
    double seq_copy_gbs = copied_gb / seq_seconds;
    double seq_page_mpps = static_cast<double>(num_pages) / seq_seconds / 1000000.0;

    std::vector<size_t> pages(num_pages);
    for (size_t i = 0; i < num_pages; ++i) {
        pages[i] = i;
    }

    std::mt19937_64 rng(42);
    std::shuffle(pages.begin(), pages.end(), rng);

    std::memset(dst, 0, size);
    auto rand_start = std::chrono::steady_clock::now();

    for (size_t idx : pages) {
        std::memcpy(dst + idx * page_size, src + idx * page_size, page_size);
    }

    auto rand_end = std::chrono::steady_clock::now();
    if (!verify_copy(src, dst, size)) {
        std::cerr << "rand full-copy verification failed\n";
        free(src); free(dst);
        return 3;
    }

    double rand_seconds = std::chrono::duration<double>(rand_end - rand_start).count();
    double rand_copy_gbs = copied_gb / rand_seconds;
    double rand_page_mpps = static_cast<double>(num_pages) / rand_seconds / 1000000.0;



    std::cout << "Sequential page copy time: " << seq_seconds << " s\n";
    std::cout << "Sequential page copy bandwidth: " << seq_copy_gbs << " GiB/s\n";
    std::cout << "Sequential page copy: " << seq_page_mpps << " million pages/s\n";

    std::cout << "Random page copy time: " << rand_seconds << " s\n";
    std::cout << "Random page copy bandwidth: " << rand_copy_gbs << " GiB/s\n";
    std::cout << "Random page copy: " << rand_page_mpps << " million pages/s\n";

    std::cout << "Full-copy verification: passed (both passes)\n";

    free(src);
    free(dst);

    return 0;
}
