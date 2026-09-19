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

Edit `content/returns.md` and run `python3 scripts/make_returns_notebook.py` to regenerate and execute `notebooks/returns.ipynb`. The title is **How to Calculate return**. Keep this introductory lesson independent of Portfolio Insurance. Per-page `notebook` in `site.config.json` overrides the sidebar download; other pages retain the site default. Source notes are in `data/returns-provenance.json`.
