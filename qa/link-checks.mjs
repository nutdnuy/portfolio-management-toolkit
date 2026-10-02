import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const root = path.resolve(import.meta.dirname, '../_site');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'build-manifest.json'), 'utf8'));
const failures = [];
let checked = 0;
assert.equal(manifest.format, 'book');
const config = JSON.parse(fs.readFileSync(path.resolve(root, '../site.config.json'), 'utf8'));
assert.deepEqual(manifest.pages, config.pages.map(page => `${page.file}.html`));
assert.equal(new Set(config.pages.map(page => page.file)).size, config.pages.length, 'Page filenames must be unique across courses');
const lessonIds = new Set(), lessonNotebooks = new Set();
for (const page of config.pages) {
  if (page.course !== undefined) assert.ok(['introduction', 'advanced'].includes(page.course), `${page.file}: unknown course`);
  if (page.dataStatus !== undefined) assert.ok(typeof page.dataStatus === 'string' && page.dataStatus.trim(), `${page.file}: dataStatus must be nonempty text`);
  if (page.notebook !== undefined) assert.ok(page.notebook === false || (typeof page.notebook === 'string' && page.notebook.endsWith('.ipynb')), `${page.file}: notebook must be false or an ipynb path`);
  if (page.module === undefined) continue;
  assert.ok(Number.isInteger(page.module) && page.module > 0, `${page.file}: invalid module number`);
  assert.ok(Number.isInteger(page.lesson) && page.lesson > 0, `${page.file}: invalid lesson number`);
  const course = page.course ?? 'introduction';
  const id = `${course}:${page.module}:${page.lesson}`;
  assert.ok(!lessonIds.has(id), `Duplicate course/module/lesson: ${id}`);
  lessonIds.add(id);
  if (typeof page.notebook === 'string') {
    assert.ok(!lessonNotebooks.has(page.notebook), `Course lessons must not overwrite the same Notebook: ${page.notebook}`);
    lessonNotebooks.add(page.notebook);
  }
}

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
  for (const match of html.matchAll(/srcset="([^"]+)"/g)) {
    for (const candidate of match[1].split(",")) localReference(owner, candidate.trim().split(/\s+/)[0]);
  }
}
for (const name of ['style.css', 'book.css', 'app.css', 'returns.css', 'risk.css', 'extreme-risk.css', 'assets/katex/katex.min.css']) {
  const owner = path.join(root, name);
  if (!fs.existsSync(owner)) { failures.push(`Missing stylesheet ${name}`); continue; }
  for (const match of fs.readFileSync(owner, 'utf8').matchAll(/url\(["']?([^"')]+)["']?\)/g)) localReference(owner, match[1]);
}
for (const name of config.pages.map(page => `${page.file}.md`)) {
  const artifact = path.join(root, name);
  if (!fs.existsSync(artifact) || fs.statSync(artifact).size === 0) failures.push(`Missing Markdown download ${name}`);
}
const notebookPaths = new Set([config.notebook, ...config.pages.map(page => page.notebook)].filter(value => typeof value === 'string'));
for (const notebookPath of notebookPaths) {
  const notebookFile = path.resolve(root, notebookPath);
  if (!notebookFile.startsWith(root + path.sep)) {
    failures.push(`Nonportable Notebook path ${notebookPath}`);
    continue;
  }
  if (!fs.existsSync(notebookFile)) failures.push(`Missing Notebook download ${notebookPath}`);
  else {
    const notebook = JSON.parse(fs.readFileSync(notebookFile, 'utf8'));
    if (notebook.nbformat !== 4 || !notebook.cells?.length) failures.push('Notebook is not a populated nbformat 4 document');
    if (notebook.cells?.some(cell => cell.outputs?.some(output => output.output_type === 'error'))) failures.push('Notebook contains an execution error');
  }
}
const returnPage = fs.readFileSync(path.join(root, 'returns.html'), 'utf8');
assert.match(returnPage, /<code class="language-python">\s*\S/, 'The Return lesson includes readable Python examples.');
assert.doesNotMatch(returnPage, /href="[^"]*\.ipynb(?:[?#][^"]*)?"/, 'The Return lesson does not link to an unrelated Notebook.');
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`Verified ${manifest.pages.length} book pages, ${htmlFiles.length} HTML files and ${checked} local references, including anchors, book.css, fonts, Markdown and Notebook downloads.`);
