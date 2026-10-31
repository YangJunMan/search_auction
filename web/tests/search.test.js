const { test } = require('node:test');
const assert = require('node:assert/strict');
const { makeHandler } = require('../api/search');
function response() { return { headers: {}, statusCode: 0, setHeader(k,v){this.headers[k]=v}, status(v){this.statusCode=v; return this}, json(v){this.body=v; return this} }; }
test('rejects missing credentials without running a browser', async () => {
  let invoked = false;
  const handler = makeHandler(async () => { invoked=true; });
  const res=response(); await handler({method:'POST',body:{username:'',password:'x'}},res);
  assert.equal(res.statusCode,400); assert.equal(invoked,false); assert.equal(res.headers['Cache-Control'],'no-store');
});
test('passes credentials to runner and returns results without exposing them', async () => {
  const handler=makeHandler(async (u,p) => { assert.equal(u,'example'); assert.equal(p,'secret'); return [{주소:'서울'}]; });
  const res=response(); await handler({method:'POST',body:{username:'example',password:'secret'}},res);
  assert.equal(res.statusCode,200); assert.deepEqual(res.body.items,[{주소:'서울'}]); assert.equal(JSON.stringify(res.body).includes('secret'),false);
});
test('does not expose internal errors or credentials', async () => {
  const handler=makeHandler(async () => { throw Error('password secret'); });
  const res=response(); await handler({method:'POST',body:{username:'example',password:'secret'}},res);
  assert.equal(res.statusCode,502); assert.equal(JSON.stringify(res.body).includes('secret'),false);
});
test('selects named saved search if present, otherwise chooses the first usable search', () => {
  const { chooseSavedSearch } = require('../api/search');
  assert.equal(chooseSavedSearch([{name:'삭제', onclick:'deleteSearch(1)'},{name:'다른 조건',onclick:'loadSearch(2)'},{name:'인천조건검색',onclick:'loadSearch(3)'}]),2);
  assert.equal(chooseSavedSearch([{name:'삭제',onclick:'deleteSearch(1)'},{name:'다른 조건',onclick:'loadSearch(2)'}]),1);
  assert.equal(chooseSavedSearch([{name:'삭제',onclick:'deleteSearch(1)'}]),-1);
});
test('restores an encrypted login session for a different saved search without credentials', async () => {
  const {openSession,readSessionCookie} = require('../lib/session');
  const secret='test_session_key'; const saved=[{name:'PHPSESSID',value:'upstream-private',domain:'www.my-auction.co.kr',path:'/'}];
  const runner=async (username,password,searchName,cookies) => {
    if (!cookies) { assert.equal(username,'example'); assert.equal(password,'secret'); }
    else { assert.equal(username,undefined); assert.equal(password,undefined); assert.deepEqual(cookies,saved); assert.equal(searchName,'경기도조건검색'); }
    return {items:[],searchName,sessionCookies:saved};
  };
  const handler=makeHandler(runner,()=>secret), first=response();
  await handler({method:'POST',headers:{},body:{username:'example',password:'secret',searchName:'인천조건검색'}},first);
  assert.equal(first.statusCode,200); assert.equal(JSON.stringify(first.body).includes('upstream-private'),false);
  const header=first.headers['Set-Cookie']; assert.match(header,/HttpOnly/); assert.match(header,/Secure/); assert.match(header,/SameSite=Lax/);
  assert.deepEqual(openSession(readSessionCookie(header),secret),saved);
  const second=response(); await handler({method:'POST',headers:{cookie:header},body:{searchName:'경기도조건검색'}},second);
  assert.equal(second.statusCode,200); assert.equal(second.body.searchName,'경기도조건검색');
});
test('reports an expired session and clears the cookie on logout', async () => {
  const handler=makeHandler(async ()=>{throw Error('not called');},()=> 'secret');
  const res=response(); await handler({method:'POST',headers:{cookie:'auction_session=bad'},body:{searchName:'인천조건검색'}},res);
  assert.equal(res.statusCode,401);
  const logout=response(); await handler({method:'DELETE',headers:{}},logout);
  assert.equal(logout.statusCode,200); assert.match(logout.headers['Set-Cookie'],/Max-Age=0/);
});
test('session state can be checked without leaking upstream data and cross-origin posts are denied', async () => {
  const {sealSession,cookieHeader} = require('../lib/session');
  const secret='test-key', cookie=cookieHeader(sealSession([{name:'id',value:'PRIVATE'}],secret));
  const handler=makeHandler(async()=>{throw Error('not reached');},()=>secret);
  const state=response(); await handler({method:'GET',headers:{cookie}},state);
  assert.deepEqual(state.body,{authenticated:true}); assert.equal(JSON.stringify(state.body).includes('PRIVATE'),false);
  const denied=response(); await handler({method:'POST',headers:{cookie,origin:'https://elsewhere.example',host:'example.com'},body:{searchName:'인천조건검색'}},denied);
  assert.equal(denied.statusCode,403);
});
