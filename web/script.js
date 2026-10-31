const form = document.querySelector('#login-form');
const password = document.querySelector('#password');
const toggle = document.querySelector('#toggle');
const message = document.querySelector('#login-message');
const submit = form.querySelector('.submit');
const result = document.querySelector('#search-results');
const grid = document.querySelector('#result-grid');
const query = document.querySelector('#result-query');
const sort = document.querySelector('#result-sort');
const count = document.querySelector('#results-count');
const use = document.querySelector('#result-use');
const minDistance = document.querySelector('#result-min-distance');
const maxDistance = document.querySelector('#result-max-distance');
const recommended = document.querySelector('#result-recommended');
const previous = document.querySelector('#result-prev');
const next = document.querySelector('#result-next');
const pageLabel = document.querySelector('#result-page-label');
let currentPage = 1;
let visibleItems = [];
const pageSize = 12;
const empty = document.querySelector('#result-empty');
let items = [];
let maps = [];

function displayResults() {
  maps.forEach(map => map.remove());
  maps = [];
  grid.replaceChildren();
  const keyword = query.value.trim().toLowerCase();
  const min = minDistance.value === '' ? null : Number(minDistance.value);
  const max = maxDistance.value === '' ? null : Number(maxDistance.value);
  const filtered = items.filter(item => {
    const distance = item['역까지거리_m'];
    return `${item['소재지'] || ''} ${item['사건번호'] || ''}`.toLowerCase().includes(keyword) && (!use.value || item['용도'] === use.value) && (!recommended.checked || item['추천'] === true) && (min === null || (distance != null && distance >= min)) && (max === null || (distance != null && distance <= max));
  });
  const number = value => Number(String(value || '').replace(/[^0-9]/g, '')) || Infinity;
  if (sort.value === 'distance') filtered.sort((a,b) => (a['역까지거리_m'] ?? Infinity) - (b['역까지거리_m'] ?? Infinity));
  if (sort.value === 'price') filtered.sort((a, b) => number(a['최저가']) - number(b['최저가']));
  if (sort.value === 'date') filtered.sort((a, b) => (a['매각기일'] || '9999').localeCompare(b['매각기일'] || '9999'));
  count.textContent = `전체 ${items.length}건 중 ${filtered.length}건 표시`;
  empty.hidden = filtered.length > 0;
  visibleItems = filtered;
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  currentPage = Math.min(currentPage, totalPages);
  previous.disabled = currentPage <= 1; next.disabled = currentPage >= totalPages;
  pageLabel.textContent = `${currentPage} / ${totalPages}`;
  for (const item of filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize)) {
    const article = document.createElement('article');
    article.className = 'result-card';
    const badge = document.createElement('span'); badge.className = 'result-badge'; badge.textContent = item['용도'] || '매물'; article.append(badge);
    const address = document.createElement('h3'); address.textContent = item['소재지'] || '소재지 정보 없음'; article.append(address);
    const prices = document.createElement('div'); prices.className = 'result-prices';
    for (const key of ['최저가', '감정가']) {
      const entry = document.createElement('div'); const label = document.createElement('span'); const value = document.createElement('strong');
      label.textContent = key; value.textContent = item[key] || '정보 없음'; entry.append(label, value); prices.append(entry);
    }
    article.append(prices);
    const details = document.createElement('dl'); details.className = 'result-details';
    for (const key of ['사건번호', '매각기일', '현재상태']) {
      const entry = document.createElement('div'); const label = document.createElement('dt'); const value = document.createElement('dd');
      label.textContent = key; value.textContent = item[key] || '정보 없음'; entry.append(label, value); details.append(entry);
    }
    for (const key of ['면적', '특수권리', '최근접역', '역까지거리_m']) {
      if (item[key] === undefined || item[key] === '') continue;
      const entry = document.createElement('div'); const label = document.createElement('dt'); const value = document.createElement('dd');
      label.textContent = key === '역까지거리_m' ? '역까지 거리' : key;
      value.textContent = key === '역까지거리_m' ? `${item[key].toLocaleString('ko-KR')}m` : item[key]; entry.append(label, value); details.append(entry);
    }
    article.append(details);
    if (item['상세주소']) {
      const detail = document.createElement('a');
      detail.className = 'result-link';
      detail.href = item['상세주소'];
      detail.target = '_blank';
      detail.rel = 'noopener noreferrer';
      detail.textContent = '매물 자세히 보기 ↗';
      detail.setAttribute('aria-label', `${address.textContent} 매물 자세히 보기 (새 창)`);
      article.append(detail);
      const addressLink = document.createElement('a');
      addressLink.href = item['상세주소']; addressLink.target = '_blank'; addressLink.rel = 'noopener noreferrer';
      addressLink.textContent = address.textContent; address.replaceChildren(addressLink);
    }
    if (Number.isFinite(item.lat) && Number.isFinite(item.lng) && window.L) {
      const mapNode = document.createElement('div'); mapNode.className = 'result-map'; mapNode.setAttribute('aria-label', `${address.textContent} 위치`); article.append(mapNode); grid.append(article);
      const map = L.map(mapNode, {scrollWheelZoom: false}).setView([item.lat, item.lng], 15);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);
      L.marker([item.lat, item.lng]).addTo(map); maps.push(map);
    } else grid.append(article);
  }
}
function applyFilter() { currentPage = 1; displayResults(); }
query.addEventListener('input', applyFilter);
sort.addEventListener('change', applyFilter);
use.addEventListener('change', applyFilter);
recommended.addEventListener('change', applyFilter);
minDistance.addEventListener('input', applyFilter);
maxDistance.addEventListener('input', applyFilter);
previous.addEventListener('click', () => { currentPage--; displayResults(); result.scrollIntoView({block:'start'}); });
next.addEventListener('click', () => { currentPage++; displayResults(); result.scrollIntoView({block:'start'}); });
document.querySelector('#result-export').addEventListener('click', () => {
  const columns = ['사건번호','용도','소재지','감정가','최저가','매각기일','면적','특수권리','현재상태','최근접역','역까지거리_m'];
  const cell = value => { let text = String(value ?? ''); if (/^[=+@\-\t\r]/.test(text)) text = "'" + text; return '"' + text.replace(/"/g,'""') + '"'; };
  const csv = [columns.map(cell).join(','), ...visibleItems.map(item => columns.map(key => cell(item[key])).join(','))].join('\r\n');
  const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob(['\ufeff', csv],{type:'text/csv;charset=utf-8'})); link.download = '경매매물.csv'; link.click(); URL.revokeObjectURL(link.href);
});

toggle.addEventListener('click', () => {
  const show = password.type === 'password';
  password.type = show ? 'text' : 'password';
  toggle.textContent = show ? '숨기기' : '보기';
  toggle.setAttribute('aria-label', show ? '비밀번호 숨기기' : '비밀번호 표시');
});

const sessionPanel = document.querySelector('#session-panel');
const loading = document.querySelector('#loading-overlay');
const loadingRegion = document.querySelector('#loading-region');
const loginTitle = document.querySelector('#login-title');
const resultConditionBar = document.querySelector('#result-condition-bar');
const panelSubtitle = document.querySelector('.panel-sub');
let signedIn = false;

function setSignedIn(value) {
  signedIn = value;
  sessionPanel.hidden = !value;
  resultConditionBar.hidden = !value;
  form.hidden = value;
  loginTitle.textContent = value ? '다시 찾아볼까요?' : '반갑습니다';
  panelSubtitle.textContent = value ? '지역을 고르면 저장된 조건으로 검색해요.' : '로그인 정보를 입력해 주세요.';
}
function setLoading(value, searchName = '') {
  loading.hidden = !value;
  loadingRegion.textContent = searchName === '경기도조건검색' ? '경기도 매물을 살펴보는 중입니다.' : '인천 매물을 살펴보는 중입니다.';
  document.body.classList.toggle('searching', value);
  submit.disabled = value;
  document.querySelectorAll('[data-search], #logout').forEach(button => { button.disabled = value; });
}
async function search(body) {
  setLoading(true, body.searchName);
  message.hidden = true;
  try {
    const response = await fetch('/api/search', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const data = await response.json().catch(() => ({error:'서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.'}));
    if (!response.ok) {
      if (data.code === 'SESSION_EXPIRED') setSignedIn(false);
      throw new Error(data.error || '요청을 처리하지 못했습니다.');
    }
    setSignedIn(!!data.sessionAvailable);
    message.hidden = false;
    message.textContent = `검색 조건: ${data.searchName || '저장된 조건'} · ${data.items.length}건을 찾았습니다.`;
    if (!data.sessionAvailable) message.textContent += ' 다시 검색하려면 로그인해 주세요.';
    items = data.items;
    query.value = '';
    use.replaceChildren(new Option('전체', ''));
    [...new Set(items.map(item => item['용도']).filter(Boolean))].sort().forEach(value => use.add(new Option(value, value)));
    recommended.checked = false; minDistance.value = ''; maxDistance.value = ''; currentPage = 1;
    const missing = items.filter(item => !Number.isFinite(item.lat) || !Number.isFinite(item.lng)).length;
    const mapNotice = document.querySelector('#map-notice');
    mapNotice.hidden = !missing;
    mapNotice.textContent = missing ? `${missing}건은 위치를 확인하지 못해 지도가 표시되지 않습니다.` : '';
    sort.value = 'original';
    displayResults();
    result.hidden = false;
    maps.forEach(map => map.invalidateSize());
    result.scrollIntoView({behavior:'smooth', block:'start'});
  } catch (error) { message.hidden = false; message.textContent = error.message || '처리하지 못했습니다. 잠시 후 다시 시도해 주세요.'; }
  finally { password.value = ''; setLoading(false); }
}
form.addEventListener('submit', event => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  search({username:document.querySelector('#username').value,password:password.value,searchName:document.querySelector('#search-name').value});
});
document.querySelectorAll('[data-search]').forEach(button => button.addEventListener('click', () => {
  if (signedIn) search({searchName:button.dataset.search});
}));
document.querySelector('#logout').addEventListener('click', async () => {
  try {
    const response=await fetch('/api/search', {method:'DELETE'});
    if (!response.ok) throw new Error('로그아웃하지 못했습니다. 다시 시도해 주세요.');
    setSignedIn(false); result.hidden = true; message.hidden = false; message.textContent = '로그아웃했습니다.';
    items = []; grid.replaceChildren(); maps.forEach(map => map.remove()); maps = [];
  } catch (error) { message.hidden = false; message.textContent = error.message; }
});
fetch('/api/search', {method:'GET'}).then(response => response.ok ? response.json() : null).then(data => { if (data?.authenticated) setSignedIn(true); }).catch(() => {});
