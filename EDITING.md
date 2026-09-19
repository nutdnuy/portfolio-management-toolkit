# Editing the book

Edit `content/*.md`, never generated `_site/` files. The book uses the same light reading layout as Quantitative Finance Notes, but has its own content, configuration and build.

## Book identity

Set the book title, author and the two ordered logo paths in `site.config.json`. Keep the Welcome heading in `content/index.md` and Notebook introduction in `scripts/make_notebook.py` consistent with the title. The approved logos are immutable PNGs; `book.css` aligns their painted bounds without modifying the assets.

## Chapters

Use an English kebab-case filename in `content/`. Add its name without `.md`, a title and description to `pages` in `site.config.json`. Markdown headings form the chapter contents list. Explicit section IDs remain stable for glossary links and bookmarks. Equations use inline `$...$` and display `$$...$$` LaTeX rendered by KaTeX.

Write a learning question, introduce unfamiliar terms, calculate a concrete example, and then explain the formula and its assumptions. Use natural, connected Thai prose that walks through the reasoning with the reader. Prefer concrete verbs and short explanations to report-like phrasing; use “เรา” when useful, without inserting the assistant’s name or conversational particles. Preserve the depth, assumptions and evidence when smoothing the prose. Distinguish hypothetical teaching examples from thesis evidence. Keep printed and PDF page references traceable. Do not bundle the source PDF.

## Interactive sections

The Portfolio Insurance chapter mounts three components: `put-lab`, `allocation-guide` and `cppi-lab`. Their order follows the surrounding explanation. Edit calculations in `src/math.mjs`, application controls in `src/app.jsx`, and shared behavior in `src/site.js`. Do not insert independent landing pages or dashboard navigation into the book.

The scenarios are twelve authored monthly returns, not empirical data. Keep units, rates, terminal floor, initial funding and payoff/profit distinctions consistent between prose, browser, CSV and Notebook.

## Notebook and checks

Run `npm run notebook` after changing the chapter or numerical source. The generator captures the complete canonical chapter, inserts executable Python examples, and runs every code cell. It needs Python 3.9+ standard library. It overwrites only `notebooks/portfolio-insurance.ipynb`; keep personal experiments under separate filenames.

Run `npm test`, `npm run check:notebook` and `npm run build:pages`. Layout or interaction changes also need `npm run check:site` with the preview on port 8764. Check desktop, mobile, light/dark themes, keyboard controls, Thai/English search, glossary anchors and local-file opening. Review `git diff --check` before committing.

Run `npm run dev` to preview and rebuild on source changes, then refresh the browser. The generated `_site/` folder includes fonts, equations, JavaScript, Markdown downloads and the Notebook for offline use.

## Return chapter

Edit `content/returns.md`. The title is **How to Calculate return**. This introductory lesson uses prose, equations and worked examples without Python or a Notebook. The central case starts at THB 1,000,000, gains 100% in year one, then loses 50% in year two. Keep the lesson independent of Portfolio Insurance. Per-page `notebook: false` in `site.config.json` hides the sidebar download; an omitted value retains the site default. Source notes are in `data/returns-provenance.json`.

Return illustrations are deterministic SVGs in `assets/charts/`, generated with `node scripts/make_returns_figures.mjs`. The interactive lesson uses `src/returns.jsx`, `src/returns.css` and `src/returns-math.mjs`, bundled only on `returns.html`. Sliders use simple returns from -95% to +200%; logs remain decimals and calculations use unrounded values. Verify with `node qa/returns-checks.mjs`, `npm run build:pages` and `node qa/returns-browser-checks.cjs` while the preview runs on port 8764. No Python or Notebook is part of the Return lesson.

## Historical insurance charts

Regenerate the four S&P 500 wealth and drawdown comparisons with `python3 scripts/make_sp500_charts.py .research/sp500-2016-2025.csv`, using the locally held input whose checksum is pinned in `data/sp500-results.json`. The generator checks annual endpoints and the Buy & Hold telescoping identity before writing `assets/charts/sp500-*.svg` and aggregate metadata in `data/sp500-charts.json`. Raw quotes remain local. The paths compound the annual experiments, with a new 90% floor and renewed allocation at each year boundary; TIPP resets its high-water mark and SLPI re-enters. This differs from an eight-year fixed floor. Every wealth SVG uses all daily observations, a calendar-date x axis and the same linear 0–300 wealth axis. Responsive picture elements select the mobile export; Notebook attachments use the desktop export. Regenerate the Notebook after changes.

Drawdown charts use `100 * (wealth / own running peak - 1)` over the entire chained 2018–2025 path, including inception. Their running peak never resets at year boundaries. All four use the same −40% to 0% axis; labels report Maximum drawdown as a positive magnitude, without annualization. Validate every plotted drawdown against the corresponding wealth SVG, and regenerate all 16 desktop/mobile SVGs plus the Notebook.


## Risk lesson

Edit `content/risk.md`. Place the definition, history and theoretical questions before the practical risk measures. There is no single inventor of investment risk. Markowitz and Roy are distinct contributions from 1952; CAPM describes expected returns under assumptions, not guaranteed realized returns. The RiskMetrics source is J.P. Morgan/Reuters's December 1996 fourth edition, hosted by MSCI, not a current market report.

All examples are hypothetical. `data/risk-provenance.json` records references and conventions. Keep sample volatility (`n-1`), downside deviation (all observations in denominator), signed drawdowns with positive MDD, inverse-ECDF VaR and exact worst-tail-mass ES explicit. Do not replace the ES implementation with averaging every loss greater than or equal to VaR when there are ties. The EWMA illustration conditions on the observed shock; subsequent zero residuals are an imposed demonstration, not a price forecast.

The three labs use `src/risk.jsx`, `src/risk.css` and `src/risk-math.mjs`. Charts are computed SVGs and follow the existing no-image-generator route. The Risk page has no Notebook; it has a downloadable Markdown source. Run `npm test`, `npm run build:pages` and `node qa/risk-browser-checks.cjs` with the preview on port 8764. The full `npm run check:site` includes the risk and returns interactions. Existing insurance Notebook content is independent and does not need regeneration for risk-only edits.
