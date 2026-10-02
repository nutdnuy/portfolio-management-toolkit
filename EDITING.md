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

Edit `content/returns.md`. The title is **How to Calculate return**. This introductory lesson now introduces finance and Python from zero, following Module 1 (Analysing returns) of the EDHEC Coursera course. Use original Thai explanations and hypothetical examples; retain the optional log-return extension. Short inline Python examples must explain inputs, syntax, output, units and assumptions, and run sequentially without course CSV dependencies. The central case starts at THB 1,000,000, gains 100% in year one, then loses 50% in year two. Keep the lesson independent of Portfolio Insurance. Per-page `notebook: false` in `site.config.json` hides the sidebar download; an omitted value retains the site default. Source notes are in `data/returns-provenance.json`.

Return illustrations are deterministic SVGs in `assets/charts/`, generated with `node scripts/make_returns_figures.mjs`. The interactive lesson uses `src/returns.jsx`, `src/returns.css` and `src/returns-math.mjs`, bundled only on `returns.html`. Sliders use simple returns from -95% to +200%; logs remain decimals and calculations use unrounded values. Verify with `node qa/returns-checks.mjs`, `npm run build:pages` and `node qa/returns-browser-checks.cjs` while the preview runs on port 8764. Inline Python is part of the Return lesson; there is no separate Returns Notebook. Execute every fenced Python example in a fresh namespace when editing these examples. Keep the original course transcripts and notebooks local. Respect the distinctions recorded in `data/returns-provenance.json`, especially Sharpe, semideviation, empirical VaR/ES and initial-capital drawdown. Preserve legacy heading anchors when reorganizing sections.

## Historical insurance charts

Regenerate the four S&P 500 wealth and drawdown comparisons with `python3 scripts/make_sp500_charts.py .research/sp500-2016-2025.csv`, using the locally held input whose checksum is pinned in `data/sp500-results.json`. The generator checks annual endpoints and the Buy & Hold telescoping identity before writing `assets/charts/sp500-*.svg` and aggregate metadata in `data/sp500-charts.json`. Raw quotes remain local. The paths compound the annual experiments, with a new 90% floor and renewed allocation at each year boundary; TIPP resets its high-water mark and SLPI re-enters. This differs from an eight-year fixed floor. Every wealth SVG uses all daily observations, a calendar-date x axis and the same linear 0–300 wealth axis. Responsive picture elements select the mobile export; Notebook attachments use the desktop export. Regenerate the Notebook after changes.

Drawdown charts use `100 * (wealth / own running peak - 1)` over the entire chained 2018–2025 path, including inception. Their running peak never resets at year boundaries. All four use the same −40% to 0% axis; labels report Maximum drawdown as a positive magnitude, without annualization. Validate every plotted drawdown against the corresponding wealth SVG, and regenerate all 16 desktop/mobile SVGs plus the Notebook.


## Risk lesson

Edit `content/risk.md`. Place the definition, history and theoretical questions before the practical risk measures. There is no single inventor of investment risk. Markowitz and Roy are distinct contributions from 1952; CAPM describes expected returns under assumptions, not guaranteed realized returns. The RiskMetrics source is J.P. Morgan/Reuters's December 1996 fourth edition, hosted by MSCI, not a current market report.

All examples are hypothetical. `data/risk-provenance.json` records references and conventions. Keep sample volatility (`n-1`), downside deviation (all observations in denominator), signed drawdowns with positive MDD, inverse-ECDF VaR and exact worst-tail-mass ES explicit. Do not replace the ES implementation with averaging every loss greater than or equal to VaR when there are ties. The EWMA illustration conditions on the observed shock; subsequent zero residuals are an imposed demonstration, not a price forecast.

The three labs use `src/risk.jsx`, `src/risk.css` and `src/risk-math.mjs`. Charts are computed SVGs and follow the existing no-image-generator route. The Risk page has no Notebook; it has a downloadable Markdown source. Run `npm test`, `npm run build:pages` and `node qa/risk-browser-checks.cjs` with the preview on port 8764. The full `npm run check:site` includes the risk and returns interactions. Existing insurance Notebook content is independent and does not need regeneration for risk-only edits.


Risk visual additions (2026-09-20): the owner explicitly requested generated imagery. `assets/illustrations/risk-uncertain-futures.png` is a conceptual AI illustration, with prompt and provenance in `data/`; this is a scoped exception to the website's default visual route. Never treat the illustration as data. The P/Q and correlation figures remain deterministic: regenerate desktop/mobile SVGs with `node scripts/make_risk_figures.mjs`. Keep scenario probabilities, SD convention, axes and explanatory captions aligned with the lesson.


## Extreme Risk continuation

Edit `content/extreme-risk.md`, placed after Returns. This is a beginner expansion of Module 1 Section 2, with original hypothetical examples; keep the Returns overview and legacy anchors intact. Provenance is in `data/extreme-risk-provenance.json`. Use population moments (`ddof=0`) for skewness/kurtosis and distinguish these from sample volatility. Normality test outputs do not prove Normality or independence. Keep the three semideviation conventions distinct. Historical VaR is the loss inverse-ECDF; ES allocates exactly the worst-tail mass, including fractional boundary weights.

`examples/extreme-risk/finance_tools.py` is the original downloadable module. Its complete displayed Python block must match the file; do not copy the private course toolkit. `scripts/make_extreme_risk_figure.mjs` generates both responsive hypothetical histogram SVGs. Run `npm run check:extreme` (dependencies pinned in `qa/extreme-risk-requirements.txt`), `npm run build:pages` and `npm run check:site`. The Python check runs all fenced examples in source order and verifies independent analytical values; browser checks cover the new page and figures. The insurance Notebook is independent and does not need regeneration for edits to this chapter.


## Course continuation: Modules 2–4

The ten new pages are selected by `module: 2`, `3` or `4` in `site.config.json`. `lesson` is the within-module reading order; `group` supplies the sidebar label. The builder adds previous/next links from configured page order. Keep these chapters in that order unless the owner asks to reorganize. Each has its own complete executed notebook, and no page depends on another chapter's Python namespace.

Edit the canonical Markdown in `content/`, then run `npm run notebook:course`, `npm run check:course`, `npm run build:pages` and `npm run check:site`. `scripts/make_course_notebooks.py` runs every Python fence in source order, captures stdout and embeds calculated SVG figures as notebook attachments. It replaces only the configured course notebooks matching the optional `--course` and `--module` filters. Use `--course introduction` for the ten Introduction notebooks. The check compares every cell and attachment, pins the Markdown hash and allows small numeric differences in stdout across operating systems. Preserve separately named reader experiments.

The original hypothetical inputs and authored CPPI path are documented in `data/course-provenance.json` and `data/course-figures.json`. Generate the eight desktop/mobile SVGs with `python3 scripts/make_course_figures.py`. Keep inputs and plotted coordinates consistent with the lesson. Existing insurance charts and notebook are independent. Course transcripts, local instructor notebooks and toolkit copies stay outside Git.

Preserve these distinctions: arithmetic mean versus CAGR; upper efficient frontier versus the lower minimum-variance boundary; CAL versus equilibrium CML; solver convergence versus estimation quality; pre-period weights and prices versus future data; exact exponential GBM versus Euler gross-return approximations; cash versus a bond matched to a dated liability; annual-effective yield versus instantaneous short rate; physical probabilities versus risk-neutral pricing; Macaulay versus modified duration; price return versus coupon-inclusive total return; terminal versus pathwise breaches; conditional versus unconditional deficits. Discrete CPPI and goal-based floors do not establish guarantees.

Use the owner's requested `no-ai-slop` editorial pass after reading a full draft. Preserve concrete calculations, units, code explanations and limitations while removing empty emphasis, generic introductions, decorative bold and repeated recap endings. The public lesson voice remains impersonal Thai. The related glossary entries have stable IDs in the `group-portfolio-construction` and `group-asset-liability` groups.

## Advanced course, starting with Module 1

Advanced pages use `course: "advanced"`, module number, lesson number and their own unique Markdown/Notebook filenames. Introduction pages have explicit `course: "introduction"`. Preserve the global book reading order and Advanced labels in sidebar, page kicker and search. Module 1 has four chapters: `factor-investing`, `multifactor-models`, `style-analysis`, `smart-beta`.

Export with `python3 scripts/make_course_notebooks.py --course advanced --module 1`. Run `npm run check:advanced` for source/Notebook consistency and independent numeric tests, then build/link and browser checks. Introduction checks remain isolated in `npm run check:course`. To refresh computed charts, run `python3 scripts/make_advanced_figures.py` before exporting notebooks.

Keep realized attribution separate from expected-return pricing; loadings from weights; factor spreads from total returns; monthly intercept from CAGR; variance tracking error from raw residual RMS; conditional held-out attribution from a forecast; independent regressors from independent random factors; capital concentration from risk contributions; pre-period weights from future prices; one-way turnover from two-sided fee bases. RBSA here defaults to centered residual variance with an intercept; the course lab uses a raw squared-error norm, so the separate raw-MSE comparison must stay explicit.

The original public optional ZIP loader reads only BRKA daily returns and the monthly FF3 file, compounds within calendar month, aligns 348 observations and subtracts RF once from the asset. Publish aggregates, hashes and conventions only. Do not silently replace the 201812 source snapshot with newer French downloads or add private ZIP paths to public code.
