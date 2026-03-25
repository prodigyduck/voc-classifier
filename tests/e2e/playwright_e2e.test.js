const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://100.100.153.74:8501';
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
const REPORT_PATH = path.join(__dirname, 'test_report.md');

if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const results = [];

async function safe(fn, page, name) {
  try {
    await fn();
    results.push({ name, status: 'PASS' });
  } catch (err) {
    console.error(`[ERROR] ${name}:`, err.message || err);
    results.push({ name, status: 'FAIL', error: String(err) });
  }
  const filename = path.join(SCREENSHOT_DIR, `${name.replace(/\s+/g, '_')}.png`);
  try {
    await page.screenshot({ path: filename, fullPage: true });
  } catch (err) {
    console.error(`[WARN] screenshot failed for ${name}:`, err.message || err);
  }
}

module.exports = (config) => {
  // This file is intended to be executed via Playwright mcp which provides
  // browser_navigate, browser_click, etc. If run directly with Playwright,
  // it will attempt to use the Playwright API.
};

// Alternative direct Playwright runner for local execution (node ./playwright_e2e.test.js)
if (require.main === module) {
  (async () => {
    const { chromium } = require('playwright');
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    // 1. Dashboard Page
    await safe(async () => {
      await page.goto(BASE_URL);
      // Verify metrics exist by checking some common selectors/texts
      await page.waitForTimeout(1000);
      const text = await page.content();
      if (!/Total VOCs|UI Related VOCs|Total/.test(text)) {
        throw new Error('Dashboard metrics not found');
      }
    }, page, '01_Dashboard_Page');

    // 2. VOC List Page
    await safe(async () => {
      // Try navigate via link text or known path
      await page.goto(BASE_URL + '/voc_list');
      await page.waitForTimeout(1000);
      // Filter by status/priority - try selecting some controls if available
      // Try to find select inputs
      const statusSelect = await page.$('select[name="status"], select#status');
      if (statusSelect) await statusSelect.selectOption({ index: 1 }).catch(()=>{});
      const prioritySelect = await page.$('select[name="priority"], select#priority');
      if (prioritySelect) await prioritySelect.selectOption({ label: 'MEDIUM' }).catch(()=>{});
      const uiOnly = await page.$('input[name="ui_related"], input#ui_related, input[type="checkbox"][name="ui_related"]');
      if (uiOnly) await uiOnly.check().catch(()=>{});
      await page.waitForTimeout(500);
    }, page, '02_VOC_List_Page');

    // 3. VOC Input Page
    await safe(async () => {
      await page.goto(BASE_URL + '/voc_input');
      await page.waitForTimeout(500);
      // Fill form fields with best-effort selectors
      const fillIf = async (selectors, value) => {
        for (const s of selectors) {
          const el = await page.$(s);
          if (el) { await el.fill(value).catch(()=>{}); return true; }
        }
        return false;
      };
      await fillIf(['input[name="title"]', 'input#title', 'input[placeholder*="title"]'], 'Test VOC');
      await fillIf(['textarea[name="content"]', 'textarea#content', 'textarea[placeholder*="content"]'], 'Test content');
      const pr = await page.$('select[name="priority"], select#priority');
      if (pr) await pr.selectOption({ label: 'MEDIUM' }).catch(()=>{});
      await fillIf(['input[name="submitted_by"]', 'input#submitted_by', 'input[placeholder*="submitted"]'], 'Test User');
      const uiChk = await page.$('input[name="ui_related"], input#ui_related, input[type="checkbox"][name="ui_related"]');
      if (uiChk) await uiChk.check().catch(()=>{});
      // Submit
      const submitBtn = await page.$('button[type="submit"], button:has-text("Submit"), button:has-text("등록")');
      if (submitBtn) await submitBtn.click();
      await page.waitForTimeout(1000);
      const content = await page.content();
      if (!/success|성공|등록되었습니다|submitted/i.test(content)) {
        throw new Error('Submission success message not found');
      }
    }, page, '03_VOC_Input_Page');

    // 4. Classification Model Page
    await safe(async () => {
      await page.goto(BASE_URL + '/classification_model');
      await page.waitForTimeout(500);
      const trainBtn = await page.$('button:has-text("Train Model"), button:has-text("학습"), button#train');
      if (trainBtn) await trainBtn.click();
      await page.waitForTimeout(1000);
      const content = await page.content();
      if (!/training|success|완료|학습 완료/i.test(content)) {
        throw new Error('Model training success message not found');
      }
    }, page, '04_Classification_Model_Page');

    // 5. UI Improvement Tracking Page
    await safe(async () => {
      await page.goto(BASE_URL + '/ui_improvement');
      await page.waitForTimeout(500);
      const text = await page.content();
      if (!/analytics|improvement|개선|통계/i.test(text)) {
        throw new Error('Analytics metrics not found');
      }
      await page.fill('input[name="improvement_name"], input#improvement_name, input[placeholder*="improvement"]', 'Test Improvement').catch(()=>{});
      await page.fill('textarea[name="description"], textarea#description, textarea[placeholder*="description"]', 'Test description').catch(()=>{});
      const submitBtn = await page.$('button[type="submit"], button:has-text("Submit"), button:has-text("등록")');
      if (submitBtn) await submitBtn.click();
      await page.waitForTimeout(1000);
      const content2 = await page.content();
      if (!/success|성공|등록되었습니다|submitted/i.test(content2)) {
        throw new Error('Improvement submission success message not found');
      }
    }, page, '05_UI_Improvement_Tracking_Page');

    // 6. Language Switching
    await safe(async () => {
      await page.goto(BASE_URL);
      await page.waitForTimeout(500);
      // Try to select English from language select
      const langSelect = await page.$('select[name="language"], select#language');
      if (langSelect) {
        await langSelect.selectOption({ label: 'English' }).catch(()=>{});
        await page.waitForTimeout(500);
        const content = await page.content();
        if (!/English|Home|Dashboard|Total VOCs/i.test(content)) {
          throw new Error('English text not detected after switching');
        }
      } else {
        // Try clicking a language toggle
        const enBtn = await page.$('button:has-text("English"), a:has-text("English")');
        if (enBtn) {
          await enBtn.click();
          await page.waitForTimeout(500);
          const content = await page.content();
          if (!/English|Home|Dashboard|Total VOCs/i.test(content)) throw new Error('English text not detected after toggling');
        } else {
          throw new Error('Language selector not found');
        }
      }
    }, page, '06_Language_Switching');

    // Write report
    const md = ['# E2E Test Report', '', `Base URL: ${BASE_URL}`, '', '## Results', ''];
    for (const r of results) {
      md.push(`- ${r.name}: ${r.status}${r.error ? ' - ' + r.error : ''}`);
    }
    fs.writeFileSync(REPORT_PATH, md.join('\n'));

    await browser.close();
    console.log('E2E run complete. Report at', REPORT_PATH);
  })();
}
