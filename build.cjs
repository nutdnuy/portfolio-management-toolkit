const fs = require('node:fs');
const path = require('node:path');
const esbuild = require('esbuild');
const katex = require('katex');
const root = __dirname, out = path.join(root, '_site');
const escape = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const plain = s => s.replace(/<[^>]+>/g, ' ').replace(/\s+/g,' ').trim();
const slug = s => plain(s).toLowerCase().replace(/[^\p{L}\p{N}]+/gu,'-').replace(/^-|-$/g,'');
async function build() {
  const {marked} = await import('marked');
  const config = JSON.parse(fs.readFileSync(path.join(root,'site.config.json'),'utf8'));
  fs.mkdirSync(out,{recursive:true});
  fs.cpSync(path.join(root,'assets'),path.join(out,'assets'),{recursive:true});
  fs.cpSync(path.join(root,'node_modules/katex/dist'),path.join(out,'assets/katex'),{recursive:true});
  fs.copyFileSync(path.join(root,'style.css'),path.join(out,'style.css'));
  fs.mkdirSync(path.join(out,'licenses'),{recursive:true});
  for(const name of fs.readdirSync(path.join(root,'vendor')).filter(n=>n.endsWith('-LICENSE.txt')))fs.copyFileSync(path.join(root,'vendor',name),path.join(out,'licenses',name));
  fs.copyFileSync(path.join(root,'THIRD_PARTY_NOTICES.md'),path.join(out,'THIRD_PARTY_NOTICES.md'));
  fs.writeFileSync(path.join(out,'licenses/index.html'),'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Third-party licenses</title><h1>Third-party licenses</h1><p><a href="../index.html">Return to the toolkit</a></p><ul>'+fs.readdirSync(path.join(out,'licenses')).filter(n=>n.endsWith('.txt')).map(n=>'<li><a href="'+n+'">'+n+'</a></li>').join('')+'</ul></html>');
  const icon = name => fs.readFileSync(path.join(root,`assets/icons/${name}.svg`),'utf8').replace('<svg','<svg aria-hidden="true" focusable="false"');
  const pages = config.pages.map(page => {
    let source=fs.readFileSync(path.join(root,`content/${page.file}.md`),'utf8').replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/,'');
    const equations=[];
    const math=(tex,display)=>{const i=equations.length;equations.push(katex.renderToString(tex.trim(),{displayMode:display,throwOnError:true,output:'htmlAndMathml',strict:'ignore'}));return display?`\n\n<div class="equation" tabindex="0" role="group" aria-label="Equation">PMTMATH${i}END</div>\n\n`:`PMTMATH${i}END`;};
    source=source.replace(/\$\$([\s\S]*?)\$\$/g,(_,tex)=>math(tex,true)).replace(/\$([^$\n]+)\$/g,(_,tex)=>math(tex,false));
    let body=marked.parse(source).replace(/PMTMATH(\d+)END/g,(_,i)=>equations[+i]);
    const headings=[], ids=new Map([...body.matchAll(/\bid="([^"]+)"/g)].map(match=>[match[1],1]));
    body=body.replace(/<h([1-3])>([\s\S]*?)<\/h\1>/g,(_,level,text)=>{const base=slug(text),n=(ids.get(base)||0)+1;ids.set(base,n);const id=base+(n===1?'':`-${n}`);if(level==='2')headings.push({id,title:plain(text)});return `<h${level} id="${id}">${text}</h${level}>`;});
    body=body.replace(/<table>/g,'<div class="table-scroll" tabindex="0" role="region" aria-label="Scrollable data table"><table>').replace(/<\/table>/g,'</table></div>').replace(/href="([a-z-]+)\.md/g,'href="$1.html');
    return {...page,body,headings};
  });
  const search=[];
  for (const page of pages) {
    const chunks=page.body.split(/(?=<h[23]\b)/);
    search.push({title:page.title,section:page.title,url:`${page.file}.html`,text:plain(page.body).slice(0,600)});
    for(const chunk of chunks){const h=chunk.match(/^<h[23] id="([^"]+)">([\s\S]*?)<\/h[23]>/);if(h)search.push({title:plain(h[2]),section:page.title,url:`${page.file}.html#${h[1]}`,text:plain(chunk).slice(0,3000)});}
    const nav=pages.map(p=>`<a href="${p.file}.html" class="nav-link${p.file===page.file?' active':''}" ${p.file===page.file?'aria-current="page"':''}>${icon(p.icon)}<span>${escape(p.title)}</span></a>`).join('');
    const i=pages.indexOf(page), next=pages[i+1];
    const html=`<!doctype html><html lang="th" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="${escape(page.description)}"><title>${escape(page.title)} · ${escape(config.title)}</title><link rel="icon" href="assets/brand/favicon-32.png"><link rel="stylesheet" href="assets/katex/katex.min.css"><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="app.css"><script>try{document.documentElement.dataset.theme=localStorage.getItem('pmt-theme')==='light'?'light':'dark'}catch(e){}</script></head><body data-page="${page.file}">
<a class="skip-link" href="#content">Skip to content</a>
<header class="mobile-header"><a href="index.html">Portfolio Management Toolkit</a><button id="menu-button" aria-label="Open navigation" aria-expanded="false" aria-controls="sidebar">${icon('menu-2')}</button></header>
<aside class="sidebar" id="sidebar"><a class="brand" href="index.html"><img class="brand-dark" src="assets/brand/quantcorner-mark-dark.svg" width="32" height="32" alt=""><img class="brand-light" src="assets/brand/quantcorner-mark-light.svg" width="32" height="32" alt=""><span>QuantCorner<span class="brand-sub">RESEARCH & LEARNING</span></span></a><a class="site-name" href="index.html">Portfolio<br>Management<br>Toolkit<span class="edition">LEARN / EXPERIMENT / UNDERSTAND</span></a><button class="search-trigger" id="search-button">${icon('search')}<span>Search toolkit</span><kbd>⌘ K</kbd></button><div class="nav-caption">EXPLORE THE TOOLKIT</div><nav aria-label="Main navigation">${nav}</nav><div class="sidebar-bottom"><div class="small muted">FIRST COLLECTION</div><p>Portfolio Insurance<br><span class="small muted">Based on Silva · 2018</span></p><button id="theme-button" class="theme-button" aria-label="Switch to light theme">${icon('sun')}<span>Light theme</span></button></div></aside>
<main id="content" class="main ${page.file==='index'?'home':'reading'}"><div class="topbar"><span>${escape(page.eyebrow)}</span><a href="research.html#source">Source & methodology ${icon('arrow-up-right')}</a></div><article>${page.body}</article>${next?`<a class="next-page" href="${next.file}.html"><span>CONTINUE EXPLORING</span><strong>${escape(next.title)} ↗</strong></a>`:''}<footer class="footer"><span>Portfolio Management Toolkit <span class="muted">/ QuantCorner</span></span><a href="licenses/index.html" class="muted">Third-party licenses</a></footer></main>
<dialog id="search-dialog" aria-labelledby="search-title"><div class="dialog-heading"><h2 id="search-title">Search the toolkit</h2><button id="close-search" aria-label="Close search">${icon('x')}</button></div><label for="search-input">Search in English or Thai</label><input id="search-input" type="search" autocomplete="off" placeholder="CPPI, Cushion, การป้องกัน…"><p id="search-status" role="status" class="small muted"></p><div id="search-results"></div></dialog><script src="search-index.js" defer></script><script src="site.js" defer></script><script src="app.js" defer></script></body></html>`;
    fs.writeFileSync(path.join(out,page.file+'.html'),html);
  }
  fs.writeFileSync(path.join(out,'search-index.js'),'window.PMTSearch='+JSON.stringify(search).replaceAll('<','\\u003c')+';');
  fs.copyFileSync(path.join(root,'src/site.js'),path.join(out,'site.js'));
  await esbuild.build({entryPoints:[path.join(root,'src/app.jsx')],outfile:path.join(out,'app.js'),bundle:true,format:'iife',jsx:'automatic',minify:true,target:'es2022',define:{'process.env.NODE_ENV':'"production"'},legalComments:'linked'});
  fs.writeFileSync(path.join(out,'build-manifest.json'),JSON.stringify({title:config.title,visualRoute:config.visualRoute,pages:pages.map(p=>p.file+'.html'),searchEntries:search.length},null,2));
  console.log(`Built ${pages.length} pages, ${search.length} search entries in _site/.`);
}
build().catch(error=>{console.error(error);process.exit(1);});
