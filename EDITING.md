# Editing the book

Edit `content/*.md`, never generated `_site/` files. The book uses the same light reading layout as Quantitative Finance Notes, but has its own content, configuration and build.

## Chapters

Use an English kebab-case filename in `content/`. Add its name without `.md`, a title and description to `pages` in `site.config.json`. Markdown headings form the chapter contents list. Explicit section IDs remain stable for glossary links and bookmarks. Equations use inline `$...$` and display `$$...$$` LaTeX rendered by KaTeX.

Write a learning question, introduce unfamiliar terms, calculate a concrete example, and then explain the formula and its assumptions. Distinguish hypothetical teaching examples from thesis evidence. Keep printed and PDF page references traceable. Do not bundle the source PDF.

## Interactive sections

The Portfolio Insurance chapter mounts three components: `put-lab`, `allocation-guide` and `cppi-lab`. Their order follows the surrounding explanation. Edit calculations in `src/math.mjs`, application controls in `src/app.jsx`, and shared behavior in `src/site.js`. Do not insert independent landing pages or dashboard navigation into the book.

The scenarios are twelve authored monthly returns, not empirical data. Keep units, rates, terminal floor, initial funding and payoff/profit distinctions consistent between prose, browser, CSV and Notebook.

## Notebook and checks

Run `npm run notebook` after changing the chapter or numerical source. The generator captures the complete canonical chapter, inserts executable Python examples, and runs every code cell. It needs Python 3.9+ standard library. It overwrites only `notebooks/portfolio-insurance.ipynb`; keep personal experiments under separate filenames.

Run `npm test`, `npm run check:notebook` and `npm run build:pages`. Layout or interaction changes also need `npm run check:site` with the preview on port 8764. Check desktop, mobile, light/dark themes, keyboard controls, Thai/English search, glossary anchors and local-file opening. Review `git diff --check` before committing.

Run `npm run dev` to preview and rebuild on source changes, then refresh the browser. The generated `_site/` folder includes fonts, equations, JavaScript, Markdown downloads and the Notebook for offline use.
