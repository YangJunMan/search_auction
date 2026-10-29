function chooseSavedSearch(entries, requested = '') {
  const usable = entries.map((entry, index) => ({...entry, index})).filter(entry => entry.name && entry.onclick && !/삭제|delete|remove|del_/i.test(entry.name + ' ' + entry.onclick));
  const choice = requested ? usable.find(entry => entry.name === requested) : usable.find(entry => entry.name === '인천조건검색') || usable[0];
  return choice ? choice.index : -1;
}

async function runSearch(username, password, requested = '') {
  try {
    const probe = await fetch('https://www.my-auction.co.kr/member/login.php', { method: 'GET', signal: AbortSignal.timeout(8000) });
    console.info('auction connectivity probe: HTTP', probe.status);
    await probe.body?.cancel();
  } catch (error) {
    const code = error.cause?.code;
    console.error('auction connectivity probe:', typeof code === 'string' && /^[A-Z_]+$/.test(code) ? code : error.name);
  }
  const { default: puppeteer } = await import('puppeteer-core');
  const { default: chromium } = await import('@sparticuz/chromium');
  const browser = await puppeteer.launch({ args: chromium.args, executablePath: await chromium.executablePath(), headless: true });
  let stage = 'browser';
  try {
    const page = await browser.newPage();
    page.setDefaultTimeout(20000);
    let loginRejected = false;
    page.on('dialog', async dialog => {
      loginRejected = true;
      const alertText = dialog.message();
      const alertClass = /error2/i.test(alertText) ? 'error2' : /error1/i.test(alertText) ? 'error1' : /중복|접속|로그인/i.test(alertText) ? 'login-related' : 'other';
      console.error('auction login dialog class:', alertClass);
      await dialog.dismiss();
    });
    stage = 'login_page';
    for (let attempt = 0; attempt < 2; attempt++) {
      try { await page.goto('https://www.my-auction.co.kr/member/login.php', {waitUntil:'domcontentloaded', timeout: 10000}); break; }
      catch (error) { if (attempt === 1) throw error; }
    }
    stage = 'login_form';
    await page.type('#id', username);
    await page.type('#passwd', password);
    stage = 'login_submit';
    await Promise.all([
      page.waitForNavigation({waitUntil:'domcontentloaded',timeout:20000}).catch(() => null),
      page.click('#btn_login'),
    ]);
    if (loginRejected) throw new Error('AUTH_FAILED');
    stage = 'search_page';
    await page.goto('https://www.my-auction.co.kr/auction/search.php', {waitUntil:'domcontentloaded'});
    if (loginRejected || /member\/login/i.test(page.url())) throw new Error('AUTH_FAILED');
    const signedIn = await page.evaluate(() => Array.from(document.querySelectorAll('a')).some(a => /logout/i.test(a.getAttribute('href') || '') || /로그아웃/.test((a.textContent || '').replace(/\s/g, ''))));
    if (!signedIn) throw new Error('AUTH_UNCONFIRMED');
    await page.waitForSelector('#sc_tab');
    const tab = await page.$$('#sc_tab a');
    let found = false;
    for (const item of tab) {
      const text = await item.evaluate(el => el.textContent.trim());
      if (text === '내 검색조건') { await item.click(); found = true; break; }
    }
    if (!found) throw new Error('SEARCH_UNAVAILABLE');
    await page.waitForSelector('#sc_list a');
    const searches = await page.$$('#sc_list a');
    const entries = await Promise.all(searches.map(item => item.evaluate(el => ({name:el.textContent.trim(),onclick:el.getAttribute('onclick') || ''}))));
    const chosen = chooseSavedSearch(entries, requested);
    if (chosen < 0) throw new Error('SEARCH_MISSING');
    const searchName = entries[chosen].name;
    await searches[chosen].click();
    await page.waitForSelector('table.tbl_auction_list tbody tr');
    const items = await page.$$eval('table.tbl_auction_list tbody tr', rows => rows.map(row => {
      const cells = row.querySelectorAll('td');
      if (cells.length < 8) return null;
      const parts = cells[2].innerText.trim().split('\n');
      const prices = cells[4].innerText.trim().split('\n');
      return { '용도':cells[2].querySelector('strong')?.innerText.trim() || '', '사건번호':parts[1] || '', '소재지':cells[3].querySelector('li')?.innerText.trim() || '', '감정가':prices[0] || '', '최저가':prices[1] || '', '매각기일':cells[6].innerText.trim().split('\n')[0], '현재상태':cells[5].innerText.trim() };
    }).filter(Boolean));
    return {items, searchName};
  } catch (error) {
    console.error('auction search stage:', stage, 'error type:', error.name, 'network code:', String(error.message).match(/net::ERR_[A-Z_]+/)?.[0] || 'none');
    throw error;
  } finally { await browser.close(); }
}

function makeHandler(runner = runSearch) {
  return async function handler(req,res) {
    res.setHeader('Cache-Control','no-store');
    res.setHeader('X-Content-Type-Options','nosniff');
    if (req.method !== 'POST') return res.status(405).json({error:'요청 방법을 확인해 주세요.'});
    const {username,password,searchName = ''} = req.body || {};
    if (typeof username !== 'string' || typeof password !== 'string' || !username.trim() || !password || username.length>256 || password.length>256 || typeof searchName !== 'string' || searchName.length > 100) return res.status(400).json({error:'아이디와 비밀번호를 입력해 주세요.'});
    try { const result = await runner(username,password,searchName.trim()); return res.status(200).json(Array.isArray(result) ? {items:result} : result); }
    catch (e) {
      const errors={AUTH_UNCONFIRMED:'로그인 상태를 확인하지 못했습니다. 잠시 후 다시 시도해 주세요.', AUTH_FAILED:'로그인을 완료하지 못했습니다. 잠시 후 다시 시도하거나 문의해 주세요.', SEARCH_MISSING:'저장된 검색 조건을 찾을 수 없습니다.', SEARCH_UNAVAILABLE:'검색 화면을 불러올 수 없습니다.'};
      return res.status(502).json({error:errors[e.message] || '처리하지 못했습니다. 잠시 후 다시 시도해 주세요.'});
    }
  };
}
module.exports = makeHandler();
module.exports.makeHandler = makeHandler;

module.exports.chooseSavedSearch = chooseSavedSearch;
