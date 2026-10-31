const {createCipheriv, createDecipheriv, randomBytes, hkdfSync} = require('node:crypto');
const COOKIE_NAME = 'auction_session';
const TTL_SECONDS = 8 * 60 * 60;
function keyFor(secret) {
  if (typeof secret !== 'string' || !secret) throw new Error('SESSION_KEY_MISSING');
  return Buffer.from(hkdfSync('sha256', Buffer.from(secret), Buffer.from('auction-session-v1'), Buffer.from('encrypted-upstream-cookies'), 32));
}
function sealSession(cookies, secret, now = Date.now()) {
  const iv=randomBytes(12), cipher=createCipheriv('aes-256-gcm',keyFor(secret),iv);
  const plaintext=Buffer.from(JSON.stringify({exp:now+TTL_SECONDS*1000,cookies}));
  const data=Buffer.concat([cipher.update(plaintext),cipher.final()]);
  const token=[iv,data,cipher.getAuthTag()].map(b=>b.toString('base64url')).join('.');
  if (token.length > 3600) throw new Error('SESSION_TOO_LARGE');
  return token;
}
function openSession(token, secret, now = Date.now()) {
  try {
    if (typeof token !== 'string' || token.length > 3600) return null;
    const pieces=token.split('.');
    if (pieces.length!==3 || pieces.some(p=>!/^[A-Za-z0-9_-]+$/.test(p))) return null;
    const [iv,data,tag]=pieces.map(p=>Buffer.from(p,'base64url'));
    if (iv.length!==12 || tag.length!==16 || [iv,data,tag].some((b,i)=>b.toString('base64url')!==pieces[i])) return null;
    const decipher=createDecipheriv('aes-256-gcm',keyFor(secret),iv); decipher.setAuthTag(tag);
    const payload=JSON.parse(Buffer.concat([decipher.update(data),decipher.final()]).toString('utf8'));
    if (!Number.isFinite(payload.exp) || payload.exp<=now || payload.exp>now+TTL_SECONDS*1000 || !Array.isArray(payload.cookies)) return null;
    return payload.cookies;
  } catch { return null; }
}
function readSessionCookie(header) {
  if (typeof header !== 'string') return null;
  const entry=header.split(';').map(part=>part.trim()).find(part=>part.startsWith(`${COOKIE_NAME}=`));
  return entry ? entry.slice(COOKIE_NAME.length+1) : null;
}
function cookieHeader(token) { return `${COOKIE_NAME}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${TTL_SECONDS}`; }
function clearCookie() { return `${COOKIE_NAME}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`; }
module.exports={sealSession,openSession,readSessionCookie,cookieHeader,clearCookie,TTL_SECONDS};
