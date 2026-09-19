import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const root = path.resolve(import.meta.dirname, '../_site');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'build-manifest.json'), 'utf8'));
const failures = [];
let checked = 0;
assert.equal(manifest.format, 'book');
assert.deepEqual(manifest.pages, ['index.html', 'returns.html', 'portfolio-insurance.html', 'glossary.html']);

function localReference(owner, reference) {
  if (/^(?:https?:|mailto:|data:|tel:)/i.test(reference)) return;
  checked++;
  const url = reference.replaceAll('&amp;', '&');
  const [file, fragment] = url.split('#');
  const target = file ? path.resolve(path.dirname(owner), decodeURIComponent(file.split('?')[0])) : owner;
  if (!target.startsWith(root + path.sep) || !fs.existsSync(target)) {
    failures.push(`${path.relative(root, owner)}: missing or nonportable ${url}`);
    return;
  }
  if (fragment && target.endsWith('.html')) {
    const targetHTML = fs.readFileSync(target, 'utf8');
    const id = decodeURIComponent(fragment);
    if (![...targetHTML.matchAll(/\bid="([^"]+)"/g)].some(match => match[1] === id)) failures.push(`${path.relative(root, owner)}: missing anchor ${url}`);
  }
}

// Include former entrypoint redirects and the license page as well as the book.
const htmlFiles = fs.readdirSync(root, { recursive: true }).filter(name => name.endsWith('.html'));
for (const name of htmlFiles) {
  const owner = path.join(root, name), html = fs.readFileSync(owner, 'utf8');
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  if (ids.length !== new Set(ids).size) failures.push(`${name}: duplicate id`);
  for (const match of html.matchAll(/(?:href|src)="([^"]+)"/g)) localReference(owner, match[1]);
}
for (const name of ['style.css', 'book.css', 'app.css', 'assets/katex/katex.min.css']) {
  const owner = path.join(root, name);
  if (!fs.existsSync(owner)) { failures.push(`Missing stylesheet ${name}`); continue; }
  for (const match of fs.readFileSync(owner, 'utf8').matchAll(/url\(["']?([^"')]+)["']?\)/g)) localReference(owner, match[1]);
}
for (const name of ['index.md', 'returns.md', 'portfolio-insurance.md', 'glossary.md']) {
  const artifact = path.join(root, name);
  if (!fs.existsSync(artifact) || fs.statSync(artifact).size === 0) failures.push(`Missing Markdown download ${name}`);
}
for (const notebookName of ['portfolio-insurance']) {
  const notebookFile = path.join(root, `notebooks/${notebookName}.ipynb`);
  if (!fs.existsSync(notebookFile)) failures.push(`Missing Notebook download notebooks/${notebookName}.ipynb`);
  else {
    const notebook = JSON.parse(fs.readFileSync(notebookFile, 'utf8'));
    if (notebook.nbformat !== 4 || !notebook.cells?.length) failures.push('Notebook is not a populated nbformat 4 document');
    if (notebook.cells?.some(cell => cell.outputs?.some(output => output.output_type === 'error'))) failures.push('Notebook contains an execution error');
  }
}
const returnPage = fs.readFileSync(path.join(root, 'returns.html'), 'utf8');
assert.doesNotMatch(returnPage, /\.ipynb|language-python|ทดลองคำนวณและตรวจคำตอบด้วย Python/);
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`Verified ${manifest.pages.length} book pages, ${htmlFiles.length} HTML files and ${checked} local references, including anchors, book.css, fonts, Markdown and Notebook downloads.`);
