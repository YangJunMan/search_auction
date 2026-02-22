from __future__ import annotations
import json
import argparse
from pathlib import Path
from typing import List, Dict
import os
import glob
from src.utils.gallery import build_gallery_html

# python -m src.utils.json_to_html --latest --prefer-enriched --open --title "최신 추천 갤러리"

DEFAULT_ORDER = [
	"사건번호","용도","소재지","감정가","최저가","매각기일","면적","특수권리","현재상태",
	"최근접역","역까지거리_m","추천","lat","lng"
]


def load_json(path: Path) -> List[Dict]:
	data = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(data, list):
		raise ValueError("JSON 최상위 구조는 리스트여야 합니다.")
	return data


def build_columns(items: List[Dict]) -> List[str]:
	keys = []
	# 우선순위 키 먼저
	for k in DEFAULT_ORDER:
		if any((k in d and d.get(k) is not None) for d in items):
			keys.append(k)
	# 나머지 키 추가
	for d in items:
		for k in d.keys():
			if k not in keys:
				keys.append(k)
	return keys


def find_latest_json(search_dir: Path, prefer_enriched: bool = True) -> Path:
	patterns = [
		"recommended_*.json",
		"search_results_with_geo_*.json",
		"search_results_*.json",
	] if prefer_enriched else [
		"search_results_*.json",
		"recommended_*.json",
		"search_results_with_geo_*.json",
	]
	candidates: list[str] = []
	for pat in patterns:
		found = glob.glob(str(search_dir / pat))
		if found:
			candidates.extend(found)
	if not candidates:
		run_dirs = sorted(
			[p for p in glob.glob(str(search_dir / "*")) if os.path.isdir(p)],
			key=lambda p: os.path.getmtime(p),
			reverse=True,
		)
		for rd in run_dirs:
			for pat in patterns:
				found = glob.glob(os.path.join(rd, pat))
				if found:
					candidates.extend(found)
			if candidates:
				break
	if not candidates:
		raise FileNotFoundError(f"JSON 파일을 찾을 수 없습니다: {search_dir}")
	candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
	return Path(candidates[0])


def main() -> None:
	parser = argparse.ArgumentParser(description="기존 JSON을 갤러리형 HTML로 변환")
	parser.add_argument("--input", help="입력 JSON 경로(생략 시 --latest 사용)")
	parser.add_argument("--dir", default="output", help="검색 디렉토리(--latest 사용 시)")
	parser.add_argument("--latest", action="store_true", help="가장 최신 JSON 자동 선택")
	parser.add_argument("--prefer-enriched", action="store_true", help="추천/좌표 포함 파일을 우선 선택")
	parser.add_argument("--open", action="store_true", help="생성 후 브라우저로 열기(Windows)")
	parser.add_argument("--title", default="추천 매물 목록", help="HTML 제목")
	parser.add_argument("--subtitle", default=None, help="HTML 부제목(미지정 시 파일명/건수 자동 표기)")
	args = parser.parse_args()

	if args.input:
		input_path = Path(args.input)
	else:
		search_dir = Path(args.dir)
		input_path = find_latest_json(search_dir, prefer_enriched=bool(args.prefer_enriched or True))
	if not input_path.exists():
		raise FileNotFoundError(f"파일을 찾을 수 없습니다: {input_path}")
	items = load_json(input_path)

	out_dir = input_path.parent
	stem = input_path.stem
	html_path = out_dir / f"{stem}.html"

	# 카드형 갤러리 UI로 렌더
	subtitle = args.subtitle or f"파일: {input_path.name} · 총 {len(items)}건"
	build_gallery_html(items, args.title, subtitle, html_path)

	print(f"HTML 생성 완료: {html_path}")
	if args.open:
		try:
			os.startfile(str(html_path))
		except Exception:
			pass


if __name__ == "__main__":
	main()


