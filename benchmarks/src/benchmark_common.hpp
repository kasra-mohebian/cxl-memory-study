#pragma once
#include <cerrno>
#include <climits>
#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>

inline unsigned long long parse_unsigned(const char* text) {
    if (!text || !*text) throw std::invalid_argument("empty numeric argument");
    for (const char* p = text; *p; ++p)
        if (*p < '0' || *p > '9') throw std::invalid_argument("expected decimal digits only");
    errno = 0;
    char* end = nullptr;
    auto value = std::strtoull(text, &end, 10);
    if (errno == ERANGE || !end || *end) throw std::out_of_range("numeric argument out of range");
    return value;
}
inline size_t parse_mib(const char* text) {
    auto value = parse_unsigned(text);
    if (!value || value > (std::numeric_limits<size_t>::max() >> 20))
        throw std::out_of_range("size must be positive MiB without byte-count overflow");
    return static_cast<size_t>(value);
}
inline int parse_node(const char* text) {
    auto value = parse_unsigned(text);
    if (value > INT_MAX) throw std::out_of_range("NUMA node out of range");
    return static_cast<int>(value);
}
inline void fill_pattern(char* data, size_t size) {
    // Every aligned 64-bit word carries a unique address-derived value.
    // Unlike a repeated byte pattern, this detects whole-page misplacement.
    for (size_t offset = 0; offset < size;) {
        const uint64_t word = static_cast<uint64_t>(offset / sizeof(uint64_t))
                              ^ UINT64_C(0x9e3779b97f4a7c15);
        const size_t count = (size - offset < sizeof(word)) ? size - offset : sizeof(word);
        std::memcpy(data + offset, &word, count);
        offset += count;
    }
}
inline bool verify_copy(const char* source, const char* destination, size_t size) {
    return std::memcmp(source, destination, size) == 0;
}
