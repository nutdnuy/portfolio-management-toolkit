import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'../_site');
const pages=JSON.parse(fs.readFileSync(path.join(root,'build-manifest.json'),'utf8')).pages;
const failures=[];
let checked=0;
for(const page of pages){
 const html=fs.readFileSync(path.join(root,page),'utf8'),ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
 if(ids.length!==new Set(ids).size)failures.push(`${page}: duplicate id`);
 for(const match of html.matchAll(/(?:href|src)="([^"]+)"/g)){
  const url=match[1];if(/^(?:https?:|mailto:|data:)/.test(url))continue;
  const [file,fragment]=url.split('#'),target=path.resolve(root,file.split('?')[0]||page);checked++;
  if(!target.startsWith(root+path.sep)||!fs.existsSync(target)){failures.push(`${page}: missing ${url}`);continue;}
  if(fragment&&target.endsWith('.html')){const targetHTML=fs.readFileSync(target,'utf8');const id=decodeURIComponent(fragment);if(!targetHTML.includes(`id="${id}"`))failures.push(`${page}: missing anchor ${url}`);}
 }
}
for(const file of ['style.css','app.css','assets/katex/katex.min.css']){
 const full=path.join(root,file);const css=fs.readFileSync(full,'utf8');
 for(const match of css.matchAll(/url\(["']?([^"')]+)["']?\)/g)){const url=match[1];if(/^(data:|https?:)/.test(url))continue;checked++;if(!fs.existsSync(path.resolve(path.dirname(full),url.split('?')[0])))failures.push(`${file}: missing ${url}`);}
}
assert.deepEqual(failures,[],failures.join('\n'));
console.log(`Verified ${pages.length} pages and ${checked} local asset/link references including anchors and CSS fonts.`);
