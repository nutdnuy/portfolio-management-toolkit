/** Check the Return lesson's plots, controls, accessible output and offline assets. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),output=path.join(__dirname,'output');
const base=process.env.PMT_PREVIEW_URL||'http://127.0.0.1:8764';
(async()=>{
 fs.mkdirSync(output,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try {
  const page=await browser.newPage(),errors=[],report=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
  for(const theme of ['light','dark'])for(const width of [320,390,768,1440]){
   await page.setViewportSize({width,height:1100});
   await page.goto(base+'/returns.html');
   await page.locator('#returns-year-1').waitFor();
   await page.evaluate(t=>document.documentElement.dataset.theme=t,theme);
   await page.evaluate(()=>document.fonts.ready);
   assert.equal(await page.locator('.katex-error').count(),0);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`Overflow: ${width} ${theme}`);
   assert.equal(await page.locator('main pre, a[href$=".ipynb"]').count(),0);
   assert.equal(await page.locator('.return-figure img').count(),2);
   assert.ok(await page.locator('.return-figure img').evaluateAll(imgs=>imgs.every(i=>i.complete&&i.naturalWidth===720)));
   const clipping=await page.locator('.rv-charts svg').evaluateAll(svgs=>svgs.flatMap(svg=>[...svg.querySelectorAll('text')].filter(t=>{const b=t.getBBox();return b.x<0||b.y<0||b.x+b.width>480||b.y+b.height>302}).map(t=>t.textContent)));
   assert.deepEqual(clipping,[],`Chart clipping: ${width} ${theme}`);
   await page.addScriptTag({path:require.resolve('axe-core/axe.min.js')});
   const violations=await page.evaluate(async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)})));
   assert.deepEqual(violations,[],JSON.stringify({width,theme,violations}));
   if([390,1440].includes(width)){
    await page.evaluate(()=>document.activeElement?.blur());
    await page.locator('.returns-viz').screenshot({path:path.join(output,`returns-lab-${theme}-${width}.png`),style:'.book-mobile-header,.skip-link{visibility:hidden!important}'});
    if(theme==='light')for(const [i,img] of (await page.locator('.return-figure img').all()).entries())await img.screenshot({path:path.join(output,`returns-figure-${i+1}-${width}.png`)});
   }
   report.push({width,theme,status:'passed'});
  }
  const result=()=>page.locator('[data-testid="terminal-wealth"]').innerText();
  assert.equal(await result(),'1,000,000 บาท');
  assert.equal(await page.locator('[data-testid="cumulative-return"]').innerText(),'0.00%');
  assert.equal(await page.locator('[data-testid="naive-return"]').innerText(),'+50.00%');
  await page.getByRole('button',{name:'+100% แล้ว −25%',exact:true}).click();
  assert.equal(await result(),'1,500,000 บาท');
  assert.equal(await page.locator('[data-testid="cumulative-return"]').innerText(),'+50.00%');
  await page.getByRole('button',{name:'+20% แล้ว −20%',exact:true}).click();
  assert.equal(await result(),'960,000 บาท');
  assert.equal(await page.locator('[data-testid="cumulative-return"]').innerText(),'−4.00%');
  await page.getByRole('button',{name:'+100% แล้ว −50%',exact:true}).click();
  await page.getByRole('button',{name:'สลับลำดับปี',exact:true}).click();
  assert.equal(await result(),'1,000,000 บาท');
  assert.equal(await page.locator('#returns-year-1').inputValue(),'-50');
  await page.locator('.rv-details summary').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('.rv-details').getAttribute('open'),'');
  assert.match(await page.locator('.rv-details tbody').innerText(),/500,000/);
  for(const id of ['#returns-year-1','#returns-year-2']){await page.locator(id).focus();await page.keyboard.press('Home');}
  assert.equal(await result(),'2,500 บาท');
  for(const id of ['#returns-year-1','#returns-year-2']){await page.locator(id).focus();await page.keyboard.press('End');}
  assert.equal(await result(),'9,000,000 บาท');
  await page.locator('#returns-year-1').fill('0');await page.locator('#returns-year-2').fill('0');
  assert.equal(await result(),'1,000,000 บาท');
  assert.match(await page.locator('.rv-pitfall').innerText(),/กรณีนี้ได้เท่ากัน/);
  await page.goto(pathToFileURL(path.join(root,'_site/returns.html')).href);
  await page.locator('#returns-year-1').waitFor();
  await page.getByRole('button',{name:'+100% แล้ว −25%',exact:true}).click();assert.equal(await result(),'1,500,000 บาท');
  const nojs=await browser.newPage({javaScriptEnabled:false});await nojs.goto(base+'/returns.html');
  assert.equal(await nojs.locator('.return-figure img').count(),2);assert.match(await nojs.locator('#returns-lab').innerText(),/เปิด JavaScript/);await nojs.close();
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(output,'returns-browser-report.json'),JSON.stringify({status:'passed',viewports:report,checks:['presets','swapped years','keyboard controls','table','slider extremes','zero returns','offline interaction','no-JS figures','no Python/Notebook','WCAG A/AA','SVG bounds']},null,2));
  console.log('Return visual checks passed: 8 viewport/theme combinations, controls, numerical outputs, accessibility, offline and no-JS.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
