from __future__ import annotations
import json
import urllib.parse
import urllib.request
from typing import Dict, Tuple, Optional
from pathlib import Path
import hashlib


def _http_get(url: str, headers: Dict[str, str]) -> bytes:
	req = urllib.request.Request(url, headers=headers)
	with urllib.request.urlopen(req, timeout=20) as resp:
		return resp.read()


def _http_post(url: str, data: bytes, headers: Dict[str, str]) -> bytes:
	req = urllib.request.Request(url, data=data, headers=headers, method="POST")
	with urllib.request.urlopen(req, timeout=40) as resp:
		return resp.read()


def get_bbox_for_area(area_name: str) -> Optional[Tuple[float, float, float, float]]:
	"""Nominatim으로 행정구역/도시 이름의 대략적 경계 bbox를 구한다. (south, west, north, east)"""
	params = {
		"q": area_name,
		"format": "json",
		"limit": "1",
	}
	url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
	headers = {"User-Agent": "stations-util/1.0 (contact: example@example.com)"}
	data = json.loads(_http_get(url, headers).decode("utf-8"))
	if not data:
		return None
	bb = data[0].get("boundingbox")
	if not bb or len(bb) < 4:
		return None
	# Nominatim order: [south, north, west, east]
	south = float(bb[0])
	north = float(bb[1])
	west = float(bb[2])
	east = float(bb[3])
	return south, west, north, east


def fetch_stations_in_bbox(south: float, west: float, north: float, east: float) -> Dict[str, Tuple[float, float]]:
	"""Overpass로 bbox 내 railway=station을 조회하여 {역명: (lat, lon)}를 반환한다."""
	overpass_url = "https://overpass-api.de/api/interpreter"
	query = f"""
	[out:json][timeout:30];
	(
	  node["railway"="station"]({south},{west},{north},{east});
	  way["railway"="station"]({south},{west},{north},{east});
	  relation["railway"="station"]({south},{west},{north},{east});
	);
	out center tags;
	"""
	headers = {"User-Agent": "stations-util/1.0 (contact: example@example.com)", "Content-Type": "application/x-www-form-urlencoded"}
	body = urllib.parse.urlencode({"data": query}).encode("utf-8")
	resp = json.loads(_http_post(overpass_url, body, headers).decode("utf-8"))
	result: Dict[str, Tuple[float, float]] = {}
	for el in resp.get("elements", []):
		tags = el.get("tags", {}) or {}
		name = tags.get("name:ko") or tags.get("name") or None
		if not name:
			continue
		lat: Optional[float] = None
		lon: Optional[float] = None
		if el.get("type") == "node":
			lat = el.get("lat")
			lon = el.get("lon")
		else:
			center = el.get("center") or {}
			lat = center.get("lat")
			lon = center.get("lon")
		if lat is None or lon is None:
			continue
		# 중복 이름은 첫 번째 것을 유지
		result.setdefault(name, (float(lat), float(lon)))
	return result


def _cache_path_for_area(area_name: str) -> Path:
	cache_dir = Path("output/cache")
	cache_dir.mkdir(parents=True, exist_ok=True)
	key = hashlib.sha256(area_name.encode("utf-8")).hexdigest()[:16]
	return cache_dir / f"stations_cache_{key}.json"


def fetch_stations_for_area(area_name: str, force_refresh: bool = False) -> Dict[str, Tuple[float, float]]:
	# 1) 캐시 조회
	cache_file = _cache_path_for_area(area_name)
	if not force_refresh and cache_file.exists():
		try:
			data = json.loads(cache_file.read_text(encoding="utf-8"))
			return {k: (float(v[0]), float(v[1])) for k, v in data.items()}
		except Exception:
			pass

	# 2) API 조회
	bbox = get_bbox_for_area(area_name)
	if not bbox:
		return {}
	south, west, north, east = bbox
	result = fetch_stations_in_bbox(south, west, north, east)

	# 3) 캐시 저장
	try:
		cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
	except Exception:
		pass
	return result


