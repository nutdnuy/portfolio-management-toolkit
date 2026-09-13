# Portfolio insurance teaching diagrams

The editable `.excalidraw` scenes are the source of the four SVGs. These are original numerical teaching diagrams, not reproductions of the supplied PDF pages. No Image Generator or external sharing service was used.

| Diagram | Teaching point | Numerical fixture |
| --- | --- | --- |
| `cppi-anatomy` | Target floor versus actual holdings | 100 = 90 + 10 = 70 + 30; m = 3 |
| `cppi-rebalance` | Price movement precedes the trade | E30/B70 → E27/B70 → E21/B76; total 100 → 97 → 97 |
| `cppi-gap` | Selling does not replenish a breached floor | E30/B70 → E18/B70 → E0/B88; floor 90 |
| `tipp-ratchet` | The observed high-water mark keeps the floor raised | V100/106/102.82; F90/95.4/95.4; E30/31.8/22.26 |

All values are hypothetical monetary units. Interest and transaction costs are zero; fractional holdings are allowed, with no borrowing or shorting. TIPP uses 90% of its own observed portfolio high-water mark. Its connecting lines do not describe unobserved prices. Neither diagram establishes a market guarantee or an optimal multiplier.

CPPI anatomy uses a shared zero baseline and 3 pixels per unit. Allocation flows use 5.2 pixels per unit in every row. The TIPP line chart has a declared 80–110 scale and 8 pixels per unit.

After editing a scene, run `python3 scripts/export_diagrams.py` from the project root, then rebuild the Notebook and website. The exporter supports unrotated rectangles, ellipses, text, lines and single-ended arrows; it raises an error for unsupported primitives. SVG geometry and labels are read directly from each scene. Excalidraw uses its editable sans-serif family, while the SVG embeds the website's existing Roboto and Noto Sans Thai fonts. Font licenses remain in `assets/fonts/` and `THIRD_PARTY_NOTICES.md`.

The supplementary conceptual source is *Dynamic Portfolio Management*, QUANTSERAS, supplied as *Quant Winter s.pdf*, PDF pages 56–60. The slides' sample allocation is not the numeric fixture used here. Full provenance is in `data/provenance.json`; the source PDF is not included.

The Notebook embeds all four SVGs verbatim as Markdown attachments, so a separately downloaded Notebook needs no companion image folder. Website captions and alt text are maintained in `content/portfolio-insurance.md`.

Local Excalidraw session state is kept under `qa/output/excalidraw-state/`; the committed scenes in this directory remain canonical.
