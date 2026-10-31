const test = require('node:test');
const assert = require('node:assert/strict');
const { geocodeItems } = require('../lib/geo');

test('adds Kakao coordinates to addresses without changing unmatched items', async () => {
  const calls = [];
  const fakeFetch = async (url, options) => {
    calls.push({url, authorization: options.headers.Authorization});
    return {ok: true, json: async () => ({documents: url.includes('/address.json') && url.includes(encodeURIComponent('인천')) ? [{x:'126.7', y:'37.4'}] : []})};
  };
  const items = [{소재지:'인천 주소'}, {소재지:'경기 주소'}, {소재지:''}];
  const actual = await geocodeItems(items, 'test-key', fakeFetch);
  assert.deepEqual(actual, [{소재지:'인천 주소',lat:37.4,lng:126.7},{소재지:'경기 주소'},{소재지:''}]);
  assert.equal(calls.length, 3);
  assert.equal(calls[0].authorization, 'KakaoAK test-key');
});

test('keeps search results when geocoding fails or no key is configured', async () => {
  const items=[{소재지:'인천 주소'}];
  assert.deepEqual(await geocodeItems(items, '', () => {throw Error('unexpected');}),items);
  assert.deepEqual(await geocodeItems(items,'test-key',async () => {throw Error('network');}),items);
});

test('adds closest subway station and recommendation within 400 metres', async () => {
  const request = async url => ({ok:true,json:async()=>url.includes('/address.json') ? {documents:[{x:'126.7',y:'37.4'}]} : {documents:[{place_name:'예시역',distance:'350'}]}});
  const [item] = await geocodeItems([{소재지:'인천 예시'}], 'key', request);
  assert.equal(item['최근접역'],'예시역');
  assert.equal(item['역까지거리_m'],350);
  assert.equal(item['추천'],true);
});
