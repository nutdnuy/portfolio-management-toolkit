"""Execute the original Module 2–4 examples and export complete lesson notebooks.

Each chapter gets a fresh namespace. Only explicitly configured course pages
are exported; existing insurance notebooks and personal experiments are untouched.
"""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://nutdnuy.github.io/portfolio-management-toolkit/"


def course_pages():
    config = json.loads((ROOT / "site.config.json").read_text())
    return [p for p in config["pages"] if p.get("module") in (2, 3, 4)]


def markdown_cell(text, index):
    # Keep published local links useful in a separately downloaded notebook.
    text = re.sub(r'(?<=href=")(?!(?:https?:|#))([^\"]+)', lambda m: BASE + m[1], text)
    text = re.sub(r'\]\((?!https?:|#|attachment:)([^)]+\.(?:html|ipynb)(?:#[^)]*)?)\)', lambda m: "](" + BASE + m[1] + ")", text)
    text = re.sub(r'<nav class="chapter-navigation"[\s\S]*?</nav>', '', text)
    attachments = {}

    def figure(match):
        image = re.search(r'<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"', match[0])
        caption = re.search(r'<figcaption>([\s\S]*?)</figcaption>', match[0])
        if not image:
            return match[0]
        name = Path(image[1]).name
        svg = (ROOT / image[1]).read_text()
        attachments[name] = {"image/svg+xml": svg}
        return f'\n![{image[2]}](attachment:{name})\n\n' + (caption[1] if caption else '')

    text = re.sub(r'<figure\b[\s\S]*?</figure>', figure, text)
    cell = {"cell_type": "markdown", "id": f"text-{index}", "metadata": {}, "source": text.strip().splitlines(True)}
    if attachments:
        cell["attachments"] = attachments
    return cell


def execute_chapter(page):
    source_path = ROOT / "content" / (page["file"] + ".md")
    source = source_path.read_text()
    body = re.sub(r"\A---\n[\s\S]*?\n---\n", "", source)
    cells, ns, outputs = [], {"__name__": "__main__"}, []
    offset = 0
    for count, match in enumerate(re.finditer(r"^```python\n([\s\S]*?)^```\s*$", body, re.M), 1):
        prose = body[offset:match.start()]
        if prose.strip():
            cells.append(markdown_cell(prose, len(cells)))
        code = match[1].rstrip() + "\n"
        output = io.StringIO()
        with redirect_stdout(output):
            exec(compile(code, f'{page["file"]}:example-{count}', 'exec'), ns)
        stdout = output.getvalue()
        cells.append({"cell_type": "code", "id": f"code-{count}", "metadata": {},
                      "source": code.splitlines(True), "execution_count": count,
                      "outputs": [{"output_type": "stream", "name": "stdout", "text": stdout.splitlines(True)}] if stdout else []})
        outputs.append({"example": count, "stdout": stdout})
        offset = match.end()
    if body[offset:].strip():
        cells.append(markdown_cell(body[offset:], len(cells)))
    assert outputs, f'No Python examples in {page["file"]}'
    notebook = {"nbformat": 4, "nbformat_minor": 5, "cells": cells,
                "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                             "language_info": {"name": "python", "version": sys.version.split()[0]},
                             "lesson": {"source": f'content/{page["file"]}.md', "sha256": hashlib.sha256(source.encode()).hexdigest(),
                                        "data_status": "Original hypothetical examples and seeded simulations"}}}
    return notebook, ns, outputs


def main():
    report = []
    for page in course_pages():
        notebook, _, outputs = execute_chapter(page)
        target = ROOT / page["notebook"]
        target.parent.mkdir(exist_ok=True, parents=True)
        target.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n")
        report.append({"page": page["file"], "examples": len(outputs), "outputs": outputs})
        print(f'{page["file"]}: executed {len(outputs)} examples, wrote {page["notebook"]}')
    out = ROOT / 'qa/output'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'course-python-outputs.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == "__main__":
    main()
