#include <algorithm>
#include <iostream>
#include <random>
#include <string>
#include <vector>

struct Page {
    int id;
    int accesses;
    std::string tier;
};

int main() {
    const int page_count = 1000;
    const int hot_page_count = 100;
    const int total_accesses = 100000;

    const int hbm_capacity_pages = 100;
    const int ram_capacity_pages = 300;

    std::vector<Page> pages;

    for (int i = 0; i < page_count; i++) {
        pages.push_back({i, 0, "CXL"});
    }

    std::mt19937 rng(42);
    std::uniform_int_distribution<int> hot_dist(0, hot_page_count - 1);
    std::uniform_int_distribution<int> cold_dist(hot_page_count, page_count - 1);
    std::uniform_int_distribution<int> chance_dist(1, 100);

    for (int i = 0; i < total_accesses; i++) {
        int page_id;

        if (chance_dist(rng) <= 80) {
            page_id = hot_dist(rng);
        } else {
            page_id = cold_dist(rng);
        }

        pages[page_id].accesses++;
    }

    std::sort(pages.begin(), pages.end(), [](const Page& a, const Page& b) {
        return a.accesses != b.accesses ? a.accesses > b.accesses : a.id < b.id;
    });

    for (int i = 0; i < page_count; i++) {
        if (i < hbm_capacity_pages) {
            pages[i].tier = "HBM";
        } else if (i < hbm_capacity_pages + ram_capacity_pages) {
            pages[i].tier = "RAM";
        } else {
            pages[i].tier = "CXL";
        }
    }

    int hbm_pages = 0;
    int ram_pages = 0;
    int cxl_pages = 0;

    long long hbm_accesses = 0;
    long long ram_accesses = 0;
    long long cxl_accesses = 0;

    for (const auto& page : pages) {
        if (page.tier == "HBM") {
            hbm_pages++;
            hbm_accesses += page.accesses;
        } else if (page.tier == "RAM") {
            ram_pages++;
            ram_accesses += page.accesses;
        } else {
            cxl_pages++;
            cxl_accesses += page.accesses;
        }
    }

    std::cout << "Simple tier decision simulation\n";
    std::cout << "Total pages: " << page_count << "\n";
    std::cout << "Total accesses: " << total_accesses << "\n";
    std::cout << "Hot page range: 0-" << hot_page_count - 1 << "\n\n";

    std::cout << "Tier placement result:\n";
    std::cout << "HBM pages: " << hbm_pages << ", accesses served: " << hbm_accesses << "\n";
    std::cout << "RAM pages: " << ram_pages << ", accesses served: " << ram_accesses << "\n";
    std::cout << "CXL pages: " << cxl_pages << ", accesses served: " << cxl_accesses << "\n\n";

    std::cout << "Top 10 pages after placement:\n";
    std::cout << "page_id,accesses,tier\n";

    for (int i = 0; i < 10; i++) {
        std::cout << pages[i].id << "," << pages[i].accesses << "," << pages[i].tier << "\n";
    }

    return 0;
}
