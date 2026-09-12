/* Browser integration checks for the shipped static pages and teaching tools. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');
const axeSource = require('axe-core').source;

const base = process.env.PMT_PREVIEW_URL || 'http://127.0.0.1:8764';
const output = path.join(__dirname, 'output');
const pages = ['index', 'portfolio-insurance', 'glossary'];
const failures = [], passed = [], accessibility = [];
fs.mkdirSync(output, { recursive: true });
const format = (n, digits = 2) => Number(n).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });

async function check(name, run) {
  try { await run(); passed.push(name); console.log(`PASS ${name}`); }
  catch (error) { failures.push({ name, error: error.message }); console.error(`FAIL ${name}: ${error.message}`); }
}
async function ready(page, name) {
  await page.goto(`${base}/${name}.html`, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  if (name === 'portfolio-insurance') {
    await page.locator('#cppi-lab select').waitFor();
    await page.locator('#put-lab [data-component="CountUp"]').first().waitFor();
    await page.locator('#allocation-guide [data-component="Stepper"]').waitFor();
  }
}
async function metrics(container) { return container.locator('.metrics-row .rb-sr-only').allTextContents(); }
async function range(page, selector, value) {
  // Use the native setter to send the same input event React receives from a slider.
  await page.locator(selector).evaluate((element, newValue) => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(element, String(newValue));
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  }, value);
  await page.waitForFunction(({ selector, value }) => {
    const el = document.querySelector(selector);
    return el.value === String(value) && el.closest('.range-control').querySelector('output').textContent.includes(String(value));
  }, { selector, value });
}

(async () => {
  const models = await import(pathToFileURL(path.join(__dirname, '../src/math.mjs')).href);
  const browser = await chromium.launch({ headless: true });
  try {
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }, { width: 320, height: 844 }]) {
      for (const theme of ['light', 'dark']) {
        const context = await browser.newContext({ viewport });
        if (theme === 'dark') await context.addInitScript(() => localStorage.setItem('pmt-book-theme', 'dark'));
        const page = await context.newPage();
        const errors = [], badResponses = [], external = [];
        page.on('pageerror', e => errors.push(e.message));
        page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
        page.on('response', r => { if (r.status() >= 400) badResponses.push(`${r.status()} ${r.url()}`); });
        page.on('request', r => { if (/^https?:/.test(r.url()) && !r.url().startsWith(base)) external.push(r.url()); });
        for (const name of pages) {
          await check(`${name} ${viewport.width}px ${theme}: layout, assets, accessibility`, async () => {
            await ready(page, name);
            assert.equal(await page.locator('html').getAttribute('data-theme'), theme);
            const dimensions = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
            assert.ok(dimensions.scroll <= dimensions.viewport + 1, `Horizontal overflow: ${JSON.stringify(dimensions)}`);
            assert.equal(await page.locator('h1').count(), 1, 'One main heading');
            assert.equal(await page.locator('nav [aria-current="page"]').count(), 1, 'One active navigation link');
            assert.deepEqual(await page.locator('img').evaluateAll(images => images.filter(i => !i.complete || !i.naturalWidth).map(i => i.src)), [], 'Images load');
            await page.addScriptTag({ content: axeSource });
            const result = await page.evaluate(async () => {
              const report = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } });
              return report.violations.filter(v => ['serious', 'critical'].includes(v.impact) || v.id === 'color-contrast').map(v => ({ id: v.id, impact: v.impact, description: v.description, nodes: v.nodes.map(n => ({ target: n.target, failureSummary: n.failureSummary })) }));
            });
            accessibility.push({ page: name, width: viewport.width, theme, violations: result });
            assert.deepEqual(result, [], 'No serious/critical accessibility or color-contrast violations');
            assert.deepEqual(errors, [], 'No browser errors');
            assert.deepEqual(badResponses, [], 'No failed asset responses');
            assert.deepEqual(external, [], 'No external runtime or font requests');
          });
          if (viewport.width !== 320 && ['index', 'portfolio-insurance'].includes(name)) {
            const stem = name === 'index' ? 'welcome' : 'chapter';
            const size = viewport.width === 1440 ? 'desktop' : 'mobile';
            await page.screenshot({ path: path.join(output, `${stem}-${size}-${theme}.png`), fullPage: name === 'index', animations: 'disabled' });
            if (name === 'portfolio-insurance') {
              await page.locator('#cppi-lab').screenshot({ path: path.join(output, `cppi-${size}-${theme}.png`), animations: 'disabled' });
            }
          }
        }
        if (viewport.width < 1000) {
          await check(`Mobile navigation ${viewport.width}px ${theme}`, async () => {
            await ready(page, 'index');
            const menu = page.locator('#menu-button');
            await menu.click();
            assert.equal(await menu.getAttribute('aria-expanded'), 'true');
            await page.getByRole('navigation', { name: 'สารบัญ' }).getByRole('link', { name: 'Portfolio Insurance', exact: true }).click();
            await page.waitForURL('**/portfolio-insurance.html');
            assert.equal(await menu.getAttribute('aria-expanded'), 'false');
            await menu.click();
            await page.keyboard.press('Escape');
            assert.equal(await menu.getAttribute('aria-expanded'), 'false');
            assert.equal(await menu.evaluate(el => el === document.activeElement), true, 'Escape restores menu focus');
          });
        }
        await context.close();
      }
    }

    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
    const page = await context.newPage();
    await check('Book sidebar, full chapter contents and chapter section navigation', async () => {
      await ready(page, 'index');
      assert.equal(await page.locator('html').getAttribute('data-theme'), 'light', 'A fresh session defaults to the light book');
      assert.deepEqual(await page.getByRole('navigation', { name: 'สารบัญ', exact: true }).locator('a').allTextContents(), ['Welcome', 'Portfolio Insurance', 'อภิธานศัพท์']);
      await Promise.all([
        page.waitForURL('**/portfolio-insurance.html'),
        page.getByRole('navigation', { name: 'สารบัญ', exact: true }).getByRole('link', { name: 'Portfolio Insurance', exact: true }).click()
      ]);
      const contents = page.getByRole('navigation', { name: 'หัวข้อในหน้านี้', exact: true });
      assert.ok(await contents.locator('a').count() >= 10, 'A chapter-length contents list');
      const link = contents.locator('a').filter({ hasText: /CPPI/ }).first();
      const anchor = await link.getAttribute('href');
      await link.click();
      await page.waitForFunction(hash => decodeURIComponent(location.hash) === hash, anchor);
      assert.ok(await page.locator(`[id="${anchor.slice(1)}"]`).isVisible());
      await page.locator('.page-contents summary').click();
      assert.equal(await page.locator('.page-contents').getAttribute('open'), null);
      await page.locator('.page-contents summary').click();
      assert.notEqual(await page.locator('.page-contents').getAttribute('open'), null);
    });
    await check('Search: English, Thai, empty result, keyboard, Escape and return focus', async () => {
      await ready(page, 'index');
      await page.locator('#search-button').click();
      assert.equal(await page.locator('#search-input').evaluate(el => el === document.activeElement), true);
      await page.locator('#search-input').fill('CPPI');
      assert.ok(await page.locator('#search-results a').count() > 0, 'English matches');
      await page.locator('#search-input').fill('การป้องกัน');
      assert.ok(await page.locator('#search-results a').count() > 0, 'Thai matches');
      await page.locator('#search-input').fill('zzzz-no-matches-94281');
      assert.equal(await page.locator('#search-results a').count(), 0);
      assert.match(await page.locator('#search-status').textContent(), /ไม่พบผลลัพธ์/);
      await page.keyboard.press('Escape');
      await page.waitForFunction(() => !document.querySelector('#search-dialog').open);
      assert.equal(await page.locator('#search-dialog').evaluate(el => el.open), false);
      assert.equal(await page.locator('#search-button').evaluate(el => el === document.activeElement), true);
      await page.keyboard.press('Control+k');
      assert.equal(await page.locator('#search-dialog').evaluate(el => el.open), true);
      await page.locator('#search-input').fill('Cushion');
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => document.activeElement.parentElement.id), 'search-results');
      const sectionResult = page.locator('#search-results a[href*="#"]').first();
      const destination = new URL(await sectionResult.getAttribute('href'), base + '/').href;
      await sectionResult.focus();
      await Promise.all([page.waitForURL(destination), page.keyboard.press('Enter')]);
      await page.waitForLoadState('networkidle');
      assert.ok(new URL(page.url()).hash, 'Search follows a real section anchor');
      assert.ok(await page.evaluate(() => !!document.getElementById(decodeURIComponent(location.hash.slice(1)))));
    });
    await check('Theme button changes theme and persists across navigation', async () => {
      await ready(page, 'index');
      const before = await page.locator('html').getAttribute('data-theme');
      await page.locator('#theme-button').click();
      const after = before === 'dark' ? 'light' : 'dark';
      assert.equal(await page.locator('html').getAttribute('data-theme'), after);
      await ready(page, 'portfolio-insurance');
      assert.equal(await page.locator('html').getAttribute('data-theme'), after);
    });
    await check('Glossary filters English and Thai, reports no result and reveals direct anchors', async () => {
      await ready(page, 'glossary');
      const query = page.locator('#glossary-query');
      const terms = page.locator('.glossary-term');
      const total = await terms.count();
      assert.ok(total >= 20);
      await query.fill('Cushion');
      assert.equal(await page.locator('#cushion').evaluate(el => el.hidden), false);
      assert.ok(await page.locator('.glossary-term:not([hidden])').count() < total);
      await query.fill('ระดับมูลค่า');
      assert.equal(await page.locator('#floor').evaluate(el => el.hidden), false);
      assert.ok(await page.locator('.glossary-term:not([hidden])').count() > 0);
      await query.fill('unmatched-glossary-3492');
      assert.equal(await page.locator('.glossary-term:not([hidden])').count(), 0);
      assert.equal(await page.locator('.glossary-group:not([hidden])').count(), 0);
      assert.match(await page.locator('#glossary-status').textContent(), /ไม่พบคำศัพท์/);
      await page.evaluate(() => { location.hash = 'floor'; });
      await page.waitForFunction(() => document.querySelector('#glossary-query').value === '');
      assert.equal(await page.locator('#floor').evaluate(el => el.hidden), false);
      assert.equal(await page.locator('.glossary-term:not([hidden])').count(), total);
      await query.focus();
      await query.fill('Cushion');
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => document.activeElement.tagName), 'A', 'A filtered term return link is keyboard reachable');
      const returnLink = page.locator('#cushion a[href*="portfolio-insurance"]').first();
      const destination = new URL(await returnLink.getAttribute('href'), base + '/').href;
      await Promise.all([page.waitForURL(destination), returnLink.click()]);
      assert.ok(await page.evaluate(() => !!document.getElementById(decodeURIComponent(location.hash.slice(1)))));
    });
    await check('Notebook and chapter Markdown download as usable local source artifacts', async () => {
      await ready(page, 'portfolio-insurance');
      for (const [selector, filename] of [['a[download][href$=".ipynb"]', 'portfolio-insurance.ipynb'], ['a[download][href="portfolio-insurance.md"]', 'portfolio-insurance.md']]) {
        const waiting = page.waitForEvent('download');
        await page.locator(selector).click();
        const artifact = await waiting;
        assert.equal(artifact.suggestedFilename(), filename);
        const destination = path.join(output, filename);
        await artifact.saveAs(destination);
        assert.ok(fs.statSync(destination).size > 1000, `${filename} has real content`);
        if (filename.endsWith('.ipynb')) {
          const notebook = JSON.parse(fs.readFileSync(destination, 'utf8'));
          assert.equal(notebook.nbformat, 4);
          assert.ok(notebook.cells.some(cell => cell.cell_type === 'code'));
          assert.ok(notebook.cells.some(cell => cell.cell_type === 'markdown'));
          assert.ok(!notebook.cells.some(cell => cell.outputs?.some(result => result.output_type === 'error')));
        } else assert.match(fs.readFileSync(destination, 'utf8'), /Portfolio Insurance/);
      }
    });
    await check('CPPI defaults, all market scenarios and slider calculations', async () => {
      await ready(page, 'portfolio-insurance');
      const lab = page.locator('#cppi-lab');
      for (const scenario of ['crash', 'rally', 'whipsaw', 'recovery']) {
        await page.locator('#scenario').selectOption(scenario);
        const expected = models.simulate({ scenario });
        assert.deepEqual(await metrics(lab), [expected.metrics.final, expected.metrics.returnPct, expected.metrics.maxDrawdownPct].map(n => format(n)));
      }
      await range(page, '#floor-control', 80);
      await range(page, '#multiplier-control', 4);
      const expected = models.simulate({ scenario: 'recovery', floorPct: 80, multiplier: 4 });
      assert.deepEqual(await metrics(lab), [expected.metrics.final, expected.metrics.returnPct, expected.metrics.maxDrawdownPct].map(n => format(n)));
      assert.equal(await lab.locator('.allocation-snapshot .rb-sr-only').textContent(), '80.0');
      assert.equal(await lab.locator('.allocation-bar span').evaluate(el => el.style.width), '80%');
      await lab.locator('.data-details summary').click();
      assert.equal(await lab.locator('tbody tr').count(), 13);
      const last = await lab.locator('tbody tr').last().locator('td').allTextContents();
      const row = expected.rows.at(-1);
      assert.deepEqual(last, [row.cppi, row.buyHold, row.constantMix, row.floor, row.exposure].map(n => format(n)));
      await page.locator('#floor-control').focus();
      await page.keyboard.press('ArrowRight');
      assert.equal(await page.locator('#floor-control').inputValue(), '81', 'Slider keyboard support');
      await lab.getByRole('button', { name: 'คืนค่าเริ่มต้น' }).click();
      assert.equal(await page.locator('#floor-control').inputValue(), '90');
      assert.equal(await page.locator('#multiplier-control').inputValue(), '3');
      assert.equal(await page.locator('#scenario').inputValue(), 'crash');
    });
    await check('Saved scenarios recall values, remain keyboard accessible and export exact CSV', async () => {
      await ready(page, 'portfolio-insurance');
      const lab = page.locator('#cppi-lab');
      await page.locator('#scenario').selectOption('rally');
      await range(page, '#floor-control', 85);
      await range(page, '#multiplier-control', 2.5);
      await lab.getByRole('button', { name: 'บันทึกชุดทดลองนี้' }).click();
      assert.equal(await lab.locator('[data-component="AnimatedList"] button').count(), 1);
      await page.locator('#scenario').selectOption('crash');
      await range(page, '#floor-control', 95);
      await lab.locator('[data-component="AnimatedList"] button').click();
      assert.equal(await page.locator('#scenario').inputValue(), 'rally');
      assert.equal(await page.locator('#floor-control').inputValue(), '85');
      assert.equal(await page.locator('#multiplier-control').inputValue(), '2.5');
      assert.equal(await lab.locator('[data-component="AnimatedList"] button').getAttribute('aria-pressed'), 'true');
      await lab.getByRole('button', { name: 'บันทึกชุดทดลองนี้' }).click();
      const runButtons = lab.locator('[data-component="AnimatedList"] button');
      await runButtons.first().focus();
      await page.keyboard.press('ArrowDown');
      assert.equal(await runButtons.nth(1).evaluate(el => el === document.activeElement), true);
      await page.keyboard.press('Tab');
      assert.equal(await runButtons.nth(1).evaluate(el => el === document.activeElement), false, 'Tab exits the list normally');
      const pending = page.waitForEvent('download');
      await lab.getByRole('button', { name: 'ดาวน์โหลด CSV' }).click();
      const download = await pending;
      assert.match(download.suggestedFilename(), /^cppi-rally-floor-85-m-2\.5\.csv$/);
      const destination = path.join(output, download.suggestedFilename());
      await download.saveAs(destination);
      assert.equal(fs.readFileSync(destination, 'utf8').replace(/^\uFEFF/, ''), models.toCSV(models.simulate({ scenario: 'rally', floorPct: 85, multiplier: 2.5 })));
      for (let i = 0; i < 6; i++) await lab.getByRole('button', { name: 'บันทึกชุดทดลองนี้' }).click();
      assert.equal(await runButtons.count(), 6, 'History is bounded to six runs');
    });
    await check('Protective put payoff, wealth, cost and profit stay consistent', async () => {
      await ready(page, 'portfolio-insurance');
      const put = page.locator('#put-lab');
      assert.deepEqual(await metrics(put), ['10.00', '90.00', '-14.00']);
      await range(page, '#put-strike', 100);
      await range(page, '#put-premium', 6.5);
      await range(page, '#put-terminal', 70);
      assert.deepEqual(await metrics(put), ['30.00', '100.00', '-6.50']);
      assert.match(await put.locator('.result-insight strong').textContent(), /มูลค่า 100\.00 − ต้นทุน 106\.50 = -6\.50/);
      await range(page, '#put-terminal', 130);
      assert.deepEqual(await metrics(put), ['0.00', '130.00', '23.50']);
      await put.locator('summary').click();
      assert.equal(await put.locator('tbody tr').count(), 21);
      await range(page, '#put-strike', 120);
      assert.ok(Number(await page.locator('#put-premium').inputValue()) >= 20, 'Strike 120 respects the minimum premium bound');
      assert.equal(await page.locator('#put-premium').getAttribute('min'), '20');
    });
    await check('Stepper all three stages and three real React Bits families', async () => {
      await ready(page, 'portfolio-insurance');
      const guide = page.locator('[data-component="Stepper"]');
      assert.equal(await guide.count(), 1);
      assert.equal(await guide.getByRole('button', { name: 'ย้อนกลับ', exact: true }).isDisabled(), true);
      assert.match(await guide.locator('.rb-step-progress').textContent(), /ขั้น 1 จาก 3/);
      await guide.getByRole('button', { name: 'ถัดไป', exact: true }).click();
      assert.match(await guide.locator('.rb-step-progress').textContent(), /ขั้น 2 จาก 3/);
      assert.match(await guide.locator('.rb-step-panel').textContent(), /100 − 90 = 10/);
      await guide.getByRole('button', { name: 'ถัดไป', exact: true }).click();
      assert.match(await guide.locator('.rb-step-progress').textContent(), /ขั้น 3 จาก 3/);
      assert.match(await guide.locator('.rb-step-panel').textContent(), /30 × 0.6 \+ 70 = 88/);
      assert.equal(await guide.getByRole('button', { name: 'ถัดไป', exact: true }).isDisabled(), true);
      await guide.getByRole('button', { name: 'ย้อนกลับ', exact: true }).click();
      assert.match(await guide.locator('.rb-step-progress').textContent(), /ขั้น 2 จาก 3/);
      await guide.locator('.rb-step-indicator').first().click();
      assert.match(await guide.locator('.rb-step-progress').textContent(), /ขั้น 1 จาก 3/);
      assert.ok(await page.locator('[data-component="CountUp"]').count() > 0);
      await ready(page, 'portfolio-insurance');
      await page.getByRole('button', { name: 'บันทึกชุดทดลองนี้' }).click();
      assert.equal(await page.locator('[data-component="AnimatedList"]').count(), 1);
    });
    await context.close();

    const reduced = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    const reducedPage = await reduced.newPage();
    await check('Reduced motion preserves final numbers, new rows and stage meaning', async () => {
      await ready(reducedPage, 'portfolio-insurance');
      await reducedPage.locator('#scenario').selectOption('rally');
      const values = await reducedPage.locator('[data-component="CountUp"]').evaluateAll(nodes => nodes.map(el => [el.querySelector('[aria-hidden]').textContent, el.querySelector('.rb-sr-only').textContent]));
      assert.ok(values.every(([visual, final]) => visual === final), 'Visual numbers immediately match accessible final values');
      await reducedPage.getByRole('button', { name: 'บันทึกชุดทดลองนี้' }).click();
      const row = reducedPage.locator('[data-component="AnimatedList"] li').first();
      assert.equal(await row.evaluate(el => getComputedStyle(el).opacity), '1');
      await ready(reducedPage, 'portfolio-insurance');
      const guide = reducedPage.locator('[data-component="Stepper"]');
      await guide.getByRole('button', { name: 'ถัดไป', exact: true }).click();
      assert.match(await guide.locator('.rb-step-progress').textContent(), /ขั้น 2 จาก 3/);
      assert.match(await guide.locator('.rb-step-panel').textContent(), /100 − 90 = 10/);
    });
    await reduced.close();
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(output, 'browser-results.json'), JSON.stringify({ base, passed, failures, accessibility }, null, 2) + '\n');
  }
  console.log(`\n${passed.length} checks passed; ${failures.length} failed. Evidence: qa/output/browser-results.json`);
  if (failures.length) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
