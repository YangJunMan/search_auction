function pageUrls(currentUrl, lastHref) {
  if (!lastHref) return [];
  const lastUrl = new URL(lastHref, currentUrl);
  if (lastUrl.origin !== new URL(currentUrl).origin) throw new Error('INVALID_PAGINATION_URL');
  const last = Number(lastUrl.searchParams.get('page'));
  if (!Number.isSafeInteger(last) || last < 2 || last > 500) return [];
  const urls = [];
  for (let n = 2; n <= last; n++) {
    const url = new URL(lastUrl);
    url.searchParams.set('page', String(n));
    urls.push(url.href);
  }
  return urls;
}
module.exports = {pageUrls};
