async function geocodeItems(items, key, request = fetch) {
  if (!key) return items;
  const cache = new Map();
  const failures = {};
  const countFailure = code => { failures[code] = (failures[code] || 0) + 1; };
  async function query(url) {
    try {
      const response = await request(url, {headers: {Authorization: `KakaoAK ${key}`}, signal: AbortSignal.timeout(5000)});
      if (!response.ok) { countFailure(`http_${response.status || 'unknown'}`); return null; }
      return (await response.json()).documents?.[0] || null;
    } catch { countFailure('network'); return null; }
  }
  async function locate(address) {
    const normalized = address.replace(/\s*\([^)]*\)/g, '').split(',')[0].trim();
    const doc = await query(`https://dapi.kakao.com/v2/local/search/address.json?query=${encodeURIComponent(normalized)}`);
    const lat = Number(doc?.y), lng = Number(doc?.x);
    if (!doc || !Number.isFinite(lat) || !Number.isFinite(lng)) return null;
    const station = await query(`https://dapi.kakao.com/v2/local/search/category.json?category_group_code=SW8&x=${lng}&y=${lat}&radius=20000&sort=distance&size=1`);
    const distance = station?.distance === '' ? NaN : Number(station?.distance);
    return station?.place_name && Number.isFinite(distance)
      ? {lat, lng, '최근접역':station.place_name, '역까지거리_m':distance, '추천':distance <= 400}
      : {lat, lng};
  }
  const result = new Array(items.length);
  let next = 0;
  async function worker() {
    while (next < items.length) {
      const index = next++;
      const item = items[index];
      const address = (item['소재지'] || '').trim();
      if (!address) { result[index] = item; continue; }
      if (!cache.has(address)) cache.set(address, locate(address));
      const coordinates = await cache.get(address);
      result[index] = coordinates ? {...item, ...coordinates} : item;
    }
  }
  await Promise.all(Array.from({length:Math.min(items.length, 10)}, worker));
  console.info('geocoding summary:', JSON.stringify({items:items.length, located:result.filter(item => Number.isFinite(item.lat) && Number.isFinite(item.lng)).length, failures}));
  return result;
}
module.exports = {geocodeItems};
