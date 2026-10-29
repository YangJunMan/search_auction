const form = document.querySelector('#login-form');
const password = document.querySelector('#password');
const toggle = document.querySelector('#toggle');
const message = document.querySelector('#login-message');
const submit = form.querySelector('.submit');
const result = document.querySelector('#search-results');

toggle.addEventListener('click', () => {
  const show = password.type === 'password';
  password.type = show ? 'text' : 'password';
  toggle.textContent = show ? '숨기기' : '보기';
  toggle.setAttribute('aria-label', show ? '비밀번호 숨기기' : '비밀번호 표시');
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  submit.disabled = true;
  message.hidden = false;
  message.textContent = '로그인하고 매물을 찾고 있습니다. 잠시 기다려 주세요.';
  result.hidden = true;
  result.replaceChildren();
  try {
    const response = await fetch('/api/search', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:document.querySelector('#username').value,password:password.value})});
    const data = await response.json().catch(() => ({error:'서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.'}));
    if (!response.ok) throw new Error(data.error || '요청을 처리하지 못했습니다.');
    message.textContent = `검색이 끝났습니다. ${data.items.length}건을 찾았습니다.`;
    for (const item of data.items) {
      const article = document.createElement('article');
      article.className = 'result-item';
      for (const [key, value] of Object.entries(item)) {
        const row = document.createElement('p');
        const label = document.createElement('strong');
        label.textContent = `${key} `;
        row.append(label, document.createTextNode(String(value)));
        article.append(row);
      }
      result.append(article);
    }
    result.hidden = false;
  } catch (error) { message.textContent = error.message || '처리하지 못했습니다. 잠시 후 다시 시도해 주세요.'; }
  finally { password.value = ''; submit.disabled = false; }
});
