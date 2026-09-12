# Sources and third-party notices

## Interface interactions

CountUp, Stepper, AnimatedList, and BlurText are adapted from
[DavidHDev/react-bits](https://github.com/DavidHDev/react-bits), pinned commit
`8d1c5fa9ebee6e077e70c9e5c63b44e87dbeaecc`. The individual JS/CSS registry
snapshots are retained in `vendor/*-JS-CSS.json` as source provenance for this
website. They are not offered as an independent component library or template
pack. Copyright © 2026 David Haz; MIT + Commons Clause License Condition v1.0
is retained in `vendor/react-bits-LICENSE.txt`.

The official shadcn MCP was attempted first; both search and detail requests
reported that `@react-bits` was not configured in its active project. The new
toolkit declares that registry in `components.json`, but the running MCP did
not read the sibling project's configuration. The governed pinned local source
was inspected and used as the reproducible fallback.

Adaptations replace upstream demonstration colors with QuantCorner / QuantSeras
Material 2 semantic tokens; make reduced motion static; keep final numeric
values immediately readable to assistive technology; use native buttons and
ordered lists; remove document-wide keyboard interception; allow content to
determine step height; and retain accessible, stable text for the one narrative
headline reveal. See `docs/component-manifest.md` for purpose and verification.

React, React DOM, Scheduler, Motion, and its bundled dependencies retain their
package license notices in `vendor/`. Exact installed versions are recorded in
`vendor/runtime-versions.json` and `package-lock.json`. KaTeX is used for native
HTML / MathML equations and retains its MIT notice in `vendor/katex-LICENSE.txt`.

## Fonts

Roboto, Roboto Mono, and Noto Sans Thai are local Fontsource 5.2.8 assets copied
unchanged from the existing Quantitative Finance Notes project. Font licenses
are retained in `assets/fonts/`; the existing version verification is retained
in `vendor/font-provenance.json`. Font bytes and individual component snapshots
are hashed in `vendor/asset-checksums.json`. The website does not request fonts
from an external service.

## Icons

The following authentic [Tabler Icons](https://github.com/tabler/tabler-icons)
outline SVGs are fetched at governed commit
`6d128ed935d4546607b1e4d5d08c8b27bdbe7758`: `book`, `chart-line`, `shield-check`,
`arrow-up-right`, `chevron-right`, `sun`, `moon`, `menu-2`, `x`, `download`,
`search`, and `external-link`.

Source files retain the native 24px grid, 2px stroke and `currentColor`. Runtime
adaptation is limited to sizing, semantic color, and accessibility attributes.
Exact source URLs and SHA-256 hashes are in `assets/icons/source.json`. The MIT
license is retained in `vendor/tabler-LICENSE.txt`.

## Approved brand assets

QuantCorner Research Coordinate Q marks and favicons are authentic owner
approved assets copied unchanged from the canonical QuantCorner brand package.
Its rules are retained in `assets/brand/README.md`. The mark's approved green
evidence point is preserved as part of the logo; it is not a new UI palette.
Dark and light marks are selected for their appropriate surface. These
owner-controlled marks are not offered under the software dependency licenses.

## Visual production

The website, interface, and calculated charts follow `no-image-generator`
under `visual-generation/Nuth-v1`, controlled by the QuantCorner / QuantSeras
Design System. All rendered text, values, chart geometry, controls and layouts
are native or deterministic. No generated artwork or decorative image filler
is included in this work.

## Educational source

Paulo José Martins Jorge da Silva, *Portfolio Insurance Strategies: Friend or Foe?* (2018), doctoral thesis, Universidade de Lisboa / ISEG. Public repository: https://hdl.handle.net/10400.5/16515. The user-provided 169-page PDF was consulted locally. Original Thai teaching notes summarize its concepts and findings with printed/PDF page citations. Two selected scenarios from Table 5.2 Panel C (printed p. 90, PDF p. 117) are transcribed and labeled as CPT scores, not returns. No source PDF or original chart image is redistributed. Author and university rights remain with their owners.

All toolkit market paths and worked examples are newly constructed teaching examples. The monthly CPPI simulation is not a replication of the thesis Monte Carlo study. See content/research.md and docs/methodology.md for scope.
