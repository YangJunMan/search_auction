const test = require('node:test');
const assert = require('node:assert/strict');
const { pageUrls } = require('../lib/pagination');
test('creates remaining page links while retaining search parameters', () => {
  const urls = pageUrls('https://example.com/auction/search_list.php?rows=20&address=12', '?page=3&address=12');
  assert.equal(urls.length, 2);
  assert.equal(new URL(urls[0]).searchParams.get('page'),'2');
  assert.equal(new URL(urls[1]).searchParams.get('page'),'3');
  assert.equal(new URL(urls[0]).searchParams.get('address'),'12');
});
test('does not invent extra pages for an absent pagination control', () => {
  assert.deepEqual(pageUrls('https://example.com/list', null), []);
});
