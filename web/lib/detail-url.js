function normalizeDetailUrl(href) {
  if (typeof href !== 'string' || !href) return '';
  try {
    const url = new URL(href, 'https://www.my-auction.co.kr');
    if (url.protocol !== 'https:' || url.hostname !== 'www.my-auction.co.kr' || !/^\/view\/\d+\/?$/.test(url.pathname)) return '';
    return url.href;
  } catch { return ''; }
}
module.exports = {normalizeDetailUrl};
