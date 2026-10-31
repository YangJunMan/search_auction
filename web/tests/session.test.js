const test = require('node:test');
const assert = require('node:assert/strict');
const { sealSession, openSession, readSessionCookie } = require('../lib/session');
const secret = 'example_test_secret_different_from_real_keys';
test('encrypts upstream cookies and can restore them before expiry', () => {
  const data=[{name:'PHPSESSID',value:'private',domain:'www.my-auction.co.kr',path:'/'}];
  const token=sealSession(data,secret,1000);
  assert.equal(token.includes('private'),false);
  assert.deepEqual(openSession(token,secret,1001),data);
  assert.equal(openSession(token,secret,1000+8*60*60*1000+1),null);
});
test('rejects altered tokens, missing key and unexpected cookie headers', () => {
  const token=sealSession([{name:'session',value:'private'}],secret,1000);
  const parts=token.split('.'); parts[1]=parts[1].slice(0,-1)+(parts[1].endsWith('A')?'B':'A');
  assert.equal(openSession(parts.join('.'),secret,1001),null);
  assert.equal(openSession(token,'wrong-key',1001),null);
  assert.equal(readSessionCookie('other=x; auction_session=abc.def; xyz=y'),'abc.def');
  assert.equal(readSessionCookie('other=x'),null);
});
