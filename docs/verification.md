# Verification record

Date: 2026-09-12. Local macOS Chromium. Node.js 22.22.3, Python 3.9.6.

This record covers the owner-selected Thai book revision based on the Binomial Model reference.

- `npm test`: 16 numerical checks passed, including analytic portfolio paths, gap risk and cash lock, rate/floor consistency, no lookahead, exposure caps, payoff/profit separation and CSV consistency.
- `npm run check:notebook`: complete chapter prose and equations captured, source/model hashes current, all 10 code cells re-executed with matching outputs, two valid SVG charts, and 16 Python/JavaScript path comparisons passed. The Notebook contains 29 cells across the 13 chapter sections.
- `npm run build:pages`: three primary book pages, six HTML files including legacy redirects and licenses, and 227 local references passed. Checks include anchors, unique IDs, book.css, fonts, Markdown downloads and a populated Notebook without error outputs.
- `npm run check:site`: 32 browser checks passed. Eighteen page scans cover three pages at 1440, 390 and 320 pixels in light/dark themes. No document overflow, serious/critical accessibility findings, color-contrast violations, runtime errors, missing resources or external runtime/font requests were detected.
- Interaction coverage: fresh light default, theme persistence, desktop sidebar and chapter contents anchors, mobile navigation, print invocation, English/Thai global search, empty results, Escape and focus restoration, 23-term glossary filtering and group visibility, direct term anchors and return links, native Notebook and Markdown downloads, four CPPI scenarios, sliders and keyboard control, reset, 13 data observations, six saved runs and recall, exact CSV export, Put calculations and premium bound, three-stage walkthrough, three React Bits families and reduced motion.
- Separate offline check with network disabled: local-file chapter opening, CPPI rally calculation, global search and glossary filtering passed with no runtime errors.
- Visual inspection: desktop chapter and inline CPPI experiment, mobile chapter and Put calculator; QA screenshots also cover Welcome/chapter/CPPI in both themes. Local evidence: `qa/output/`.
- Source review: thesis concepts and findings checked against the local PDF. The two selected CPT score scenarios were checked visually against Table 5.2 Panel C, printed p. 90 / PDF p. 117. Citations distinguish thesis evidence from original teaching examples.
- Final diff review and `git diff --check` passed. The original quantitative-finance-notes working tree remains clean.

The site is a local preview with no new hosted repository or live deployment. The source PDF is not redistributed. No real market backtest or full thesis Monte Carlo replication is claimed. Safari/Firefox and full screen-reader narration were not tested.

## 2026-09-13 — Portfolio Management Toolkit Notes

Continued the existing standalone project built from the same source thesis. Updated the book title, Welcome page, metadata, Notebook introduction and author attribution (QuantCorner). Reused the approved QuantCorner / Quantsera cover from the current Quantitative Finance Notes website and removed a duplicated scenario label in the CPPI selector.

- `npm test`: 16 numerical checks passed.
- `npm run notebook` and `npm run check:notebook`: 29 cells, 10 executed code cells, two SVG charts, full chapter capture and 16 Python/JavaScript path comparisons passed.
- `npm run build:pages`: three book pages, six HTML files and 232 local references passed.
- `npm run check:site`: all 32 browser checks and 18 accessibility scans passed, with no recorded failures.
- Additional cover checks: 12 viewport/theme combinations at 320, 390, 768, 800, 834 and 1440 px; both image boxes fit, original proportions remain intact, and visible widths and painted centers match. All three page titles and author footers passed. Evidence: `qa/output/cover-results.json`.
- Focused check after the final UI copy edit: all four scenario labels appear once and all four CPPI scenarios remain selectable.
- Current offline verification: local-file CPPI scenario selection, global search and glossary filtering passed without runtime errors.
- Visual inspection: Welcome on desktop/mobile and the inline CPPI experiment. Quantsera brand preflight and immutable asset checksums passed.
- Source review: checked the supplied local thesis for protective strategies, CPPI/TIPP mechanics, simulation assumptions, EUT/CPT findings and the limitations of its robo-advisor sample. This was a targeted review of relevant sections, not a full independent replication of the thesis.

Publication requires a new repository; the local preview is ready at `http://127.0.0.1:8764/`. The original Quantitative Finance Notes repository remains unchanged. The source PDF is not included. Safari/Firefox and full screen-reader narration have not been tested.
