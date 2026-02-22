from __future__ import annotations
import os
import json
import time
import math
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Tuple, Optional


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
	"""Calculate great-circle distance in meters between two WGS84 points."""
	R = 6371000.0
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dphi = phi2 - phi1
	dlam = math.radians(lon2 - lon1)
	a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
	return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class GeocodeCache:
	"""Simple JSON file cache for geocoding results."""

	def __init__(self, path: Path):
		self.path = path
		self.data: Dict[str, Dict[str, float]] = {}
		if self.path.exists():
			try:
				self.data = json.loads(self.path.read_text(encoding="utf-8"))
			except Exception:
				self.data = {}

	def get(self, key: str) -> Optional[Tuple[float, float]]:
		item = self.data.get(key)
		if not item:
			return None
		return float(item["lat"]), float(item["lng"])

	def set(self, key: str, lat: float, lng: float) -> None:
		self.data[key] = {"lat": float(lat), "lng": float(lng)}

	def save(self) -> None:
		self.path.parent.mkdir(exist_ok=True, parents=True)
		self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")


def _http_get(url: str, headers: Dict[str, str]) -> bytes:
	req = urllib.request.Request(url, headers=headers)
	with urllib.request.urlopen(req, timeout=10) as resp:
		return resp.read()


def kakao_geocode(query: str, api_key: str) -> Optional[Tuple[float, float]]:
	url = "https://dapi.kakao.com/v2/local/search/address.json?query=" + urllib.parse.quote(query)
	headers = {
		"Authorization": f"KakaoAK {api_key}",
		"User-Agent": "geo-util/1.0",
	}
	data = json.loads(_http_get(url, headers=headers).decode("utf-8"))
	docs = data.get("documents", [])
	if not docs:
		return None
	# Kakao returns x: lon, y: lat
	x = float(docs[0]["x"])
	y = float(docs[0]["y"])
	return y, x


def nominatim_geocode(query: str) -> Optional[Tuple[float, float]]:
	params = {"q": query, "format": "json", "limit": "1", "addressdetails": "0"}
	url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
	headers = {"User-Agent": "geo-util/1.0 (contact: example@example.com)"}
	data = json.loads(_http_get(url, headers=headers).decode("utf-8"))
	if not data:
		return None
	lat = float(data[0]["lat"])  # type: ignore[index]
	lon = float(data[0]["lon"])  # type: ignore[index]
	return lat, lon


class Geocoder:
	"""Geocoder with provider selection and simple caching."""

	def __init__(self, cache: GeocodeCache, provider: Optional[str] = None):
		self.cache = cache
		self.provider = (provider or os.getenv("GEOCODER_PROVIDER") or "kakao").lower()
		self.kakao_key = os.getenv("KAKAO_REST_API_KEY")

	def geocode(self, query: str) -> Optional[Tuple[float, float]]:
		query = (query or "").strip()
		if not query:
			return None
		cached = self.cache.get(query)
		if cached:
			return cached

		result: Optional[Tuple[float, float]] = None
		try:
			if self.provider == "kakao" and self.kakao_key:
				result = kakao_geocode(query, self.kakao_key)
			else:
				result = nominatim_geocode(query)
			if result:
				self.cache.set(query, result[0], result[1])
				time.sleep(0.15)
		except Exception:
			# fallback to Nominatim if Kakao fails
			if self.provider != "nominatim":
				try:
					result = nominatim_geocode(query)
					if result:
						self.cache.set(query, result[0], result[1])
						time.sleep(1.0)  # be nicer to public API
				except Exception:
					result = None
		return result


