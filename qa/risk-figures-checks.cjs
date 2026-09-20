const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const base=process.env.PMT_PREVIEW_URL||'http://127.0.0.1:8764';
(async()=>{const b=await chromium.launch();try{const p=await b.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
for(const width of [320,390,1440])for(const theme of ['light','dark']){
 await p.setViewportSize({width,height:1000});await p.goto(base+'/risk.html',{waitUntil:'networkidle'});await p.evaluate(t=>document.documentElement.dataset.theme=t,theme);
 assert.equal(await p.locator('.risk-editorial-image').count(),1);assert.equal(await p.locator('.risk-static-figure').count(),2);
 for(const [i,f] of (await p.locator('.risk-editorial-image,.risk-static-figure').all()).entries()){
  await f.scrollIntoViewIfNeeded();const img=f.locator('img');await img.evaluate(e=>e.decode());assert.ok(await img.evaluate(e=>e.complete&&e.naturalWidth>0));
  if(i>0)assert.equal(await img.evaluate(e=>e.naturalWidth),width<=600?400:720);
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  if(width!==320)await f.screenshot({path:path.join(__dirname,'output',`risk-new-figure-${i}-${theme}-${width}.png`),style:'.book-mobile-header{visibility:hidden!important}'});
 }
}
for(const name of ['risk-outcomes','risk-correlation'])for(const suffix of ['', '-mobile']){
 await p.goto(`${base}/assets/charts/${name}${suffix}.svg`);await p.evaluate(()=>document.fonts.ready);
 const clipped=await p.evaluate(()=>{const svg=document.querySelector('svg'),v=svg.viewBox.baseVal;return [...svg.querySelectorAll('text')].filter(t=>{const b=t.getBBox();return b.x<0||b.y<0||b.x+b.width>v.width||b.y+b.height>v.height}).map(t=>t.textContent)});assert.deepEqual(clipped,[],name+suffix);
}
assert.deepEqual(errors,[]);console.log('Risk figures passed: image decoding, responsive variants, 6 viewport/theme combinations, SVG text bounds.');
}finally{await b.close()}})().catch(e=>{console.error(e);process.exit(1)});
