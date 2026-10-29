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
