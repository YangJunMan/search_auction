const test = require('node:test');
const assert = require('node:assert/strict');
const { normalizeDetailUrl } = require('../lib/detail-url');
test('resolves the original auction listing URL', () => {
  assert.equal(normalizeDetailUrl('/view/1315153'), 'https://www.my-auction.co.kr/view/1315153');
  assert.equal(normalizeDetailUrl('https://www.my-auction.co.kr/view/1511470'), 'https://www.my-auction.co.kr/view/1511470');
});
test('rejects unsafe or unrelated destinations', () => {
  for (const href of ['', 'javascript:alert(1)', 'https://example.com/view/1315153', '/auction/search.php', '//evil.example/view/123']) assert.equal(normalizeDetailUrl(href), '');
});
