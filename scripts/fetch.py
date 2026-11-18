#!/usr/bin/env python3
"""
우동 자동 수집 스크립트 v0.3 (핵심: 동네 소식 자동 보기, 시범: 서울 성동구)

출처 (2026-11-18 브라우저로 직접 확인):
  - 성동구청 새소식 게시판 (bbsNo=183, key=1472)
    목록: https://www.sd.go.kr/main/selectBbsNttList.do?bbsNo=183&key=1472
    RSS:  https://www.sd.go.kr/rssBbsNtt.do?bbsNo=183&integrDeptCode=
    RSS는 title/link/guid/pubDate를 제공한다. 항목은 최신 10개이다.
  - 복지 안내 허브: https://www.sd.go.kr/main/contents.do?key=5213
    부모급여 안내: https://www.sd.go.kr/main/contents.do?key=4510
    복지 공지는 새소식 안에 별도 분류가 없고 제목 검색으로 찾는다.
    복지로(www.bokjiro.go.kr)는 별도 게시판이 없고 신청처로 안내된다.

주의:
  - 이 서버(VM)에서 sd.go.kr로 직접 가져오면 연결이 끊기는 경우가 있다.
    그래서 RSS 가져오기가 실패하면 가짜 소식을 만들지 않고,
    기존 data.json의 소식을 그대로 두고 status에 실패를 기록한다.
    정기 작업에서는 브라우저로 RSS 목록을 확인하는 방식을 같이 쓴다.
  - 제목·날짜·원문 링크만 저장하고 본문을 복사하지 않는다.
  - API 키는 환경변수 SEOUL_API_KEY로만 받는다. 코드에 키를 넣지 않는다.

실행:
  python3 scripts/fetch.py
"""
import json
import os
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data.json"
KST = timezone(timedelta(hours=9))
RSS_URL = "https://www.sd.go.kr/rssBbsNtt.do?bbsNo=183&integrDeptCode="

CATEGORIES = [
    ("urgent", ["단수", "정전", "공사", "통제", "긴급", "재난", "한파"]),
    ("welfare", ["복지", "지원", "부모급여", "돌봄", "바우처", "신청"]),
    ("event", ["행사", "축제", "장터", "공연", "전시", "강좌", "페스티벌"]),
    ("work", ["공사", "교통", "도로", "주차", "재개발", "건축"]),
    ("life", ["생활", "청소", "쓰레기", "폐기물", "민원", "안전"]),
]


def classify(title: str) -> str:
    for cat, words in CATEGORIES:
        if any(w in title for w in words):
            return cat
    return "life"


def fetch_rss():
    req = urllib.request.Request(
        RSS_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (udong/0.3)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
    except Exception as e:
        return [], {"source": "seongdong_rss", "status": f"fetch_failed:{type(e).__name__}", "url": RSS_URL,
                    "note": "이 서버에서 직접 가져오기가 끊겼다. 브라우저로는 읽힌다. 기존 소식을 유지한다."}
    try:
        root = ET.fromstring(raw)
    except Exception as e:
        return [], {"source": "seongdong_rss", "status": f"parse_failed:{type(e).__name__}", "url": RSS_URL}
    notices = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        date = ""
        if pub:
            try:
                date = parsedate_to_datetime(pub).astimezone(KST).strftime("%Y-%m-%d")
            except Exception:
                date = pub[:10]
        if not title:
            continue
        notices.append({
            "title": title,
            "category": classify(title),
            "date": date,
            "source": "성동구청 새소식",
            "url": link,
        })
    return notices, {"source": "seongdong_rss", "status": "ok", "url": RSS_URL, "count": len(notices)}


def main() -> int:
    now = datetime.now(KST)
    # 기존 data.json이 있으면, 가져오기가 실패했을 때 소식을 유지하기 위해 읽어둔다.
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            old = {}

    notices, rss_status = fetch_rss()
    sources = [rss_status]
    if not notices and old.get("notices"):
        # 브라우저로 확인한 기존 소식을 유지할 때는 그 출처 기록도 유지한다.
        sources = old.get("sources", []) + [rss_status]

    # 서울시 예약 API는 소식 핵심이 아니라 부가 기능이다. 키가 없으면 상태만 기록한다.
    if not os.environ.get("SEOUL_API_KEY", "").strip():
        sources.append({"source": "seoul_reservation", "status": "missing_key",
                        "note": "SEOUL_API_KEY가 없어서 예약 정보를 가져오지 않았다."})
    else:
        sources.append({"source": "seoul_reservation", "status": "not_checked_in_news_mode",
                        "note": "v0.3은 소식 중심이다. 예약은 다음 단계에서 확인한다."})

    if notices:
        final_notices = notices[:20]
    else:
        # 가져오기 실패: 기존 소식을 그대로 두고, 새로 만든 가짜 소식은 넣지 않는다.
        final_notices = old.get("notices", [])

    data = {
        "service": "udong",
        "area": "서울 성동구 성수동 (시범)",
        "generated_at_kst": now.strftime("%Y-%m-%d %H:%M KST"),
        "generated_at": now.isoformat(),
        "sources": sources,
        "notices": final_notices,
        "spots": old.get("spots", []),
        "note": "동네 소식 중심이다. 제목·날짜·원문 링크만 저장하고 본문은 복사하지 않는다. RSS 가져오기가 실패하면 기존 소식을 유지한다.",
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} notices={len(final_notices)} rss={rss_status['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
