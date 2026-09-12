# Verification record

Date: 2026-09-12. Local macOS Chromium. Node.js 22.22.3.

- `npm test`: 16 numerical checks passed, including analytic portfolio paths, gap risk and cash lock, rate/floor consistency, no lookahead, exposure caps, payoff/profit separation and CSV consistency.
- `npm run build:pages`: five main pages built; 221 local asset/link references checked including anchors and CSS fonts. Source HTML contains no duplicate IDs.
- `npm run check:site`: 41 browser checks passed. Thirty page scans cover five pages at 1440, 390 and 320 pixels in dark/light themes. No document overflow, serious/critical axe findings, color-contrast violations, runtime errors, missing resources or external font requests were detected.
- Interaction coverage: English/Thai search, no results, Escape and focus restoration, section anchors, theme persistence, mobile navigation, four CPPI scenarios, sliders and keyboard control, 13 data observations, saving/recalling up to six runs, exact exported CSV, Put metrics and minimum premium bound, three-step walkthrough, all four React Bits families and reduced motion.
- Separate offline check with network disabled: local file opening, home chart, search and CPPI scenario switching passed.
- Visual inspection: desktop and mobile overview and strategy lab, in both themes. Evidence: `qa/output/` (local only).
- Source review: thesis strategies and findings checked against the local PDF; the two CPT score scenarios were checked visually against Table 5.2 Panel C, printed p. 90 / PDF p. 117. Citations distinguish thesis evidence from the toolkit's original examples.
- `git diff --cached --check` passed before the local commit. The original quantitative-finance-notes working tree was left clean.

Limitations: no real market backtest, no claim of reproducing the thesis's full Monte Carlo experiments, and no tests of live trading. Safari/Firefox and full screen-reader narration were not tested. Initial delivery is local; hosting requires a separate publication decision.
