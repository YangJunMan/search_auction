from __future__ import annotations
import json
import glob
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from src.utils.geo import GeocodeCache, Geocoder
from src.utils.geo_ops import geocode_stations, enrich_with_geo_parallel, compute_distances
from src.utils.report import write_csv, build_html_from_csv


DEFAULT_RADIUS_M = 500


BASE_COLS = [
	"사건번호",
	"용도",
	"소재지",
	"감정가",
	"최저가",
	"매각기일",
	"면적",
	"특수권리",
	"현재상태",
	"최근접역",
	"역까지거리_m",
	"추천",
]


def find_latest_json() -> str:
	# 가장 최근 실행 폴더(timestamp) 하위에서 찾되, 없으면 루트 output에서 탐색
	run_dirs = sorted(
		[p for p in glob.glob(os.path.join("output", "*")) if os.path.isdir(p)],
		key=lambda p: os.path.getmtime(p),
		reverse=True,
	)
	files: List[str] = []
	for rd in run_dirs:
		files = glob.glob(os.path.join(rd, "search_results_*.json"))
		if files:
			break
	if not files:
		files = glob.glob(os.path.join("output", "search_results_*.json"))
	if not files:
		raise FileNotFoundError("output/**/search_results_*.json 파일을 찾을 수 없습니다.")
	files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
	return files[0]


def load_json(path: str) -> List[Dict]:
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def save_json(data, path: str) -> None:
	Path(path).parent.mkdir(exist_ok=True, parents=True)
	with open(path, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=4)


def parse_station_arg(names: Optional[str]) -> List[str]:
	if not names:
		return []
	return [s.strip() for s in names.split(",") if s.strip()]


def main() -> None:
	parser = argparse.ArgumentParser(description="역 반경 추천 필터")
	parser.add_argument("--input", type=str, default=None, help="입력 JSON 경로 (미지정 시 최신 파일 자동 탐색)")
	parser.add_argument("--stations", type=str, required=True, help='기준역 이름 콤마구분 예) "부천역,송내역,중동역"')
	parser.add_argument("--city", type=str, default=None, help='지오코딩 힌트용 도시/구명 예) "부천시"')
	parser.add_argument("--radius", type=int, default=DEFAULT_RADIUS_M, help="반경(m), 기본 500")
	parser.add_argument("--kakao-key", type=str, default=None, help="카카오 REST API 키 (환경변수/설정 파일보다 우선)")
	args = parser.parse_args()

	input_path = args.input or find_latest_json()
	items: List[Dict] = load_json(input_path)

	# Kakao 키 로딩 우선순위: CLI --kakao-key > 환경변수 KAKAO_REST_API_KEY > config.json
	if args.kakao_key:
		os.environ["KAKAO_REST_API_KEY"] = args.kakao_key
	elif not os.getenv("KAKAO_REST_API_KEY"):
		cfg_path = Path("config.json")
		if cfg_path.exists():
			try:
				cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
				candidate = None
				if isinstance(cfg, dict):
					candidate = cfg.get("kakao_rest_api_key") or cfg.get("KAKAO_REST_API_KEY")
					if not candidate and isinstance(cfg.get("api_keys"), dict):
						ak = cfg["api_keys"]
						candidate = ak.get("kakao_rest_api_key") or ak.get("KAKAO_REST_API_KEY")
				if candidate:
					os.environ["KAKAO_REST_API_KEY"] = str(candidate)
			except Exception:
				pass

	cache = GeocodeCache(Path("output/geocode_cache.json"))
	coder = Geocoder(cache)

	station_names = parse_station_arg(args.stations)
	station_coords = geocode_stations(station_names, args.city, coder)
	cache.save()
	if not station_coords:
		raise RuntimeError("기준역 좌표를 구할 수 없습니다. --stations / --city 값을 확인하세요.")

	enrich_with_geo_parallel(items, coder, args.city, max_workers=4)
	cache.save()

	compute_distances(items, station_coords, args.radius)

	base_path = Path(input_path)
	out_dir = base_path.parent
	base_stem = base_path.stem
	stations_tag = "_".join(station_names) if station_names else "stations"

	full_json = out_dir / f"search_results_with_geo_{base_stem}.json"
	save_json(items, str(full_json))

	recommended = [x for x in items if x.get("추천")]
	reco_json = out_dir / f"recommended_{base_stem}_{stations_tag}_{args.radius}m.json"
	save_json(recommended, str(reco_json))

	# CSV + 클라이언트 로드 HTML로 개선된 가독성/성능
	columns = BASE_COLS
	reco_csv = out_dir / f"recommended_{base_stem}_{stations_tag}_{args.radius}m.csv"
	write_csv(reco_csv, recommended, columns)

	reco_html = out_dir / f"recommended_{base_stem}_{stations_tag}_{args.radius}m.html"
	build_html_from_csv(
		csv_rel_path=reco_csv.name,
		title="역 주변 추천 매물",
		subtitle=f"기준역: {', '.join(station_names)} · 반경 {args.radius}m",
		output_html_path=reco_html,
	)

	print(f"추천 JSON: {reco_json}")
	print(f"추천 HTML: {reco_html}")


if __name__ == "__main__":
	main()


