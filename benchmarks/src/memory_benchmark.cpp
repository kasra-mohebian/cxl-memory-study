#include "benchmark_common.hpp"
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <vector>

int main(int argc, char** argv) {
    size_t size_mb = 1024; // legacy name; value is MiB (default: 1 GiB)

    if (argc > 2) { std::cerr << "Usage: " << argv[0] << " [size_mib]\n"; return 2; }
    try { if (argc == 2) size_mb = parse_mib(argv[1]); }
    catch (const std::exception& error) { std::cerr << error.what() << "\n"; return 2; }

    const size_t size = size_mb * 1024ULL * 1024ULL;
    const size_t page_size = 4096;

    std::cout << "Benchmark size: " << size_mb << " MiB\n";

    char* buffer = nullptr;
    int ret = posix_memalign(reinterpret_cast<void**>(&buffer), page_size, size);
    if (ret != 0 || buffer == nullptr) {
        std::cerr << "Allocation failed\n";
        return 1;
    }

    // Touch pages first, so memory is really allocated on the selected NUMA node.
    for (size_t i = 0; i < size; i += page_size) {
        buffer[i] = 1;
    }

    // Sequential write benchmark
    auto start_write = std::chrono::steady_clock::now();
    std::memset(buffer, 7, size);
    auto end_write = std::chrono::steady_clock::now();

    double write_seconds = std::chrono::duration<double>(end_write - start_write).count();
    double write_gb = static_cast<double>(size) / (1024.0 * 1024.0 * 1024.0);
    double write_bandwidth = write_gb / write_seconds;

    // Sequential read benchmark
    volatile uint64_t sum = 0;
    auto start_read = std::chrono::steady_clock::now();
    for (size_t i = 0; i < size; i += 64) {
        sum += buffer[i];
    }
    auto end_read = std::chrono::steady_clock::now();

    double read_seconds = std::chrono::duration<double>(end_read - start_read).count();
    double read_bandwidth = write_gb / read_seconds;

    std::cout << "Sequential write time: " << write_seconds << " s\n";
    std::cout << "Sequential write bandwidth: " << write_bandwidth << " GiB/s\n";
    std::cout << "Sequential read time: " << read_seconds << " s\n";
    std::cout << "Sequential read bandwidth: " << read_bandwidth << " GiB/s\n";
    std::cout << "Checksum: " << sum << "\n";

    free(buffer);
    return 0;
}
