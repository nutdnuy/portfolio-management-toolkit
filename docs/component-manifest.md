# Book interaction and asset manifest

Date: 2026-09-12. Visual route: `no-image-generator` under `visual-generation/Nuth-v1`.

The owner selected the light Thai book layout of the Binomial Model lesson. The book uses native text and equations, a left contents column, inline experiments, print and Notebook downloads. Light is the default; readers may choose dark. QuantCorner / QuantSeras Material 2 tokens and local Roboto / Noto Sans Thai / Roboto Mono fonts are retained.

## Three component families

| Family | Purpose and location | Trigger | Reduced motion / static equivalence |
| --- | --- | --- | --- |
| CountUp | Numeric results in the Put and CPPI inline experiments | Calculated value changes | Final value immediately; screen readers receive the final value rather than interpolation |
| Stepper | Three stages of the worked allocation example | Native stage, Back and Next buttons | Identical named controls, progress and content without transition |
| AnimatedList | Up to six saved CPPI assumptions with recall | Saving or recalling a run | Same ordered list and native recall buttons, with new rows visible immediately |

No headline reveal, idle animation or marketing components are rendered. Each family is exercised in a visible user state by browser checks. Updated evidence is in `docs/verification.md` and local `qa/output/`.

## Source and adaptation

The official shadcn MCP search and detail calls returned `NOT_CONFIGURED`, including after this sibling project's registry declaration in `components.json`. The approved local fallback used verified React Bits Git HEAD `8d1c5fa9ebee6e077e70c9e5c63b44e87dbeaecc`. Complete JS/CSS source and registry snapshots were inspected before adaptation. Snapshots and the MIT + Commons Clause notice are retained in `vendor/`. BlurText was inspected in the initial work but is not used in the book.

Only semantic `--rb-*` adapters appear in component styling, mapped to the application's Material 2 tokens. Upstream demonstration palettes and gradients are removed. Runtime and CSS reduced-motion fallbacks preserve content. Native Tab order is retained; arrow navigation is limited to the saved-run list.

The Tabler icon source URLs, SVG checksums and authentic 24px/2px construction are recorded in `assets/icons/source.json`. Font and owner-approved brand asset checksums and licenses are retained in `vendor/` and `assets/`. The book shell is reused from the owner's Quantitative Finance Notes layout. The sidebar's CPPI/recovery thumbnail is deterministic output of `build.cjs`.

## Integration API

- `CountUp({to, digits = 2, className = ''})`: callers supply label and unit. Final text is available immediately through a visually hidden span; interpolation is hidden from screen readers.
- `Stepper({children})`: three stage bodies, with optional `data-step-title`. Native stage and navigation buttons; natural panel height.
- `AnimatedList({items, onItemSelect})`: items contain stable `id` and `label`; callback receives `(item, index)` for recall.
- Import `src/components/components.css` once. Application tokens control both themes.
