from __future__ import annotations
import json
import html as html_lib
from pathlib import Path
from typing import List, Dict


def build_gallery_html(items: List[Dict], title: str, subtitle: str, output_html_path: Path) -> None:
	# 최신 카드형 갤러리 UI (데이터를 인라인하여 로컬에서도 동작)
	tpl = """<!DOCTYPE html>
<html lang=\"ko\">
<head>
	<meta charset=\"UTF-8\" />
	<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
	<title>__TITLE__</title>
	<link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css\" rel=\"stylesheet\" />
	<link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\" />
	<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css\" />
	<script src=\"https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js\"></script>
	<style>
		/* 강제 라이트 테마 */
		:root { --bg:#f5f7fb; --card:#ffffff; --text:#0f172a; --muted:#64748b; --accent:#0ea5e9; --chip:#f1f5f9; --chip-border:#e2e8f0; --warn:#d97706; }
		body { background: var(--bg); color: var(--text); padding: 28px; }
		.header { margin-bottom: 18px; }
		.header h2 { margin: 0; font-weight: 800; letter-spacing: -0.3px; }
		.header .meta { color: var(--muted); font-size: 0.95rem; }
		.toolbar { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom: 16px; }
		.toolbar .form-control, .toolbar .form-select { background: var(--chip); color: var(--text); border-color: var(--chip-border); }
		.grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap:16px; }
		.cardx { background: var(--card); border-radius: 16px; box-shadow: 0 10px 30px rgba(2,6,23,0.12); overflow:hidden; border: 1px solid rgba(148,163,184,0.18); transition: transform .15s ease, box-shadow .15s ease; }
		.cardx:hover { transform: translateY(-2px); box-shadow: 0 16px 44px rgba(2,6,23,0.2); }
		.cardx .head { display:flex; justify-content:space-between; align-items:center; padding:14px 16px 6px 16px; }
		.badge-type { padding:4px 10px; border-radius:999px; background: var(--chip); border:1px solid var(--chip-border); font-size:12px; }
		.badge-reco { padding:4px 10px; border-radius:999px; background: rgba(34,197,94,0.12); color: var(--accent); border:1px solid rgba(34,197,94,0.35); font-size:12px; }
		.cardx .addr { padding:8px 16px; color: var(--muted); font-size: 1rem; min-height: 52px; }
		.meta-row { display:flex; gap:8px; align-items:center; padding: 0 16px 6px 16px; }
		.pill { display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border-radius:999px; background: var(--chip); border:1px solid var(--chip-border); font-size:12px; color: var(--text); }
		.pill i { color: var(--muted); }
		.prices { padding: 10px 16px; background: rgba(2,6,23,0.035); display:flex; justify-content:space-between; }
		.price { font-weight: 800; font-size: 1.08rem; }
		.disc { color: var(--warn); font-weight:700; }
		.cardx .body { padding: 8px 16px 12px 16px; display:grid; grid-template-columns: 1fr 1fr; gap: 8px; }
		.kv { font-size: 0.95rem; }
		.kv .k { color: var(--muted); }
		.kv .v { font-weight: 600; }
		.rights { padding: 8px 16px 12px 16px; }
		.chip { display:inline-block; padding:2px 8px; border-radius:999px; background: var(--chip); border:1px solid var(--chip-border); margin: 2px 4px 2px 0; font-size: 12px; }
		.mapbox { height: 168px; border-top:1px solid rgba(148,163,184,0.18); }
		/* (역 마커 제거에 따라 툴팁 스타일도 제거) */
	</style>
</head>
<body>
	<div class=\"container-fluid\">
		<div class=\"header\">
			<h2>__TITLE__</h2>
			<div class=\"meta\">__SUBTITLE__ · 총 <span id=\"cnt\"></span>건</div>
		</div>
		<div class=\"toolbar\">
			<input id=\"q\" class=\"form-control\" style=\"width:280px\" placeholder=\"주소/사건번호 검색\" />
			<select id=\"useSel\" class=\"form-select\" style=\"width:160px\"><option value=\"\">용도 전체</option></select>
			<label class=\"form-check-label\"><input id=\"onlyReco\" class=\"form-check-input\" type=\"checkbox\" /> 추천만</label>
			<div class=\"input-group\" style=\"width: 320px;\">
				<span class=\"input-group-text\">거리(m)</span>
				<input type=\"number\" min=\"0\" class=\"form-control\" id=\"minDist\" placeholder=\"최소\" />
				<input type=\"number\" min=\"0\" class=\"form-control\" id=\"maxDist\" placeholder=\"최대\" />
			</div>
			<select id=\"sortSel\" class=\"form-select\" style=\"width:180px\">
				<option value=\"distAsc\">거리 오름차순</option>
				<option value=\"distDesc\">거리 내림차순</option>
				<option value=\"priceAsc\">최저가 오름차순</option>
				<option value=\"priceDesc\">최저가 내림차순</option>
				<option value=\"dateAsc\">매각기일 오름차순</option>
				<option value=\"dateDesc\">매각기일 내림차순</option>
			</select>
			<button id=\"btnExport\" class=\"btn btn-sm btn-outline-primary\"><i class=\"bi bi-file-earmark-excel\"></i> 엑셀 내보내기</button>
		</div>
		<div id=\"grid\" class=\"grid\"></div>
	</div>

	<script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script>
	<script>
		const RAW = __DATA__;
		function num(x){ if(x===null||x===undefined) return null; const n=(''+x).replace(/[^\\d.-]/g,''); return n?Number(n):null; }
		function perc(app,low){ if(!app||!low) return null; const p=100*low/app; return Math.round(p); }
		function fmt(x){ if(x===null||x===undefined||x==='') return ''; const n=num(x); return (n===null)?x:n.toLocaleString('ko-KR'); }
		function parseDate(s){ if(!s) return null; return new Date(s.replace(/\./g,'-')); }

		const DATA = RAW.map(r=>({
			...r,
			__app:num(r['감정가']),
			__low:num(r['최저가']),
			__p: perc(num(r['감정가']), num(r['최저가'])),
			__d: r['역까지거리_m']? Number((''+r['역까지거리_m']).replace(/[^\\d.-]/g,'')) : null,
			__date: parseDate(r['매각기일'])
		}));

		const uses=[...new Set(DATA.map(x=>x['용도']).filter(Boolean))];
		const useSel=document.getElementById('useSel');
		uses.forEach(u=>{ const o=document.createElement('option'); o.value=u; o.textContent=u; useSel.appendChild(o); });

		function card(item){
			const rights=(item['특수권리']||'').split(/\s+/).filter(Boolean).map(x=>`<span class=\"chip\">${x}</span>`).join('');
			const disc = item.__p? `<span class=\"disc\">${item.__p}%</span>`: '';
			const reco = (item['추천']===true||item['추천']==='True'||item['추천']==='true')? '<span class=\"badge-reco\">추천</span>':'';
			const mapBox = (item['lat']&&item['lng'])? `<div class=\"mapbox\" id=\"map_${item['사건번호']}\"></div>`: '';
			return `
			<div class=\"cardx\">
				<div class=\"head\">
					<div class=\"badge-type\">${item['용도']||''}</div>
					<div>${reco}</div>
				</div>
				<div class=\"addr\">${item['소재지']||''}</div>
				<div class=\"meta-row\">
					${item['최근접역']? `<span class=\"pill\"><i class=\"bi bi-train-front\"></i>${item['최근접역']}</span>`:''}
					${item.__d? `<span class=\"pill\"><i class=\"bi bi-geo-alt\"></i>${item.__d.toLocaleString('ko-KR')} m</span>`:''}
				</div>
				<div class=\"prices\"><div>최저가 <span class=\"price\">${fmt(item['최저가'])}</span></div><div>감정가 <span>${fmt(item['감정가'])}</span> ${disc}</div></div>
				<div class=\"body\">
					<div class=\"kv\"><div class=\"k\">사건번호</div><div class=\"v\">${item['사건번호']||''}</div></div>
					<div class=\"kv\"><div class=\"k\">매각기일</div><div class=\"v\">${item['매각기일']||''}</div></div>
				</div>
				<div class=\"rights\">${rights}</div>
				${mapBox}
			</div>`;
		}

		function mountMaps(root){
			const nodes=[...root.querySelectorAll('.mapbox')];
			nodes.forEach(n=>{
				const id=n.id.replace('map_','');
				const item = DATA.find(x=>x['사건번호']===id);
				if(!item) return;
				const lat=parseFloat(item['lat']); const lng=parseFloat(item['lng']);
				if(!lat||!lng) return;
				const m=L.map(n.id, { zoomControl:false, attributionControl:false });
				L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(m);
				L.marker([lat,lng], {title:'매물'}).addTo(m);
				m.setView([lat,lng], 15);
				setTimeout(()=> m.invalidateSize(), 80);
			});
		}

		function apply(){
			const q=(document.getElementById('q').value||'').trim();
			const u=useSel.value||'';
			const only=document.getElementById('onlyReco').checked;
			const minD=parseFloat(document.getElementById('minDist').value||'');
			const maxD=parseFloat(document.getElementById('maxDist').value||'');
			const sort=document.getElementById('sortSel').value;
			let arr=DATA.slice();
			arr=arr.filter(x=>{
				if(u && x['용도']!==u) return false;
				if(only && !(x['추천']===true||x['추천']==='True'||x['추천']==='true')) return false;
				if(!isNaN(minD) && !((x.__d||Infinity)>=minD)) return false;
				if(!isNaN(maxD) && !((x.__d||-Infinity)<=maxD)) return false;
				if(q){
					const s=(x['소재지']||'')+' '+(x['사건번호']||'');
					if(!s.includes(q)) return false;
				}
				return true;
			});
			arr.sort((a,b)=>{
				if(sort==='distAsc') return (a.__d||Infinity)-(b.__d||Infinity);
				if(sort==='distDesc') return (b.__d||-Infinity)-(a.__d||-Infinity);
				if(sort==='priceAsc') return (a.__low||Infinity)-(b.__low||Infinity);
				if(sort==='priceDesc') return (b.__low||-Infinity)-(a.__low||-Infinity);
				if(sort==='dateAsc') return (a.__date||0)-(b.__date||0);
				if(sort==='dateDesc') return (b.__date||0)-(a.__date||0);
				return 0;
			});
			document.getElementById('cnt').textContent = arr.length.toLocaleString('ko-KR');
			const grid=document.getElementById('grid');
			grid.innerHTML = arr.map(card).join('');
			mountMaps(grid);

			// 엑셀 내보내기 핸들러: 현재 필터 결과 기준으로 워크북 생성
			document.getElementById('btnExport').onclick = () => {
				const exportCols = ['사건번호','용도','소재지','감정가','최저가','매각기일','면적','특수권리','현재상태','최근접역','역까지거리_m'];
				const rows = arr.map(r => {
					const o = {};
					exportCols.forEach(k => o[k] = r[k] ?? '');
					return o;
				});
				const ws = XLSX.utils.json_to_sheet(rows);
				const wb = XLSX.utils.book_new();
				XLSX.utils.book_append_sheet(wb, ws, '추천목록');
				XLSX.writeFile(wb, 'recommended.xlsx');
			};
		}

		document.getElementById('q').addEventListener('input', ()=> apply());
		useSel.addEventListener('change', ()=> apply());
		document.getElementById('onlyReco').addEventListener('change', ()=> apply());
		document.getElementById('minDist').addEventListener('input', ()=> apply());
		document.getElementById('maxDist').addEventListener('input', ()=> apply());
		document.getElementById('sortSel').addEventListener('change', ()=> apply());

		apply();
	</script>
</body>
</html>
"""

	output_html_path.parent.mkdir(parents=True, exist_ok=True)
	safe_title = html_lib.escape(title)
	safe_subtitle = html_lib.escape(subtitle)
	html = tpl.replace("__TITLE__", safe_title).replace("__SUBTITLE__", safe_subtitle)
	data_json = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
	html = html.replace("__DATA__", data_json)
	output_html_path.write_text(html, encoding="utf-8")


