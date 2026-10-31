const { geocodeItems } = require('../lib/geo');
const { pageUrls } = require('../lib/pagination');
const { normalizeDetailUrl } = require('../lib/detail-url');
const { validateFirstPage } = require('../lib/result-validation');
const { sealSession, openSession, readSessionCookie, cookieHeader, clearCookie } = require('../lib/session');

function chooseSavedSearch(entries, requested = '') {
  const usable = entries.map((entry, index) => ({...entry, index})).filter(entry => entry.name && entry.onclick && !/삭제|delete|remove|del_/i.test(entry.name + ' ' + entry.onclick));
  const choice = requested ? usable.find(entry => entry.name === requested) : usable.find(entry => entry.name === '인천조건검색') || usable[0];
  return choice ? choice.index : -1;
}

async function runSearch(username, password, requested = '', sessionCookies = null) {
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
    if (sessionCookies) {
      stage = 'restore_session';
      await browser.setCookie(...sessionCookies);
    } else {
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
    }
    stage = 'search_page';
    await page.goto('https://www.my-auction.co.kr/auction/search.php', {waitUntil:'domcontentloaded'});
    if (loginRejected || /member\/login/i.test(page.url())) throw new Error(sessionCookies ? 'SESSION_EXPIRED' : 'AUTH_FAILED');
    const signedIn = await page.evaluate(() => Array.from(document.querySelectorAll('a')).some(a => /logout/i.test(a.getAttribute('href') || '') || /로그아웃/.test((a.textContent || '').replace(/\s/g, ''))));
    if (!signedIn) throw new Error(sessionCookies ? 'SESSION_EXPIRED' : 'AUTH_UNCONFIRMED');
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
    await page.waitForFunction(() => {
      const rows = Array.from(document.querySelectorAll('table.tbl_auction_list tbody tr'));
      const hasData = rows.some(row => row.querySelectorAll('td').length >= 8);
      const heading = Array.from(document.querySelectorAll('.auction_result h4')).map(el => el.innerText).find(text => /검색결과/.test(text));
      return hasData || /검색결과\s*:\s*0\s*건/.test(heading || '');
    }, {timeout:20000});
    const parseRows = rows => rows.map(row => {
      const cells = row.querySelectorAll('td');
      if (cells.length < 8) return null;
      const parts = cells[2].innerText.trim().split('\n');
      const prices = cells[4].innerText.trim().split('\n');
      const locations = cells[3].querySelectorAll('li');
      return { '용도':cells[2].querySelector('strong')?.innerText.trim() || '', '사건번호':parts[1] || '', '소재지':locations[0]?.innerText.trim() || '', '감정가':prices[0] || '', '최저가':prices[1] || '', '매각기일':cells[6].innerText.trim().split('\n')[0], '면적':locations[1]?.innerText.trim() || '', '특수권리':Array.from(cells[3].querySelectorAll('span.refer a')).map(a => a.innerText.trim()).filter(Boolean).join(' '), '현재상태':cells[5].innerText.trim(), '상세주소':cells[3].querySelector('a[href*="/view/"]')?.getAttribute('href') || '' };
    }).filter(Boolean);
    const selector = 'table.tbl_auction_list tbody tr';
    const firstItems = await page.$$eval(selector, parseRows);
    const total = await page.evaluate(() => {
      const heading = Array.from(document.querySelectorAll('.auction_result h4')).map(e => e.innerText).find(t => /검색결과/.test(t));
      const match = heading?.match(/검색결과\s*:\s*([\d,]+)\s*건/);
      return match ? Number(match[1].replace(/,/g, '')) : null;
    });
    validateFirstPage(firstItems, total);
    const lastHref = await page.$eval('#youtube_number a.ytb_end', a => a.getAttribute('href')).catch(() => null);
    const urls = pageUrls(page.url(), lastHref);
    const chunks = new Array(urls.length);
    let nextPage = 0;
    stage = 'search_pages';
    async function collectPages() {
      const worker = await browser.newPage();
      worker.setDefaultTimeout(20000);
      try {
        while (nextPage < urls.length) {
          const index = nextPage++;
          for (let attempt = 0; attempt < 2; attempt++) {
            try {
              await worker.goto(urls[index], {waitUntil:'domcontentloaded', timeout:20000});
              await worker.waitForSelector(selector);
              chunks[index] = await worker.$$eval(selector, parseRows);
              if (!chunks[index].length) throw new Error('SEARCH_PAGE_EMPTY');
              break;
            } catch (error) { if (attempt === 1) throw error; }
          }
        }
      } finally { await worker.close(); }
    }
    await Promise.all(Array.from({length:Math.min(2, urls.length)}, collectPages));
    const items = firstItems.concat(...chunks).map(item => ({...item, '상세주소':normalizeDetailUrl(item['상세주소'])}));
    stage = 'geocoding';
    const enriched = await geocodeItems(items, process.env.KAKAO_REST_API_KEY);
    const cookies = (await browser.cookies()).filter(c => /(^|\.)my-auction\.co\.kr$/i.test(c.domain) && !/^(_ga|_gid|_gcl|_fbp)/i.test(c.name)).map(c => {
      const out={name:c.name,value:c.value,domain:c.domain,path:c.path,secure:c.secure,httpOnly:c.httpOnly};
      if (c.expires > 0) out.expires=c.expires;
      if (c.sameSite) out.sameSite=c.sameSite;
      return out;
    });
    return {items: enriched, searchName, sessionCookies:cookies};
  } catch (error) {
    console.error('auction search stage:', stage, 'error type:', error.name, 'network code:', String(error.message).match(/net::ERR_[A-Z_]+/)?.[0] || 'none');
    throw error;
  } finally { await browser.close(); }
}

function makeHandler(runner = runSearch, getSecret = () => process.env.SESSION_SECRET || process.env.KAKAO_REST_API_KEY) {
  return async function handler(req,res) {
    res.setHeader('Cache-Control','no-store');
    res.setHeader('X-Content-Type-Options','nosniff');
    const headers=req.headers || {};
    if (headers.origin && headers.host && headers.origin !== `https://${headers.host}` && headers.origin !== `http://${headers.host}`) return res.status(403).json({error:'요청 출처를 확인해 주세요.'});
    const token=readSessionCookie(headers.cookie);
    const session=token ? openSession(token,getSecret()) : null;
    if (req.method === 'GET') return res.status(200).json({authenticated:!!session});
    if (req.method === 'DELETE') { res.setHeader('Set-Cookie',clearCookie()); return res.status(200).json({ok:true}); }
    if (req.method !== 'POST') return res.status(405).json({error:'요청 방법을 확인해 주세요.'});
    const {username,password,searchName = ''} = req.body || {};
    const credentials=typeof username === 'string' && typeof password === 'string' && !!username.trim() && !!password && username.length<=256 && password.length<=256;
    if (typeof searchName !== 'string' || searchName.length > 100) return res.status(400).json({error:'검색 조건 이름을 확인해 주세요.'});
    if (!credentials && !session) {
      if (token) return res.status(401).json({error:'로그인 시간이 끝났습니다. 다시 로그인해 주세요.',code:'SESSION_EXPIRED'});
      return res.status(400).json({error:'아이디와 비밀번호를 입력해 주세요.'});
    }
    try {
      const result=await runner(credentials ? username : undefined,credentials ? password : undefined,searchName.trim(),credentials ? null : session);
      const {sessionCookies,...safeResult}=Array.isArray(result) ? {items:result} : result;
      let sessionAvailable=false;
      if (sessionCookies?.length) {
        try { res.setHeader('Set-Cookie',cookieHeader(sealSession(sessionCookies,getSecret()))); sessionAvailable=true; }
        catch (e) { console.error('session could not be saved:',e.message); }
      }
      return res.status(200).json({...safeResult,sessionAvailable});
    } catch (e) {
      const errors={AUTH_UNCONFIRMED:'로그인 상태를 확인하지 못했습니다. 잠시 후 다시 시도해 주세요.', AUTH_FAILED:'로그인을 완료하지 못했습니다. 잠시 후 다시 시도하거나 문의해 주세요.', SESSION_EXPIRED:'로그인 시간이 끝났습니다. 다시 로그인해 주세요.', SEARCH_MISSING:'저장된 검색 조건을 찾을 수 없습니다.', SEARCH_UNAVAILABLE:'검색 화면을 불러올 수 없습니다.', SEARCH_RESULT_UNREADABLE:'매물 목록을 확인하지 못했습니다. 잠시 후 다시 검색해 주세요.'};
      if (e.message === 'SESSION_EXPIRED') {res.setHeader('Set-Cookie',clearCookie()); return res.status(401).json({error:errors.SESSION_EXPIRED,code:'SESSION_EXPIRED'});}
      return res.status(502).json({error:errors[e.message] || '처리하지 못했습니다. 잠시 후 다시 시도해 주세요.'});
    }
  };
}
module.exports = makeHandler();
module.exports.makeHandler = makeHandler;

module.exports.chooseSavedSearch = chooseSavedSearch;
