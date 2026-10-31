module.exports = async function(req,res) {
  try { const r=await fetch('https://www.my-auction.co.kr/auction/search.php',{signal:AbortSignal.timeout(10000)}); await r.body?.cancel(); return res.status(200).json({connected:true,status:r.status}); }
  catch(e) { return res.status(200).json({connected:false,type:e.name,code:e.cause?.code||''}); }
};
