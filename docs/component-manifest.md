# Interaction and asset manifest

Created before implementation: 2026-09-12.

Visual route: `no-image-generator` under `visual-generation/Nuth-v1`.
Controlling system: QuantCorner / QuantSeras, exact Material Design 2;
dark primary and light supporting, local Roboto / Noto Sans Thai / Roboto Mono.

## Planned React Bits families

| Family | Semantic purpose and location | Trigger | Reduced motion / static equivalence |
| --- | --- | --- | --- |
| CountUp | Shows the result of a portfolio calculation in result metrics | Calculated value changes | Final value immediately; screen readers always receive the final value, never interpolation |
| Stepper | Three-stage learning sequence: define protection, allocate risk, review outcomes | Reader chooses Back, Next, or a named stage | Same named native buttons, progress and content, without transition |
| AnimatedList | Saved scenario history with recall | A saved run is appended; reader recalls a run | Same ordered list and native recall buttons, with new rows visible immediately |
| BlurText | One narrative headline connects the opening question to the research | Headline first enters view | Identical headline rendered statically and available to screen readers immediately |

Each family must render in a visible user state before being counted. Four
families are planned for this research toolkit. No repeating or idle effects.

## Sourcing and adaptation

The official shadcn MCP was called first. Its initial `@react-bits` search
returned `NOT_CONFIGURED`; this project now declares the official registry in
`components.json`. Registry inspection and pinned-source details will be
recorded below before implementation.

Both the search and item-detail MCP calls returned `NOT_CONFIGURED`, including
after this new project's registry configuration was created. The MCP server
is not reading the new sibling project configuration. The approved local
fallback is therefore used: verified Git HEAD
`8d1c5fa9ebee6e077e70c9e5c63b44e87dbeaecc`. Inspected the complete JS/CSS
source for all four families and their `public/r/*-JS-CSS.json` registry
snapshots before implementation. Each snapshot declares only
`motion@^12.23.12`; this project pins the installed runtime in its lockfile.
The four individual source snapshots are retained in `vendor/` for
application provenance, together with the MIT + Commons Clause notice.

Presentation is scoped to `src/components/components.css`, using semantic
`--rb-*` adapters mapped to the application tokens. No upstream demonstration
palette, decorative gradients or glow. The approved QuantCorner mark remains
an unchanged authentic file, including its approved green evidence point.

## Verification status

Implementation complete in `src/components/`. All four entrypoints passed an
independent esbuild browser bundle with the project's installed React 19.2.6
and Motion 12.43.0. shadcn's audit checklist was retrieved after implementation.
All icons were validated as SVGs with a 24px viewBox and 2px stroke. Exact
source/font/brand checksums and icon URLs are retained in `vendor/` and
`assets/icons/source.json`. Full licenses are retained.

Component CSS contains only semantic variable references and approved Material
2 fallback colors; upstream neon literals and gradients have been removed.
Reduced motion has both runtime and CSS static fallbacks. Native Tab order is
preserved; optional scenario-list arrow navigation is scoped to that list.

Integrated browser verification completed on 2026-09-12: `npm run check:site`
passed 41 checks. All four families render and perform their stated functions.
Thirty page scans (five pages x 1440/390/320px x dark/light) found no page
overflow, serious/critical accessibility findings, contrast violations, missing
assets, or runtime errors. Keyboard, saved-run recall, all three steps, live
metric updates, single headline reveal and static reduced-motion behavior
passed. Exact evidence and eight screenshots are in `qa/output/`.

## Integration API

- `CountUp({to, digits = 2, className = ''})`: numeric output; callers supply
  the metric's label and unit. The final value is available immediately through
  a visually hidden span, while interpolation is hidden from screen readers.
- `Stepper({children})`: three stage bodies; optional `data-step-title` on each
  child overrides the default stage label. Back, Next, and numbered stage
  buttons are native keyboard controls. The panel uses natural height.
- `AnimatedList({items, onItemSelect})`: items have stable `id` and `label`;
  callback receives `(item, index)`. New rows reveal once, saved history can be
  recalled, and the empty state explains how to begin.
- `BlurText({text, className = ''})`: inline text, suitable inside the caller's
  `h1` or `h2`. Use once per narrative view.
- Import `src/components/components.css` once. It maps `--rb-*` to app tokens
  `--background`, `--surface`, `--text`, `--muted`, `--primary`, `--on-primary`,
  `--secondary` and `--border`. App tokens control the light theme as well.
