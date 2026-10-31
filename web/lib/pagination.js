function pageUrls(currentUrl, lastHref) {
  if (!lastHref) return [];
  const last = Number(new URL(lastHref, currentUrl).searchParams.get('page'));
  if (!Number.isSafeInteger(last) || last < 2 || last > 500) return [];
  const urls = [];
  for (let n = 2; n <= last; n++) {
    const url = new URL(currentUrl);
    url.searchParams.set('page', String(n));
    urls.push(url.href);
  }
  return urls;
}
module.exports = {pageUrls};
