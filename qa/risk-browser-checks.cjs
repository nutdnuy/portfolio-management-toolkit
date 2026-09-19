/** Risk lesson: numerical interactions, accessible charts, navigation and offline reading. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),output=path.join(__dirname,'output');
const base=process.env.PMT_PREVIEW_URL||'http://127.0.0.1:8764';
(async()=>{
 fs.mkdirSync(output,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage(),errors=[],report=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
  const value=id=>page.getByTestId(id).innerText();
  for(const theme of ['light','dark'])for(const width of [320,390,768,1440]){
   await page.setViewportSize({width,height:1000});
   await page.goto(base+'/risk.html');await page.locator('#risk-lambda').waitFor();
   await page.evaluate(t=>document.documentElement.dataset.theme=t,theme);await page.evaluate(()=>document.fonts.ready);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`Overflow ${width} ${theme}`);
   assert.equal(await page.locator('.katex-error').count(),0);
   assert.equal(await page.locator('a[href$=".ipynb"]').count(),0,'Risk must not link an unrelated Notebook');
   assert.equal(await page.locator('.risk-viz').count(),3);
   const duplicates=await page.evaluate(()=>{const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);return ids.filter((id,i)=>ids.indexOf(id)!==i)});
   assert.deepEqual(duplicates,[]);
   const clipped=await page.locator('.risk-chart svg').evaluateAll(svgs=>svgs.flatMap(svg=>[...svg.querySelectorAll('text')].filter(t=>{const b=t.getBBox(),v=svg.viewBox.baseVal;return b.x<-.5||b.y<-.5||b.x+b.width>v.width+.5||b.y+b.height>v.height+.5}).map(t=>t.textContent)));
   assert.deepEqual(clipped,[],`SVG clipping ${width} ${theme}`);
   await page.addScriptTag({path:require.resolve('axe-core/axe.min.js')});
   const violations=await page.evaluate(async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)})));
   assert.deepEqual(violations,[],JSON.stringify({width,theme,violations}));
   if([390,1440].includes(width))for(const id of ['risk-path-lab','risk-tail-lab','risk-ewma-lab'])await page.locator('#'+id).screenshot({path:path.join(output,`${id}-${theme}-${width}.png`),style:'.book-mobile-header,.skip-link{visibility:hidden!important}'});
   report.push({width,theme,status:'passed'});
  }
  assert.equal(await value('path-mdd'),'19.00%');assert.equal(await value('path-volatility'),'11.55%');assert.equal(await value('path-terminal'),'980,100 บาท');
  await page.getByRole('button',{name:/^พอร์ต B/}).focus();await page.keyboard.press('Enter');
  assert.equal(await value('path-mdd'),'10.90%');assert.equal(await value('path-volatility'),'11.55%');assert.equal(await value('path-terminal'),'980,100 บาท');
  const pathDetails=page.locator('#risk-path-lab details');await pathDetails.locator('summary').focus();await page.keyboard.press('Enter');
  assert.equal(await pathDetails.getAttribute('open'),'');assert.match(await pathDetails.innerText(),/-10.90%/);
  assert.equal(await value('tail-var'),'20,000 บาท');assert.equal(await value('tail-es'),'56,000 บาท');
  await page.locator('#risk-extreme').focus();await page.keyboard.press('End');
  assert.equal(await value('tail-var'),'20,000 บาท');assert.equal(await value('tail-es'),'96,000 บาท');
  await page.locator('#risk-extreme').fill('300000');assert.equal(await value('tail-es'),'76,000 บาท');
  assert.equal(await value('ewma-next'),'1.3784%');
  await page.locator('#risk-lambda').fill('0.97');assert.equal(await value('ewma-next'),'1.2042%');
  await page.locator('#risk-lambda').focus();await page.keyboard.press('Home');assert.equal(await value('ewma-next'),'2.0000%');
  await page.locator('#risk-shock').fill('4');assert.equal(await value('ewma-next'),'2.0000%');
  await page.locator('#risk-shock').fill('0');assert.equal(await value('ewma-next'),'0.8944%');
  await page.locator('#risk-shock').focus();await page.keyboard.press('End');assert.equal(await value('ewma-next'),'2.8284%');
  await page.locator('#risk-lambda').focus();await page.keyboard.press('End');assert.equal(await value('ewma-new-weight'),'1%');
  const clippedExtreme=await page.locator('#risk-ewma-lab svg text').evaluateAll(nodes=>nodes.filter(t=>{const b=t.getBBox();return b.x<0||b.y<0||b.x+b.width>500||b.y+b.height>265}).map(t=>t.textContent));assert.deepEqual(clippedExtreme,[]);
  // Changing orientation before an in-page jump must use the new text layout.
  await page.setViewportSize({width:390,height:1000});
  await page.goto(base+'/risk.html#expected-shortfall');
  await page.waitForFunction(()=>{const t=document.getElementById('expected-shortfall').parentElement.nextElementSibling.getBoundingClientRect().top;return t>=66&&t<180});
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('#search-button').click();await page.locator('#search-input').fill('Bernoulli');
  await page.waitForFunction(()=>document.querySelector('#search-results').textContent.includes('Bernoulli'));
  assert.ok(await page.locator('#search-results a[href^="risk.html"]').count()>0);await page.locator('#close-search').click();
  await page.goto(base+'/glossary.html#expected-shortfall');
  assert.equal(await page.locator('.glossary-term').count(),47);
  const query=page.locator('#glossary-query');
  for(const term of ['ความผันผวน','Expected Shortfall','EWMA']){await query.fill(term);assert.ok(await page.locator('.glossary-term:not([hidden])').count()>0)}
  await query.fill('no-risk-term-1234');assert.equal(await page.locator('.glossary-term:not([hidden])').count(),0);
  await query.fill('Expected Shortfall');await page.locator('#expected-shortfall a').click();assert.equal(new URL(page.url()).hash,'#expected-shortfall');
  // Initial deep links must remain visible after charts and Thai fonts change layout.
  for(const width of [390,1440]){
   await page.setViewportSize({width,height:1000});
   await page.goto(base+'/risk.html#expected-shortfall',{waitUntil:'networkidle'});
   await page.waitForFunction(()=>{const t=document.getElementById('expected-shortfall').parentElement.nextElementSibling.getBoundingClientRect().top;return t>=24&&t<180});
   await page.screenshot({path:path.join(output,`risk-anchor-${width}.png`)});
  }
  await page.goto(pathToFileURL(path.join(root,'_site/risk.html')).href);await page.locator('#risk-lambda').waitFor();
  await page.getByRole('button',{name:/^พอร์ต B/}).click();assert.equal(await value('path-mdd'),'10.90%');
  await page.locator('#risk-extreme').fill('400000');assert.equal(await value('tail-es'),'96,000 บาท');
  await page.locator('#risk-lambda').fill('0.97');assert.equal(await value('ewma-next'),'1.2042%');
  const nojs=await browser.newPage({javaScriptEnabled:false});await nojs.goto(base+'/risk.html');
  assert.equal(await nojs.locator('h1').count(),1);assert.equal(await nojs.locator('main table').count(),7);
  for(const id of ['risk-path-lab','risk-tail-lab','risk-ewma-lab'])assert.match(await nojs.locator('#'+id).innerText(),/เปิด JavaScript/);
  await nojs.close();assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(output,'risk-browser-report.json'),JSON.stringify({status:'passed',viewports:report,checks:['path preset and drawdown','VaR/ES extremes and ties','EWMA timing and symmetry','keyboard controls','SVG bounds','WCAG A/AA','Thai/English glossary','search','offline labs','initial deep links after lab and font loading','no-JS prose and tables']},null,2));
  console.log('Risk checks passed: 8 viewport/theme combinations, 3 labs, keyboard, accessibility, search, glossary, offline and no-JS.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
