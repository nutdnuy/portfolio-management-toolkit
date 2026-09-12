# Publishing the independent toolkit

This is a standalone site. Do not deploy it into the quantitative-finance-notes repository or replace that site's root.

The local build exports `_site/`, with relative links, bundled fonts and JavaScript. No private PDF, `.research/`, source clone, credentials or local configuration belongs in the deployment artifact.

## GitHub Pages

The included **Publish toolkit** workflow installs locked dependencies on Node.js 22, runs numerical and executed-Notebook consistency checks, builds three book pages, checks local assets and anchors, uploads `_site/` and deploys Pages. The downloadable Notebook is committed; regenerate it locally when its chapter or model changes.

After the owner chooses publication:

1. Create a separate repository named `portfolio-management-toolkit` under the chosen account; confirm intended visibility before creating a public repository.
2. Push this project's `main` branch to that new repository.
3. Set Settings → Pages → Source to GitHub Actions.
4. Run or inspect **Publish toolkit**. Verify both deployment status and live page before reporting publication.

No hosted repository or live URL has been configured at initial local delivery. No DNS changes are required for the account's standard GitHub Pages path.

Documentation: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
