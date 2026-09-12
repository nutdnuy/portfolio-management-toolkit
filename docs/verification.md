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
