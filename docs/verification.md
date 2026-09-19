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

## 2026-09-13 — Detailed lesson expansion

Expanded the existing 13 sections from 15 to 57 explanatory subsections, retaining all 19 explicit chapter anchors/mounts. Added derivations, multi-period accounting tables, eight review questions with answers, and 11 linked glossary entries (34 total). The mathematical website model and interface behavior are unchanged.

- Primary-source review covered strategy mechanics, the theoretical continuous CPPI claim, simulation assumptions, EUT/CPT definitions and Table 5.2, and the robo-advisor methodology. The six reproduced Panel C values were checked against the rendered PDF page 117. Independent review found no numerical errors; precision edits explicitly state independent GBM shocks, the weak Jensen inequality, and sampled versus continuous high-water marks.
- `npm test`: all 16 model checks passed.
- `npm run notebook` and `npm run check:notebook`: 36 cells, 17 executed code cells, two embedded SVG charts, complete canonical chapter capture, exact saved-output re-execution, and 16 Python/JavaScript path comparisons passed. Added assertions check the new budget, four-period CPPI, positive-rate gap, TIPP, utility/weighting and shortfall examples.
- `npm run build:pages`: three primary pages, six HTML files, 111 search entries and 264 local references passed.
- `npm run check:site`: 32 checks passed; all 18 page/theme/viewport accessibility scans had no recorded violations.
- Focused checks: all 378 rendered math expressions have no KaTeX errors; eight answer panels; new glossary English/Thai search and term-return links; long-table keyboard scrolling at 390 and 320 px; offline expanded content and search. Evidence: `qa/output/depth-results.json`.
- Visual inspection covered the multi-period CPPI table on desktop/mobile and the continuous cushion equation. Existing light/dark reading layout, branding, labs and downloads are preserved.

This revision is local; repository publication remains undecided. Source PDF and temporary research/drafts are excluded from Git. Safari/Firefox and full screen-reader narration remain untested.

## 2026-09-13 — Narrative voice pass

Adjusted five Welcome passages and 27 lesson passages to connected, natural Thai explanation. All 378 math expressions, 129 table rows, headings, numeric tokens, source/term links and 19 explicit chapter anchors remain unchanged. All 17 Notebook code cells and saved outputs match the preceding revision exactly.

Regenerated the Notebook; complete chapter capture, re-execution and 16 Python/JavaScript comparisons passed. The build and 264 local-reference checks passed. A focused browser check confirmed the revised copy, no page overflow at 1440/390 px, and no KaTeX errors. Publication status remains local.

## 2026-09-13 — Four explanatory teaching figures

- Added editable Excalidraw anatomy, rebalance, gap-risk and TIPP scenes with self-contained SVG exports. The supplementary reference is the supplied QUANTSERAS slide deck, PDF pp. 56–60. Examples keep the chapter's existing hypothetical values.
- All four scenes passed the Excalidraw validator and visual quality gate. Independent numeric review confirmed proportional geometry, portfolio totals, asset trades, floor levels and TIPP observations.
- Inspected all four rendered figures and mobile website captures. Focused browser checks passed 24 figure/viewport/theme combinations (1440, 390, 320 pixels; light/dark), with no clipping, page overflow or runtime errors. All four images also loaded from the exported local HTML while offline.
- `npm run check:site`: 32 passed, zero failures, including 18 accessibility scans. The harness now scrolls to lazy-loaded lesson diagrams and waits for decoding before asserting that images loaded.
- `npm run notebook` and `npm run check:notebook`: 36 cells, 17 executed code cells, two calculated SVG charts and four SVG Markdown attachments. Each attachment matches its asset byte for byte; all 16 Python/JavaScript path comparisons passed. Original code cells and saved outputs are unchanged.
- `npm run build:pages`: three book pages, six HTML files, 111 search entries and 268 local references passed. Original mathematical expressions are unchanged. `git diff --check` passed.
- Evidence remains local in `qa/output/figure-layout-results.json`, `qa/output/browser-results.json`, figure screenshots and Excalidraw session state. The original quantitative-finance-notes working tree remains clean.
- This remains the local preview; no source PDF or scene was uploaded externally. Safari/Firefox and full screen-reader narration were not tested.

## Variable-Multiplier extension — 2026-09-19

Added a CPPI subsection, one glossary entry, source attribution and an executable Notebook example. The inverse-volatility rule and parameters are explicitly authored teaching assumptions, separate from the cited Mahayni/Zieling/Balder research and the fixed-m browser simulator.

Verification: regenerated 36-cell Notebook with 17 executed code cells; complete chapter/model consistency and 16 Python/JavaScript comparisons passed. New analytic checks cover the three volatility snapshots, multiplier bounds, one-period gains/losses, the 0.75-unit rebalance sale, a floor-breaching gap and invalid volatility inputs. Build/link checks passed 274 local references. Browser suite passed 32 checks; targeted checks also confirmed the new anchor at 1440/390/320px without document overflow, the new glossary filter/return link and global search. `git diff --check` passed.
