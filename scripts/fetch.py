#!/usr/bin/env python3
"""
우동 자동 수집 스크립트 v0.2 (시범: 서울 성동구 성수동)

하는 일:
  1. 서울 열린데이터광장 공공서비스예약 API에서 성동구 관련 예약 정보를 가져온다.
     - API 키가 없으면(fake 데이터를 만들지 않고) status를 missing_key로 기록한다.
     - 키는 환경변수 SEOUL_API_KEY로만 받는다. 코드에 키를 넣지 않는다.
  2. 성동구청 공지 RSS/XML은 공개된 RSS 주소를 찾지 못했기 때문에,
     이 버전에서는 자동 수집 대상으로 넣지 않는다.
     - 출처 파일(sources.yaml)에 RSS 주소가 추가되면 그때부터 수집한다.
     - 구청 게시판을 무단으로 크롤링하지 않는다.
  3. 결과를 data.json으로 쓴다. 제목·날짜·원문 링크만 저장하고 본문을 복사하지 않는다.

실행:
  SEOUL_API_KEY=... python3 scripts/fetch.py
  키 없이 실행하면 data.json에 status만 기록되고, 실제 공지는 0건이다.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data.json"
KST = timezone(timedelta(hours=9))

# 분류 키워드: 제목만으로 분류한다. 본문을 복사하지 않는다.
CATEGORIES = [
    ("urgent", ["단수", "정전", "공사", "통제", "긴급", "재난"]),
    ("welfare", ["지원", "복지", "신청", "모집", "장학", "바우처"]),
    ("event", ["행사", "축제", "장터", "공연", "전시", "강좌"]),
    ("work", ["공사", "교통", "도로", "주차"]),
    ("life", ["생활", "청소", "쓰레기", "폐기물", "민원"]),
]


def classify(title: str) -> str:
    for cat, words in CATEGORIES:
        if any(w in title for w in words):
            return cat
    return "life"


def fetch_seoul_reservation(api_key: str):
    """서울시 공공서비스예약 정보. 서비스명은 서울 열린데이터광장 기준이다.

    이 함수는 예약 '목록'만 가져온다. 실시간 남은 자리 수는
    이 API가 제공하지 않기 때문에, spots에는 예약 페이지 링크만 넣는다.
    """
    # 서울시 공공서비스예약(종합) 정보 서비스명. 지역 필터는 응답에서 확인한다.
    service = "ListPublicReservationCulture"
    url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/{service}/1/20/"
    req = urllib.request.Request(url, headers={"User-Agent": "udong/0.2"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return [], {"source": "seoul_reservation", "status": f"http_{e.code}", "url": url}
    except Exception as e:  # 네트워크 오류 등은 상태를 기록하고 멈추지 않는다
        return [], {"source": "seoul_reservation", "status": f"error:{type(e).__name__}", "url": url}

    rows = []
    try:
        rows = payload[service]["row"]
    except Exception:
        return [], {"source": "seoul_reservation", "status": "unexpected_response", "url": url}

    notices = []
    for row in rows:
        place = str(row.get("PLACENAME", "") or "")
        title = str(row.get("SVCNM", "") or "").strip()
        if not title:
            continue
        # 시범 범위: 성동구 / 성수동 관련만 남긴다. 장소가 비어 있으면 제외한다.
        if "성동" not in place and "성수" not in place:
            continue
        link = str(row.get("SVCURL", "") or "")
        notices.append({
            "title": title,
            "category": classify(title),
            "date": str(row.get("RCPTBGNDT", "") or "")[:10],
            "source": "서울시 공공서비스예약",
            "url": link,
            "place": place,
        })
    return notices, {"source": "seoul_reservation", "status": "ok", "url": url, "count": len(notices)}


def main() -> int:
    now = datetime.now(KST)
    api_key = os.environ.get("SEOUL_API_KEY", "").strip()

    notices = []
    sources = []

    if not api_key:
        sources.append({
            "source": "seoul_reservation",
            "status": "missing_key",
            "note": "SEOUL_API_KEY 환경변수가 없어서 예약 정보를 가져오지 않았다. 키는 data.seoul.go.kr에서 발급받아 GitHub Secrets에 넣는다.",
        })
    else:
        fetched, status = fetch_seoul_reservation(api_key)
        notices.extend(fetched)
        sources.append(status)

    # 성동구청 공지: 공개 RSS/XML 주소를 확인하지 못했음. 자동 수집 대상에서 제외.
    sources.append({
        "source": "seongdong_notice",
        "status": "no_rss_found",
        "note": "성동구청(sd.go.kr) 공지사항의 공개 RSS/XML 주소를 찾지 못했다. RSS 주소가 확인되면 sources.yaml에 추가한 뒤 수집한다. 게시판 무단 크롤링은 하지 않는다.",
        "url": "https://www.sd.go.kr/",
    })

    # 중복 제거: 원문 링크 기준, 링크가 없으면 제목 기준
    seen = set()
    unique = []
    for n in notices:
        key = n.get("url") or n.get("title")
        if key in seen:
            continue
        seen.add(key)
        unique.append(n)

    data = {
        "service": "udong",
        "area": "서울 성동구 성수동 (시범)",
        "generated_at_kst": now.strftime("%Y-%m-%d %H:%M KST"),
        "generated_at": now.isoformat(),
        "sources": sources,
        "notices": unique[:50],
        "spots": [],
        "note": "이 파일은 자동 수집 결과이다. 실제 공지가 0건이면 샘플이 아니라 0건 그대로 기록한다. spots의 실시간 남은 자리 수는 API가 제공하지 않아 이 버전에서는 비워둔다.",
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} notices={len(unique)} sources={len(sources)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
