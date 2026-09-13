const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
const esbuild = require('esbuild');
const katex = require('katex');
const root = __dirname, out = path.join(root, '_site');
const escape = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const plain = s => s.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
const slug = s => plain(s).toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-|-$/g, '');
async function build() {
  const {marked} = await import('marked');
  const config = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json'), 'utf8'));
  fs.mkdirSync(out, {recursive:true});
  fs.cpSync(path.join(root, 'assets'), path.join(out, 'assets'), {recursive:true});
  fs.cpSync(path.join(root, 'node_modules/katex/dist'), path.join(out, 'assets/katex'), {recursive:true});
  for (const name of ['style.css', 'book.css', 'THIRD_PARTY_NOTICES.md']) fs.copyFileSync(path.join(root, name), path.join(out, name));
  if (fs.existsSync(path.join(root, 'notebooks'))) fs.cpSync(path.join(root, 'notebooks'), path.join(out, 'notebooks'), {recursive:true});
  fs.mkdirSync(path.join(out, 'licenses'), {recursive:true});
  for (const name of fs.readdirSync(path.join(root, 'vendor')).filter(n => n.endsWith('-LICENSE.txt'))) fs.copyFileSync(path.join(root, 'vendor', name), path.join(out, 'licenses', name));
  fs.writeFileSync(path.join(out, 'licenses/index.html'), '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Third-party licenses</title><h1>Third-party licenses</h1><p><a href="../index.html">Return to the book</a></p><ul>' + fs.readdirSync(path.join(out, 'licenses')).filter(n => n.endsWith('.txt')).map(n => '<li><a href="' + n + '">' + n + '</a></li>').join('') + '</ul></html>');
  const cover = className => `<div class="brand-cover ${className}" role="img" aria-label="QuantCorner / Quantsera บนพื้นหลังสีดำ">${config.logos.map(src => `<img src="${escape(src)}" alt="" width="1024" height="228">`).join('')}</div>`;
  const icon = fs.readFileSync(path.join(root, 'assets/icons/search.svg'), 'utf8').replace('<svg', '<svg aria-hidden="true" focusable="false"');
  const pages = config.pages.map(page => {
    let source = fs.readFileSync(path.join(root, `content/${page.file}.md`), 'utf8').replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '');
    fs.copyFileSync(path.join(root, `content/${page.file}.md`), path.join(out, `${page.file}.md`));
    const equations = [];
    const math = (tex, display) => {
      const i = equations.length;
      equations.push(katex.renderToString(tex.trim(), {displayMode:display, throwOnError:true, output:'htmlAndMathml', strict:'ignore'}));
      return display ? `\n\n<div class="equation math-display" tabindex="0" role="group" aria-label="สมการ">PMTMATH${i}END</div>\n\n` : `PMTMATH${i}END`;
    };
    source = source.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => math(tex, true)).replace(/\$([^$\n]+)\$/g, (_, tex) => math(tex, false));
    let body = marked.parse(source).replace(/PMTMATH(\d+)END/g, (_, i) => equations[+i]);
    const headings = [], ids = new Map([...body.matchAll(/\bid="([^"]+)"/g)].map(match => [match[1], 1]));
    body = body.replace(/<h([1-3])>([\s\S]*?)<\/h\1>/g, (_, level, text) => {
      const base = slug(text), n = (ids.get(base) || 0) + 1;
      ids.set(base, n);
      const id = base + (n === 1 ? '' : `-${n}`);
      if (level === '2') headings.push({id, title:plain(text)});
      return `<h${level} id="${id}">${text}</h${level}>`;
    });
    body = body.replace(/<table>/g, '<div class="table-scroll" tabindex="0" role="region" aria-label="ตารางข้อมูล เลื่อนแนวนอนได้"><table>').replace(/<\/table>/g, '</table></div>').replace(/href="([a-z-]+)\.md/g, 'href="$1.html').replace(/<a href="glossary\.html#[^"]+"/g, link => link + ' class="glossary-link"');
    return {...page, body, headings};
  });
  const search = [];
  for (const page of pages) {
    const chunks = page.body.split(/(?=<h[23]\b)/);
    search.push({title:page.title, section:page.title, url:`${page.file}.html`, text:plain(page.body).slice(0, 600)});
    for (const chunk of chunks) {
      const h = chunk.match(/^<h[23] id="([^"]+)">([\s\S]*?)<\/h[23]>/);
      if (h) search.push({title:plain(h[2]), section:page.title, url:`${page.file}.html#${h[1]}`, text:plain(chunk).slice(0, 3500)});
    }
    const nav = pages.map(p => `<a href="${p.file}.html" class="book-link${p.file === page.file ? ' current' : ''}" ${p.file === page.file ? 'aria-current="page"' : ''}>${escape(p.title)}</a>`).join('');
    const contents = page.file === 'index' ? '' : `<details class="page-contents" open><summary>ในหน้านี้</summary><nav aria-label="หัวข้อในหน้านี้">${page.headings.map(h => `<a href="#${escape(h.id)}">${escape(h.title)}</a>`).join('')}</nav></details>`;
    const home = page.file === 'index';
    const html = `<!doctype html><html lang="th" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="${escape(page.description)}"><title>${escape(page.title)} · ${escape(config.title)}</title><link rel="icon" href="assets/brand/favicon-32.png"><link rel="stylesheet" href="assets/katex/katex.min.css"><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="app.css"><link rel="stylesheet" href="book.css"><script>try{document.documentElement.dataset.theme=localStorage.getItem('pmt-book-theme')==='dark'?'dark':'light'}catch(e){}</script></head><body class="book ${home ? 'welcome-page' : 'lesson-page'}" data-page="${page.file}">
<a class="skip-link" href="#content">ข้ามไปเนื้อหา</a>
<header class="book-mobile-header"><a href="index.html">${escape(config.title)}</a><button id="menu-button" aria-expanded="false" aria-controls="book-sidebar">สารบัญ</button></header>
<div class="book-layout"><aside id="book-sidebar" class="book-sidebar"><a href="index.html" class="cover-link" aria-label="กลับหน้า Welcome">${cover('book-cover')}</a><a class="book-name" href="index.html">${escape(config.title)}</a><button class="search-trigger" id="search-button">${icon}<span>Search</span><kbd>⌘ K</kbd></button><nav class="book-nav" aria-label="สารบัญ">${nav}</nav>${contents}<div class="book-sidebar-footer"><a href="${escape(config.notebook)}" download>ดาวน์โหลด Notebook</a><a href="${page.file}.md" download>ไฟล์ Markdown หน้านี้</a><button id="theme-button">พื้นหลังมืด</button></div></aside>
<main class="book-main ${home ? 'welcome-main' : 'chapter'}" id="content"><div class="page-topline"><span>${escape(config.title)}</span><button id="print-button">พิมพ์หน้านี้</button></div>${home ? cover('mobile-cover') : ''}${page.body}<footer class="book-footer"><span>${escape(config.title)}</span><span>โดย ${escape(config.author)} · <a href="licenses/index.html">สิทธิ์การใช้งาน</a></span></footer></main></div>
<dialog id="search-dialog" aria-labelledby="search-title"><div class="search-dialog-heading"><h2 id="search-title">ค้นหาในหนังสือ</h2><button id="close-search" aria-label="ปิดการค้นหา">ปิด</button></div><label for="search-input" class="sr-only">คำค้นหา</label><input id="search-input" type="search" autocomplete="off" placeholder="ค้นหา CPPI, Cushion หรือ การป้องกัน"><p id="search-status" role="status"></p><div id="search-results"></div></dialog><script src="search-index.js" defer></script><script src="site.js" defer></script>${page.file === 'portfolio-insurance' ? '<script src="app.js" defer></script>' : ''}</body></html>`;
    fs.writeFileSync(path.join(out, page.file + '.html'), html);
  }
  for (const [old, anchor] of [['lab','cppi-lab'], ['research','references']]) fs.writeFileSync(path.join(out, old + '.html'), `<!doctype html><html lang="th"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=portfolio-insurance.html#${anchor}"><title>Portfolio Insurance</title><a href="portfolio-insurance.html#${anchor}">อ่านบท Portfolio Insurance</a></html>`);
  fs.writeFileSync(path.join(out, 'search-index.js'), 'window.PMTSearch=' + JSON.stringify(search).replaceAll('<', '\\u003c') + ';');
  fs.copyFileSync(path.join(root, 'src/site.js'), path.join(out, 'site.js'));
  await esbuild.build({entryPoints:[path.join(root, 'src/app.jsx')], outfile:path.join(out, 'app.js'), bundle:true, format:'iife', jsx:'automatic', minify:true, target:'es2022', define:{'process.env.NODE_ENV':'"production"'}, legalComments:'linked'});
  for (const page of pages) {
    const file = path.join(out, page.file + '.html');
    let html = fs.readFileSync(file, 'utf8');
    for (const asset of ['style.css','book.css','app.css','app.js','site.js','search-index.js']) {
      const hash = createHash('sha256').update(fs.readFileSync(path.join(out, asset))).digest('hex').slice(0, 10);
      html = html.replaceAll(`"${asset}"`, `"${asset}?v=${hash}"`);
    }
    fs.writeFileSync(file, html);
  }
  fs.writeFileSync(path.join(out, 'build-manifest.json'), JSON.stringify({title:config.title, visualRoute:config.visualRoute, format:'book', pages:pages.map(p => p.file + '.html'), searchEntries:search.length}, null, 2));
  console.log(`Built ${pages.length} book pages, ${search.length} search entries in _site/.`);
}
build().catch(error => {console.error(error); process.exit(1);});
