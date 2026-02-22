from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

from src.utils.geo import Geocoder, haversine_m


def geocode_stations(station_names: List[str], city_hint: Optional[str], coder: Geocoder) -> Dict[str, Tuple[float, float]]:
	result: Dict[str, Tuple[float, float]] = {}
	for name in station_names:
		query = name if not city_hint else f"{city_hint} {name}"
		coord = coder.geocode(query)
		if coord:
			result[name] = coord
	return result


def default_address_normalizer(addr: str) -> str:
	s = re.sub(r"\([^)]*\)", "", addr)
	s = re.sub(r"\s+", " ", s).strip()
	s = re.sub(r"\s*(\d+호|\d+층)$", "", s)
	return s


def enrich_with_geo(items: List[Dict], coder: Geocoder, city_hint: Optional[str], normalizer: Optional[Callable[[str], str]] = default_address_normalizer) -> None:
	for it in items:
		addr = (it.get("소재지") or "").strip()
		if normalizer:
			addr = normalizer(addr)
		query = addr if not city_hint else f"{city_hint} {addr}"
		coord = coder.geocode(query)
		if coord:
			it["lat"], it["lng"] = coord


def enrich_with_geo_parallel(items: List[Dict], coder: Geocoder, city_hint: Optional[str], max_workers: int = 4, normalizer: Optional[Callable[[str], str]] = default_address_normalizer) -> None:
	queries: Dict[str, List[int]] = {}
	for idx, it in enumerate(items):
		if it.get("lat") is not None and it.get("lng") is not None:
			continue
		addr = (it.get("소재지") or "").strip()
		if normalizer:
			addr = normalizer(addr)
		query = addr if not city_hint else f"{city_hint} {addr}"
		if not query:
			continue
		queries.setdefault(query, []).append(idx)

	def task(q: str):
		return q, coder.geocode(q)

	if not queries:
		return

	with ThreadPoolExecutor(max_workers=max_workers) as ex:
		futures = [ex.submit(task, q) for q in queries.keys()]
		for fut in as_completed(futures):
			q, coord = fut.result()
			if coord:
				for idx in queries[q]:
					items[idx]["lat"], items[idx]["lng"] = coord


def compute_distances(items: List[Dict], stations: Dict[str, Tuple[float, float]], radius_m: int) -> None:
	for it in items:
		lat = it.get("lat")
		lng = it.get("lng")
		if lat is None or lng is None:
			it["최근접역"], it["역까지거리_m"], it["추천"] = None, None, False
			continue
		min_name: Optional[str] = None
		min_d: Optional[float] = None
		for name, (s_lat, s_lng) in stations.items():
			d = haversine_m(float(lat), float(lng), s_lat, s_lng)
			if min_d is None or d < min_d:
				min_d, min_name = d, name
		it["최근접역"] = min_name
		it["역까지거리_m"] = round(min_d) if min_d is not None else None
		it["추천"] = bool(min_d is not None and min_d <= radius_m)


