#!/usr/bin/env python3
"""
우동 자동 수집 스크립트 v0.4 (핵심: 동네 소식 자동 보기)

시범 1곳 + RSS 확인된 7곳, 총 8개 지역을 돈다.
  - 서울 성동구: data.json (기존 동작 그대로 유지 — 이 서버에서 직접
    가져오면 연결이 끊겨, 실패 시 브라우저로 확인한 기존 소식을 유지한다)
  - 강남구, 서초구, 노원구, 구로구, 금천구(보도자료), 대구광역시, 군위군:
    data_nationwide.json (2026-11-18 서버 직접 가져오기 + 브라우저로 확인됨)
  - 구미시는 제외: RSS 주소로 열면 구미시청 HTML 포털이 나오고 RSS 항목이
    없다. 브라우저(2026-11-18 14:07 KST)와 서버 직접 가져오기 둘 다 확인했다.

출처 (2026-11-18 확인):
  - 성동구청 새소식 RSS: https://www.sd.go.kr/rssBbsNtt.do?bbsNo=183&integrDeptCode=
  - 강남구 공지 RSS: https://www.gangnam.go.kr/portal/bbs/rss.do?bbsId=B_000001
  - 서초구 공지 RSS: https://www.seocho.go.kr/rss/notice.jsp
  - 노원구 공지 RSS: https://www.nowon.kr/www/user/bbs/ND_selectRssList.do?q_bbsCode=1001&q_estnColumn1=11
  - 구로구 새소식 RSS: https://www.guro.go.kr/rssBbsNtt.do?bbsNo=662&integrDeptCode=
  - 금천구 보도자료 RSS: https://www.geumcheon.go.kr/portal/rssBbsNtt.do?key=297&bbsNo=8
  - 대구시 공지 RSS: http://www.daegu.go.kr/icms/rss/feed.do?id=BBS_00029
  - 군위군 알립니다 RSS: http://gunwi.go.kr/programs/board/rss.do?mnu_uid=101

주의:
  - 제목·날짜·원문 링크만 저장하고 본문을 복사하지 않는다.
  - 한 지역 가져오기가 실패해도 다른 지역은 계속 돌고, 실패한 지역은
    기존 data_nationwide.json의 소식을 유지한다. 가짜 소식은 만들지 않는다.
  - API 키는 환경변수 SEOUL_API_KEY로만 받는다. 코드에 키를 넣지 않는다.

실행:
  python3 scripts/fetch.py
  -> data.json (성동구, 기존과 동일), data_nationwide.json (8개 지역 중 성동 제외 7곳)
"""
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data.json"
OUT_NATIONWIDE = ROOT / "data_nationwide.json"
KST = timezone(timedelta(hours=9))
RSS_URL = "https://www.sd.go.kr/rssBbsNtt.do?bbsNo=183&integrDeptCode="

# 성동구를 제외한, RSS가 살아 있는 것이 확인된 지역들.
# board_note가 있으면 그 게시판 성격(새소식/보도자료)을 source 라벨에 적는다.
FEEDS = [
    {"region": "서울 강남구", "board": "강남구청 공지사항",
     "rss": "https://www.gangnam.go.kr/portal/bbs/rss.do?bbsId=B_000001",
     "list_url": "http://www.gangnam.go.kr/board/B_000001/list.do?mid=ID05_040101"},
    {"region": "서울 서초구", "board": "서초구청 공지사항",
     "rss": "https://www.seocho.go.kr/rss/notice.jsp",
     "list_url": "https://www.seocho.go.kr/site/seocho/ex/bbs/List.do?cbIdx=57"},
    {"region": "서울 노원구", "board": "노원구청 공지사항",
     "rss": "https://www.nowon.kr/www/user/bbs/ND_selectRssList.do?q_bbsCode=1001&q_estnColumn1=11"},
    {"region": "서울 구로구", "board": "구로구청 새소식",
     "rss": "https://www.guro.go.kr/rssBbsNtt.do?bbsNo=662&integrDeptCode=",
     "list_url": "http://www.guro.go.kr/www/sub.do?key=1790"},
    {"region": "서울 금천구", "board": "금천구청 보도자료",
     "rss": "https://www.geumcheon.go.kr/portal/rssBbsNtt.do?key=297&bbsNo=8",
     "list_url": "https://www.geumcheon.go.kr/portal/selectBbsNttList.do?bbsNo=8&key=297",
     "board_note": "보도자료 게시판이다. 공지 게시판(bbsNo)은 별도 확인이 필요하다."},
    {"region": "대구광역시", "board": "대구시 공지사항",
     "rss": "http://www.daegu.go.kr/icms/rss/feed.do?id=BBS_00029",
     "list_url": "https://www.daegu.go.kr/index.do?menu_id=00000854&menu_link=/icms/bbs/selectBoardList.do?bbsId=BBS_00029"},
    {"region": "대구 군위군", "board": "군위군 알립니다",
     "rss": "http://gunwi.go.kr/programs/board/rss.do?mnu_uid=101"},
]

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


def parse_date(raw: str) -> str:
    """RSS 날짜를 YYYY-MM-DD로. 지역마다 형식이 달라서 여러 형식을 시도한다.
    예: 'Wed, 18 Nov 2026 01:06:54 GMT', '2026-11-18', '2026.11.18',
    '2026-11-18 13:23:10', 'Tue Nov 17 17:25:06 KST 2026',
    '수, 18 11월 2026 14:00:03 +0900'"""
    raw = (raw or "").strip()
    if not raw:
        return ""
    # 한국어 날짜: '수, 18 11월 2026 ...' -> '18 11 2026'으로 정리
    cleaned = re.sub(r"^[월화수목금토일],\s*", "", raw)
    cleaned = re.sub(r"(\d{1,2})월", r"\1", cleaned)
    cleaned = cleaned.replace("KST", "").strip()
    for candidate in (cleaned, raw):
        try:
            dt = parsedate_to_datetime(candidate)
            if dt is not None:
                return dt.astimezone(KST).strftime("%Y-%m-%d")
        except Exception:
            pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(cleaned[:19], fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    m = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", cleaned)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # 한국어식 '18 11 2026' (일 월 연) 순서: '수, 18 11월 2026 ...'에서 온다.
    m = re.search(r"(\d{1,2})\s+(\d{1,2})\s+(\d{4})", cleaned)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return raw[:10]


def _item_text(item, tag):
    el = item.find(tag)
    if el is not None and (el.text or "").strip():
        return el.text.strip()
    # dc:date 같은 네임스페이스 태그
    for child in item:
        if child.tag.endswith("}" + tag) and (child.text or "").strip():
            return child.text.strip()
    return ""


def parse_rss(raw: bytes, board: str, region: str):
    root = ET.fromstring(raw)
    notices = []
    for item in root.iter("item"):
        title = _item_text(item, "title")
        if not title:
            continue
        link = _item_text(item, "link")
        if not link:
            # <link href="..."/> 형태
            link_el = item.find("link")
            if link_el is not None:
                link = link_el.get("href", "")
        pub = _item_text(item, "pubDate") or _item_text(item, "date")
        notices.append({
            "title": title,
            "category": classify(title),
            "date": parse_date(pub),
            "region": region,
            "source": board,
            "url": link,
        })
    return notices


def fetch_one(feed):
    req = urllib.request.Request(
        feed["rss"],
        headers={
            "User-Agent": "Mozilla/5.0 (udong/0.4)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
    except Exception as e:
        return [], {"region": feed["region"], "source": feed["board"],
                    "status": f"fetch_failed:{type(e).__name__}", "url": feed["rss"],
                    "note": "직접 가져오기가 실패했다. 기존 소식을 유지한다."}
    try:
        notices = parse_rss(raw, feed["board"], feed["region"])
    except Exception as e:
        return [], {"region": feed["region"], "source": feed["board"],
                    "status": f"parse_failed:{type(e).__name__}", "url": feed["rss"]}
    return notices, {"region": feed["region"], "source": feed["board"],
                     "status": "ok", "url": feed["rss"], "count": len(notices)}


def fetch_rss():
    req = urllib.request.Request(
        RSS_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (udong/0.4)",
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
        notices = parse_rss(raw, "성동구청 새소식", "서울 성동구")
    except Exception as e:
        return [], {"source": "seongdong_rss", "status": f"parse_failed:{type(e).__name__}", "url": RSS_URL}
    return notices, {"source": "seongdong_rss", "status": "ok", "url": RSS_URL, "count": len(notices)}


def main() -> int:
    now = datetime.now(KST)
    # --- 성동구 (data.json, 기존 동작 그대로) ---
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            old = {}

    notices, rss_status = fetch_rss()
    sources = [rss_status]
    if not notices and old.get("notices"):
        sources = old.get("sources", []) + [rss_status]

    if not os.environ.get("SEOUL_API_KEY", "").strip():
        sources.append({"source": "seoul_reservation", "status": "missing_key",
                        "note": "SEOUL_API_KEY가 없어서 예약 정보를 가져오지 않았다."})
    else:
        sources.append({"source": "seoul_reservation", "status": "not_checked_in_news_mode",
                        "note": "v0.4는 소식 중심이다. 예약은 다음 단계에서 확인한다."})

    final_notices = notices[:20] if notices else old.get("notices", [])

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

    # --- 전국 7곳 (data_nationwide.json, 성동구 제외) ---
    old_nw = {}
    if OUT_NATIONWIDE.exists():
        try:
            old_nw = json.loads(OUT_NATIONWIDE.read_text(encoding="utf-8"))
        except Exception:
            old_nw = {}
    old_regions = {r.get("region"): r for r in old_nw.get("regions", [])}

    regions = []
    total = 0
    for feed in FEEDS:
        items, status = fetch_one(feed)
        if items:
            region_notices = items[:10]
            total += len(region_notices)
        else:
            # 실패 시 기존 소식을 유지하고, 새로 만든 가짜 소식은 넣지 않는다.
            region_notices = old_regions.get(feed["region"], {}).get("notices", [])
        regions.append({
            "region": feed["region"],
            "board": feed["board"],
            "rss": feed["rss"],
            "list_url": feed.get("list_url", ""),
            "status": status["status"],
            "count": len(region_notices),
            "notices": region_notices,
        })
        print(f"  {feed['region']}: {status['status']} notices={len(region_notices)}")

    nw = {
        "service": "udong",
        "generated_at_kst": now.strftime("%Y-%m-%d %H:%M KST"),
        "generated_at": now.isoformat(),
        "regions": regions,
        "total_notices": total,
        "excluded": [
            {"region": "경북 구미시",
             "rss": "https://www.gumi.go.kr/portal/rssservice/RssServiceDetail.do?rssId=00000000000000000001",
             "reason": "RSS 주소로 열면 구미시청 HTML 포털이 나오고 RSS 항목이 없다. 브라우저(2026-11-18 14:07 KST)와 서버 직접 가져오기 둘 다 확인했다."},
        ],
        "note": "동네 소식 중심이다. 제목·날짜·원문 링크만 저장하고 본문은 복사하지 않는다. 한 지역 가져오기가 실패하면 그 지역의 기존 소식을 유지한다. 성동구는 data.json에 따로 있다.",
    }
    OUT_NATIONWIDE.write_text(json.dumps(nw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_NATIONWIDE} regions={len(regions)} total_notices={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
