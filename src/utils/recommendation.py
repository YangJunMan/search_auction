from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from src.utils.geo import GeocodeCache, Geocoder
from src.utils.geo_ops import geocode_stations, enrich_with_geo, enrich_with_geo_parallel, compute_distances
from src.utils.stations import fetch_stations_for_area
from src.utils.gallery import build_gallery_html


def ensure_kakao_key_from_config(config_dict: Dict) -> None:
    """If KAKAO_REST_API_KEY env var is missing, try to read from config.json-compatible dict."""
    if os.getenv("KAKAO_REST_API_KEY"):
        return
    try:
        candidate = config_dict.get("kakao_rest_api_key") or config_dict.get("KAKAO_REST_API_KEY")
        if not candidate and isinstance(config_dict.get("api_keys"), dict):
            ak = config_dict["api_keys"]
            candidate = ak.get("kakao_rest_api_key") or ak.get("KAKAO_REST_API_KEY")
        if candidate:
            os.environ["KAKAO_REST_API_KEY"] = str(candidate)
    except Exception:
        pass


def generate_recommendations(
    items: List[Dict],
    output_dir: Path,
    station_names: List[str] | None,
    radius_m: int = 500,
    city_hint: Optional[str] = None,
    base_stem: Optional[str] = None,
) -> Dict[str, Path]:
    """
    Enrich items with coordinates, compute nearest-station distances, store full/recommended JSON and HTML.

    Returns dict with keys: full_json, recommended_json, recommended_html
    """
    station_names = [str(s).strip() for s in (station_names or []) if str(s).strip()]
    if not station_names and city_hint:
        # 지역 내 모든 역 자동 탐지 (OSM Overpass)
        auto = fetch_stations_for_area(city_hint)  # {name: (lat, lon)}
        station_names = list(auto.keys())
        station_coords = auto
    else:
        station_coords = None

    cache = GeocodeCache(Path("output/cache/geocode_cache.json"))
    coder = Geocoder(cache)
    if station_coords is None:
        station_coords = geocode_stations(station_names, city_hint, coder)
    cache.save()
    if not station_coords:
        raise RuntimeError("기준역 좌표를 구할 수 없습니다. stations 또는 city 설정을 확인하세요.")

    # 병렬 지오코딩으로 가속 (공공 API는 동시성 3~5 권장)
    enrich_with_geo_parallel(items, coder, city_hint, max_workers=4)
    cache.save()

    compute_distances(items, station_coords, int(radius_m))

    if not base_stem:
        base_stem = f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 파일명용 태그 슬러그/축약 처리 (경로 길이/문자 이슈 방지)
    import re, hashlib
    raw_tag = "_".join(station_names)
    slug = re.sub(r"[^\uAC00-\uD7A3A-Za-z0-9_]+", "", raw_tag)
    if len(slug) > 50:
        h = hashlib.sha1(raw_tag.encode("utf-8")).hexdigest()[:8]
        slug = slug[:50] + "_" + h
    stations_tag = slug or "stations"
    output_dir.mkdir(exist_ok=True, parents=True)

    full_geo_json = output_dir / f"search_results_with_geo_{base_stem}.json"
    with full_geo_json.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=4)

    recommended = [x for x in items if x.get("추천")]
    reco_json = output_dir / f"recommended_{base_stem}_{stations_tag}_{int(radius_m)}m.json"
    with reco_json.open("w", encoding="utf-8") as f:
        json.dump(recommended, f, ensure_ascii=False, indent=4)

    # 카드형 갤러리 HTML 생성
    reco_html = output_dir / f"recommended_{base_stem}_{stations_tag}_{int(radius_m)}m.html"
    build_gallery_html(
        recommended,
        title="역 주변 추천 매물",
        subtitle=f"기준역: {', '.join(station_names)} · 반경 {int(radius_m)}m",
        output_html_path=reco_html,
    )

    return {
        "full_json": full_geo_json,
        "recommended_json": reco_json,
        "recommended_html": reco_html,
    }


def run_recommendations_from_config(
    config_dict: Dict,
    items: List[Dict],
    saved_path: Optional[Path],
    output_dir: Path,
    logger: Optional[object] = None,
) -> None:
    """High-level orchestrator: read stations/city/radius from config and generate recommendations.

    - config_dict: typically Config.data
    - items: scraped results (list of dicts)
    - saved_path: path of the saved original results; used to derive base_stem
    - output_dir: folder to store generated files
    - logger: optional logger with .info/.warning
    """
    ensure_kakao_key_from_config(config_dict)

    stations_cfg = config_dict.get("stations") or (config_dict.get("recommend") or {}).get("stations")
    radius_m = (
        config_dict.get("radius_m")
        or (config_dict.get("recommend") or {}).get("radius_m")
        or 500
    )
    city_hint = (
        config_dict.get("city")
        or (config_dict.get("recommend") or {}).get("city")
        or None
    )
    should_run_recommend = (
        (isinstance(stations_cfg, list) and len(stations_cfg) > 0) or (city_hint is not None)
    )
    if not should_run_recommend:
        if logger:
            logger.info("config에 stations/city 설정이 없어 추천 산출을 생략합니다.")
        else:
            print("[recommend] stations/city not configured; skipping.")
        return

    station_names: List[str] | None = None
    if isinstance(stations_cfg, list) and len(stations_cfg) > 0:
        station_names = [str(s).strip() for s in stations_cfg if str(s).strip()]

    base_stem = Path(saved_path).stem if saved_path else None
    try:
        out = generate_recommendations(
            items=items,
            output_dir=output_dir,
            station_names=station_names,
            radius_m=int(radius_m),
            city_hint=city_hint,
            base_stem=base_stem,
        )
        if logger:
            logger.info(f"추천 JSON: {out['recommended_json']}")
            logger.info(f"추천 HTML: {out['recommended_html']}")
        else:
            print(f"추천 JSON: {out['recommended_json']}")
            print(f"추천 HTML: {out['recommended_html']}")
    except Exception as e:
        if logger:
            logger.warning(f"추천 산출 실패: {e}")
        else:
            print(f"[recommend] failed: {e}")

