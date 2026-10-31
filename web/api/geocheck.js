const {geocodeItems} = require('../lib/geo');
module.exports = async function(req, res) {
  if (req.method !== 'GET') return res.status(405).end();
  const [item] = await geocodeItems([{'소재지':'인천광역시 남동구 정각로 29'}], process.env.KAKAO_REST_API_KEY);
  return res.status(200).json({configured:!!process.env.KAKAO_REST_API_KEY, located:Number.isFinite(item.lat) && Number.isFinite(item.lng), station:!!item['최근접역']});
};
