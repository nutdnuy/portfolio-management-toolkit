# Publishing Portfolio Management Toolkit Notes

Repository: <https://github.com/nutdnuy/portfolio-management-toolkit>

Public book: <https://nutdnuy.github.io/portfolio-management-toolkit/>

Portfolio Insurance chapter: <https://nutdnuy.github.io/portfolio-management-toolkit/portfolio-insurance.html>

The owner authorized this public repository and GitHub Pages on 2026-09-13. This is a standalone site; deployment does not replace Quantitative Finance Notes. No custom domain or DNS change is required.

## Automatic publication

The repository uses `main` and Settings → Pages → Source: **GitHub Actions**. The **Publish toolkit** workflow installs locked dependencies on Node.js 22, runs numerical and executed-Notebook consistency checks, builds the book, checks local assets and anchors, then uploads `_site/` and deploys Pages.

1. Edit the canonical Markdown, scripts or assets. Regenerate the Notebook when its chapter, calculations or diagrams change.
2. Run the relevant checks described in `EDITING.md` and `git diff --check`.
3. Commit and push to `main`.
4. Inspect [Publish toolkit runs](https://github.com/nutdnuy/portfolio-management-toolkit/actions/workflows/publish.yml). Wait for the build and deployment jobs to succeed.
5. Verify the live pages, images, relative asset paths and Notebook download before reporting an update as public.

Pull requests build and validate the site; only `main` publishes. The workflow also supports manual dispatch.

## Publication contents

The exported `_site/` uses relative links and bundles the fonts, JavaScript, diagrams, editable Excalidraw files, licenses, Markdown downloads and executed Notebook. Do not edit generated output directly.

Private source PDFs, `.research/`, credentials, dependencies, local configurations and temporary QA files remain excluded from Git and the deployment artifact. The source documents are referenced in the lesson and provenance records; they are not redistributed.

Documentation: <https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages>
