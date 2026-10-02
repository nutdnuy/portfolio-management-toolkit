/* Focused checks for the Introduction and Advanced lessons and executable downloads. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '..');
const config = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json'), 'utf8'));
const pages = config.pages.filter(p => p.module && typeof p.notebook === 'string');
const base = process.env.PMT_PREVIEW_URL || 'http://127.0.0.1:8764';
const out = path.join(__dirname, 'output');
fs.mkdirSync(out, {recursive: true});

async function loadImages(page) {
  for (const image of await page.locator('main img').all()) {
    await image.scrollIntoViewIfNeeded();
    await image.evaluate(el => el.decode());
  }
}

(async () => {
  const browser = await chromium.launch({headless: true});
  const report = {pages: [], figures: [], search: [], downloads: []};
  try {
    const context = await browser.newContext({viewport:{width:768,height:960}, acceptDownloads:true});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    for (const item of pages) {
      await page.goto(`${base}/${item.file}.html`, {waitUntil:'networkidle'});
      await page.evaluate(() => document.fonts.ready);
      await loadImages(page);
      const source = fs.readFileSync(path.join(root,'content',item.file+'.md'),'utf8');
      const python = [...source.matchAll(/^```python\n([\s\S]*?)^```\s*$/gm)].map(m=>m[1].trim());
      assert.deepEqual(await page.locator('main code.language-python').allTextContents().then(xs=>xs.map(x=>x.trim())),python);
      assert.equal(await page.locator('main pre[tabindex="0"]').count(),await page.locator('main pre').count());
      assert.ok(await page.locator('main .katex').count()>0);
      const index = config.pages.findIndex(p=>p.file===item.file);
      for (const [relation, neighbor] of [['prev', config.pages[index-1]], ['next', config.pages[index+1]]]) {
        const link = page.locator(`main a[rel="${relation}"]`);
        if (neighbor) assert.equal(await link.getAttribute('href'),neighbor.file+'.html');
        else assert.equal(await link.count(),0,`${item.file} has no ${relation} chapter`);
      }
      const prefix = item.course === 'advanced' ? 'Advanced · ' : '';
      assert.equal(await page.locator('.chapter-kicker').textContent(),`${prefix}Module ${item.module} · บทย่อย ${item.lesson}`);
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+1);
      assert.equal(overflow,false,`${item.file} tablet overflow`);
      const details=page.locator('main details').first();
      if(await details.count()){
        await details.locator('summary').focus();
        await page.keyboard.press('Enter');
        assert.notEqual(await details.getAttribute('open'),null);
        await page.keyboard.press('Enter');
        assert.equal(await details.getAttribute('open'),null);
      }
      // Each download is the executed notebook belonging to this exact chapter.
      await page.locator('#menu-button').click();
      const [download]=await Promise.all([
        page.waitForEvent('download'),
        page.locator('.book-sidebar-footer').getByRole('link',{name:'ดาวน์โหลด Notebook',exact:true}).click()
      ]);
      const file=path.join(out,`download-${item.file}.ipynb`);
      await download.saveAs(file);
      assert.deepEqual(fs.readFileSync(file),fs.readFileSync(path.join(root,item.notebook)));
      report.downloads.push(item.notebook);
      report.pages.push({page:item.file,course:item.course || 'introduction',module:item.module,pythonBlocks:python.length,tablet:true,navigation:true,keyboard:true});
    }
    // Search crosses module boundaries and preserves the zero-result state.
    await page.goto(`${base}/index.html`,{waitUntil:'networkidle'});
    await page.locator('#menu-button').click();
    await page.locator('#search-button').click();
    for(const [query,target] of [['covariance','portfolio-basics'],['Glide path','goal-based-allocation'],['glidepath','glossary'],['Funding ratio','asset-liability'],['น้ำหนักพอร์ต','portfolio-basics']]){
      await page.locator('#search-input').fill(query);
      await page.waitForFunction(prefix=>[...document.querySelectorAll('#search-results a')].some(a=>a.getAttribute('href').startsWith(prefix)),target+'.html');
      report.search.push(query);
    }
    const advanced = pages.find(item => item.course === 'advanced');
    if (advanced) {
      await page.locator('#search-input').fill('Advanced');
      await page.waitForFunction(prefix=>[...document.querySelectorAll('#search-results a')].some(a=>a.getAttribute('href').startsWith(prefix)),advanced.file+'.html');
      const result = page.locator(`#search-results a[href="${advanced.file}.html"]`);
      assert.match(await result.locator('small').textContent(),/^Advanced · /);
      report.search.push('Advanced');
    }
    await page.locator('#search-input').fill('course-no-result-874639');
    await page.waitForFunction(()=>document.querySelectorAll('#search-results a').length===0);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#search-dialog').isVisible(),false);
    await context.close();

    // Self-contained exports, including readable code and pictures without JS.
    const offline = await browser.newContext({viewport:{width:390,height:844},javaScriptEnabled:false});
    const local = await offline.newPage();
    for(const item of pages){
      await local.goto(pathToFileURL(path.join(root,'_site',item.file+'.html')).href);
      await loadImages(local);
      assert.equal(await local.locator('h1').count(),1);
      assert.ok(await local.locator('main code.language-python').count()>0);
      assert.ok(await local.locator('main .katex').count()>0);
      assert.equal(await local.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+1),false);
    }
    await offline.close();

    const charts = await browser.newContext({viewport:{width:800,height:650}});
    const chartPage = await charts.newPage();
    const advancedCharts = fs.readdirSync(path.join(root,'assets/charts'))
      .filter(name=>name.startsWith('advanced-') && name.endsWith('.svg') && !name.endsWith('-mobile.svg'))
      .map(name=>name.slice(0,-4));
    for(const name of ['course-diversification','course-frontier','course-cppi','course-duration',...advancedCharts]){
      for(const suffix of ['', '-mobile']){
        await chartPage.goto(`${base}/assets/charts/${name}${suffix}.svg`);
        await chartPage.evaluate(()=>document.fonts.ready);
        const outside=await chartPage.evaluate(()=>{
          const svg=document.querySelector('svg'),v=svg.viewBox.baseVal;
          return [...svg.querySelectorAll('text')].map(el=>({text:el.textContent,b:el.getBBox()}))
            .filter(({b})=>b.x<0||b.y<0||b.x+b.width>v.width||b.y+b.height>v.height).map(({text})=>text);
        });
        assert.deepEqual(outside,[],`${name}${suffix} labels fit`);
        await chartPage.locator('svg').screenshot({path:path.join(out,`${name}${suffix}.png`)});
        report.figures.push(name+suffix);
      }
    }
    await charts.close();
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(out,'course-browser-report.json'),JSON.stringify(report,null,2)+'\n');
    console.log(`PASS ${pages.length} course pages: Python, math, previous/next, keyboard, downloads, search, offline/no-JS; ${report.figures.length} SVG bounds.`);
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exit(1)});
