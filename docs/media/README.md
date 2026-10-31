# Technical project illustration

`project-overview-technical.png` was generated with the built-in OpenAI image-generation tool in Codex. It is conceptual artwork, not a screenshot, measured chart, hardware photograph or a figure taken from a paper or teaching material.

Technical concept illustration of the memory tiers and page operations; it is not the measured server layout or a performance ranking.

The image follows CC BY 4.0 for original explanatory material, to the extent rights exist and are held. No exclusive rights are asserted in legally unprotectable material; third-party rights are unaffected.

## Generation prompt

> Use case: stylized-concept. Asset: wide technical editorial cover for a serious GitHub engineering portfolio. Create a richly detailed, professional technical illustration, not a generic cute infographic. Visual language: precision CAD-like cutaways blended with sophisticated scientific magazine illustration; deep ink/navy structures, luminous teal pathways, restrained amber highlights, pale neutral background, subtle alignment grid, clear hierarchy and depth. Wide landscape around 2:1. Fine engineering details must serve the explanation, not random ornament. No people, university/publisher marks, brand logos, watermarks, fake benchmark numbers, charts or product screenshots. All spatial layouts are conceptual schematics. Use only the few exact labels requested, with crisp typography. Subject: CPU-driven page-operation experiments across three abstract memory domains. Show a coherent CPU/root-complex block with a local RAM domain, a distinct high-bandwidth HBM domain, and a CXL-attached domain reached through a visibly separate link. Depict page-sized tiles moving between source and destination buffers, a sequential sweep and a shuffled access path as two inset ribbon diagrams, and an explicit small NUMA placement boundary. Include data-path arrows and magnified buffer-cell texture. Do not imply one actual server physical layout, module form factor, speed ranking, latency values or a DBMS implementation. No SSD or GPU. Exact labels only: 'RAM', 'HBM', 'CXL', 'PAGE OPERATIONS', 'SCHEMATIC'.

### Refinement 1

> Preserve this sophisticated technical schematic and its labels, color palette, memory-cell detail and page-operation insets. Correct one potentially misleading connection: CXL memory must have a clearly separate path from the CPU/root-complex region directly to the CXL attachment, bypassing the HBM block entirely. HBM is not a bridge to CXL. Route this teal CXL path visibly in a separate lane below or behind the HBM domain, with a distinct attachment interface; HBM keeps its own direct amber CPU connection and RAM keeps its own direct local connection. Do not depict a literal tested motherboard or assert exact packaging: make all three memory domains visibly schematic. Keep the SCHEMATIC designation. No GPU, SSD, throughput values or physical-layout claims.
