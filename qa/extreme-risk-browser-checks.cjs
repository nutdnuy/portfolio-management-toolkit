/** Verify the beginner Extreme Risk chapter, code, figure and local downloads. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const root = path.resolve(__dirname, '..');
const output = path.join(__dirname, 'output');
const base = process.env.PMT_PREVIEW_URL || 'http://127.0.0.1:8764';
const pageName = 'extreme-risk.html';
const source = fs.readFileSync(path.join(root, 'content/extreme-risk.md'), 'utf8');
const pythonBlocks = [...source.matchAll(/```python\r?\n([\s\S]*?)```/g)].map(match => match[1].trim());
const moduleBytes = fs.readFileSync(path.join(root, 'examples/extreme-risk/finance_tools.py'));
const config = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json'), 'utf8'));
const pageIndex = config.pages.findIndex(item => item.file === 'extreme-risk');
assert.ok(pageIndex > 0, 'The chapter belongs in the book navigation.');

(async () => {
  fs.mkdirSync(output, {recursive: true});
  const browser = await chromium.launch({headless: true});
  const errors = [], viewports = [], figures = [];
  try {
    const page = await browser.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => {
      if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
    });

    for (const theme of ['light', 'dark']) for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({width, height: 1100});
      await page.goto(`${base}/${pageName}`);
      await page.evaluate(value => { document.documentElement.dataset.theme = value; }, theme);
      await page.evaluate(() => document.fonts.ready);
      assert.equal(await page.locator('.katex-error').count(), 0);
      assert.ok(await page.locator('.katex').count() > 0, 'Equations render as math.');
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false,
        `Document overflow: ${width} ${theme}`);
      assert.deepEqual((await page.locator('main pre code.language-python').allTextContents()).map(code => code.trim()),
        pythonBlocks, 'Rendered Python preserves every source block.');
      assert.ok(await page.locator('main pre').evaluateAll(blocks => blocks.every(block =>
        block.tabIndex === 0 && block.getAttribute('role') === 'region' && block.getAttribute('aria-label'))),
      'Every code/output block can be reached and identified by keyboard.');
      assert.equal(await page.locator('.book-nav a.current').getAttribute('href'), pageName);
      assert.equal(await page.locator('a[download][href$=".ipynb"]').count(), 0);

      const missingAnchors = await page.locator('a[href^="#"]').evaluateAll(links => links
        .map(link => decodeURIComponent(link.getAttribute('href').slice(1)))
        .filter(id => id && !document.getElementById(id)));
      assert.deepEqual(missingAnchors, [], 'All in-page links have targets.');

      const image = page.locator('main img[src*="extreme-risk-shapes"]');
      assert.equal(await image.count(), 1);
      await image.scrollIntoViewIfNeeded();
      await image.evaluate(img => img.decode());
      const loaded = await image.evaluate(img => ({width: img.naturalWidth, currentSrc: img.currentSrc}));
      assert.ok([400, 720].includes(loaded.width));
      assert.equal(loaded.currentSrc.includes('-mobile.svg'), width <= 650,
        `Responsive figure variant at ${width}px`);

      await page.addScriptTag({path: require.resolve('axe-core/axe.min.js')});
      const violations = await page.evaluate(async () => (await axe.run(document, {
        runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa']},
      })).violations.map(item => ({id: item.id, targets: item.nodes.map(node => node.target)})));
      assert.deepEqual(violations, [], JSON.stringify({width, theme, violations}));

      if (theme === 'light' && [390, 1440].includes(width)) {
        await image.screenshot({path: path.join(output, `extreme-risk-figure-${width}.png`)});
        await page.locator('main pre code.language-python').first().locator('..').screenshot({
          path: path.join(output, `extreme-risk-python-${width}.png`),
        });
      }
      viewports.push({width, theme, status: 'passed'});
    }

    // Read the standalone SVG so text bounds and original data can be inspected.
    const svgPage = await browser.newPage();
    for (const suffix of ['', '-mobile']) {
      const filename = `extreme-risk-shapes${suffix}.svg`;
      await svgPage.goto(`${base}/assets/charts/${filename}`);
      await svgPage.evaluate(() => document.fonts.ready);
      const svgState = await svgPage.locator('svg').evaluate(svg => {
        const bounds = svg.viewBox.baseVal;
        const clipped = [...svg.querySelectorAll('text')].flatMap(text => {
          const box = text.getBBox();
          return box.x < -0.5 || box.y < -0.5 || box.x + box.width > bounds.width + 0.5 ||
            box.y + box.height > bounds.height + 0.5 ? [{text: text.textContent, x: box.x, width: box.width}] : [];
        });
        const counts = Object.fromEntries(['Regular', 'LeftTail'].map(series => [series,
          [...svg.querySelectorAll(`rect[data-series="${series}"]`)].map(bar => Number(bar.dataset.count))]));
        return {clipped, counts};
      });
      assert.deepEqual(svgState.clipped, [], `${filename}: clipped text`);
      assert.deepEqual(svgState.counts, {Regular: [0, 1, 3, 2, 3, 1], LeftTail: [1, 0, 0, 9, 0, 0]});
      figures.push({filename, ...svgState, status: 'passed'});
    }
    await svgPage.close();

    await page.setViewportSize({width: 320, height: 1100});
    await page.goto(`${base}/${pageName}`);
    const codeIndex = await page.locator('main pre').evaluateAll(blocks =>
      blocks.findIndex(block => block.scrollWidth > block.clientWidth + 10));
    assert.ok(codeIndex >= 0, 'The narrow viewport exercises a horizontally scrolling code block.');
    const scrollingCode = page.locator('main pre').nth(codeIndex);
    await scrollingCode.focus();
    await scrollingCode.evaluate(block => { block.scrollLeft = 0; });
    await page.keyboard.press('ArrowRight');
    await page.waitForFunction(index => document.querySelectorAll('main pre')[index].scrollLeft > 0, codeIndex);
    assert.equal(await scrollingCode.evaluate(block => block === document.activeElement), true);

    // Sidebar and search are reachable at mobile width through the book menu.
    await page.locator('#menu-button').click();
    assert.equal(await page.locator('#menu-button').getAttribute('aria-expanded'), 'true');
    await page.locator('#search-button').click();
    assert.equal(await page.locator('#search-input').evaluate(input => input === document.activeElement), true);
    for (const query of ['Skewness', 'ความเบ้']) {
      await page.locator('#search-input').fill(query);
      await page.waitForFunction(() => document.querySelectorAll('#search-results a[href^="extreme-risk.html"]').length > 0);
    }
    await page.locator('#search-input').fill('zzzz-extreme-risk-no-matches-9273');
    assert.equal(await page.locator('#search-results a').count(), 0);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#search-dialog').evaluate(dialog => dialog.open), false);

    await page.setViewportSize({width: 1440, height: 1100});
    const chapterNavigation = page.locator('nav[aria-label="บทเรียนก่อนหน้าและถัดไป"]');
    for (const adjacent of [config.pages[pageIndex - 1], config.pages[pageIndex + 1]].filter(Boolean)) {
      const href = `${adjacent.file}.html`;
      const link = chapterNavigation.locator(`a[href="${href}"]`);
      assert.equal(await link.count(), 1, `Chapter navigation includes ${href}`);
      await link.click();
      assert.ok(page.url().endsWith(`/${href}`));
      await page.goto(`${base}/${pageName}`);
    }

    const downloadable = page.locator('a[download][href$="finance_tools.py"]').first();
    const waiting = page.waitForEvent('download');
    await downloadable.click();
    const download = await waiting;
    assert.equal(download.suggestedFilename(), 'finance_tools.py');
    const downloadedPath = path.join(output, 'extreme-risk-downloaded-finance_tools.py');
    await download.saveAs(downloadedPath);
    assert.deepEqual(fs.readFileSync(downloadedPath), moduleBytes, 'The downloaded module exactly matches the source.');

    const details = page.locator('main details').first();
    assert.ok(await page.locator('main details').count() > 0, 'Exercises provide native reveal controls.');
    await details.locator('summary').focus();
    await page.keyboard.press('Enter');
    assert.equal(await details.getAttribute('open'), '');

    await page.goto(pathToFileURL(path.join(root, '_site', pageName)).href);
    assert.deepEqual((await page.locator('main pre code.language-python').allTextContents()).map(code => code.trim()), pythonBlocks);
    const offlineImage = page.locator('main img[src*="extreme-risk-shapes"]');
    await offlineImage.scrollIntoViewIfNeeded();
    await offlineImage.evaluate(img => img.decode());
    const localDownload = await page.locator('a[download][href$="finance_tools.py"]').first().getAttribute('href');
    assert.deepEqual(fs.readFileSync(path.resolve(root, '_site', localDownload)), moduleBytes);

    const nojs = await browser.newPage({javaScriptEnabled: false});
    await nojs.goto(`${base}/${pageName}`);
    assert.equal(await nojs.locator('main pre code.language-python').count(), pythonBlocks.length);
    assert.ok(await nojs.locator('.katex').count() > 0);
    assert.equal(await nojs.locator('main img[src*="extreme-risk-shapes"]').count(), 1);
    await nojs.locator('main details summary').first().click();
    assert.equal(await nojs.locator('main details').first().getAttribute('open'), '');
    await nojs.close();
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, 'extreme-risk-browser-report.json'), JSON.stringify({
      status: 'passed', timestamp: new Date().toISOString(), viewports, figures,
      pythonBlocks: pythonBlocks.length,
      checks: ['math', 'all in-page anchors', 'book and chapter navigation', 'Thai and English search',
        'empty search', 'keyboard code scrolling', 'module download exact bytes', 'exercise keyboard use',
        'offline source and assets', 'no-JS lesson', 'WCAG A/AA'],
    }, null, 2));
    console.log('Extreme Risk browser checks passed: 8 viewport/theme pairs, SVG data/bounds, code, navigation, download, search, accessibility, offline and no-JS.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
