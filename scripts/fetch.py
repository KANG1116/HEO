#!/usr/bin/env python3
"""
우동 자동 수집 스크립트 v0.5 (핵심: 동네 소식 자동 보기)

시범 1곳 + RSS 확인된 8곳 + 목록 HTML 파싱 확인된 13곳, 총 22개 지역을 돈다.
(성동구는 data.json에 따로 있다.)
  - 서울 성동구: data.json (기존 동작 그대로 유지 — 이 서버에서 직접
    가져오면 연결이 끊겨, 실패 시 브라우저로 확인한 기존 소식을 유지한다)
  - RSS 8곳: 강남구, 서초구, 노원구, 구로구, 금천구(보도자료), 대구광역시,
    군위군, 도봉구 동 게시판(방학1동 위주, 본청 공지 아님)
    -> data_nationwide.json (2026-11-18 서버 직접 가져오기 + 브라우저로 확인됨)
  - 목록 HTML 파싱 13곳: 경기 하남시·가평군·군포시·양주시·파주시·이천시·김포시,
    서울 송파구·영등포구·종로구·마포구, 세종특별자치시, 대전 동구
    -> data_nationwide.json (2026-11-18 서버 직접 가져오기 + 브라우저로 확인됨)
  - 구미시는 제외: RSS 주소로 열면 구미시청 HTML 포털이 나오고 RSS 항목이
    없다. 브라우저(2026-11-18 14:07 KST)와 서버 직접 가져오기 둘 다 확인했다.
  - 이번 단계에서 제외(목록 파싱 미확인): 연천군(직접 가져오기 끊김,
    browser.open도 실패), 안성시(목록은 파싱되나 상세 링크가 POST 방식이라
    GET으로 미검증), 용산구(직접 가져오기 끊김, 스냅샷 66일 전),
    중구(직접 가져오기 끊김, 개별 글 cid가 목록에 노출되지 않음).
    정부24 지자체 소식은 보조용으로만 본다(지역 필터 srchArea 확인됨,
    원문보기는 각 지자체 홈페이지로 감. 공고·고시 위주라 주 경로 아님).

출처 (2026-11-18 확인):
  - 성동구청 새소식 RSS: https://www.sd.go.kr/rssBbsNtt.do?bbsNo=183&integrDeptCode=
  - 강남구 공지 RSS: https://www.gangnam.go.kr/portal/bbs/rss.do?bbsId=B_000001
  - 서초구 공지 RSS: https://www.seocho.go.kr/rss/notice.jsp
  - 노원구 공지 RSS: https://www.nowon.kr/www/user/bbs/ND_selectRssList.do?q_bbsCode=1001&q_estnColumn1=11
  - 구로구 새소식 RSS: https://www.guro.go.kr/rssBbsNtt.do?bbsNo=662&integrDeptCode=
  - 금천구 보도자료 RSS: https://www.geumcheon.go.kr/portal/rssBbsNtt.do?key=297&bbsNo=8
  - 대구시 공지 RSS: http://www.daegu.go.kr/icms/rss/feed.do?id=BBS_00029
  - 군위군 알립니다 RSS: http://gunwi.go.kr/programs/board/rss.do?mnu_uid=101
  - 도봉구 동 게시판 RSS: https://www.dobong.go.kr/WDB_common/rss/bbs.asp?code=10009682
  - 하남시 공지 목록: https://www.hanam.go.kr/www/selectBbsNttList.do?key=170&bbsNo=30
  - 가평군 공지 목록: https://www.gp.go.kr/portal/selectBbsNttList.do?key=501&bbsNo=150
  - 군포시 공지 목록: https://www.gunpo.go.kr/www/selectBbsNttList.do?key=3890&bbsNo=675
  - 양주시 공지 목록: https://www.yangju.go.kr/www/selectBbsNttList.do?bbsNo=13&key=202
  - 파주시 새소식 목록: https://www.paju.go.kr/user/plan_news/board/BD_board.list.do?seq=20171219114930714&bbsCd=2001
  - 이천시 공지 목록: https://www.icheon.go.kr/portal/board/post/list.do?bcIdx=698&mid=0401010000
  - 김포시 공지 목록: https://gimpo.go.kr/portal/selectBbsNttList.do?key=3309&bbsNo=56
  - 송파구 공지 목록: https://www.songpa.go.kr/www/selectBbsNttList.do?bbsNo=92&pageUnit=10&key=2775&pageIndex=1
  - 영등포구 공지 목록: https://www.ydp.go.kr/www/selectBbsNttList.do?bbsNo=40&key=2848
  - 종로구 공지 목록: http://jongno.go.kr/portal/bbs/selectBoardList.do?bbsId=BBSMSTR_000000000201&menuId=1752&menuNo=1752
  - 마포구 공지 목록: https://www.mapo.go.kr/site/main/board/notice/list
  - 세종시 공지 목록: https://www.sejong.go.kr/bbs/R0071/list.do
  - 대전 동구 공지 목록: https://donggu.go.kr/dg/kor/article/newsNotice

주의:
  - 제목·날짜·원문 링크만 저장하고 본문을 복사하지 않는다.
  - 한 지역 가져오기가 실패해도 다른 지역은 계속 돌고, 실패한 지역은
    기존 data_nationwide.json의 소식을 유지한다. 가짜 소식은 만들지 않는다.
  - 목록에 보이는 href/onclick 식별자만 쓴다. 추측으로 URL을 만들지 않는다.
    단, onclick 방식(파주·이천·종로·대전 동구)은 해당 사이트 JS에서 확인한
    이동 패턴을 쓰고, 상세 페이지 1건씩 직접 가져와 검증했다.
  - API 키는 환경변수 SEOUL_API_KEY로만 받는다. 코드에 키를 넣지 않는다.

실행:
  python3 scripts/fetch.py
  -> data.json (성동구, 기존과 동일), data_nationwide.json (성동 제외 21곳)
"""
import html as html_lib
import json
import os
import re
import sys
import urllib.parse
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
    {"region": "서울 도봉구", "board": "도봉구 동 게시판(방학1동)",
     "rss": "https://www.dobong.go.kr/WDB_common/rss/bbs.asp?code=10009682",
     "board_note": "동 게시판이다. 본청 공지 게시판이 아니다. 최신이 2026-11-12로 일주일 전이다."},
]

# 목록 HTML 파싱이 확인된 지역들. kind별 파서(아래 LIST_PARSERS)를 쓴다.
# bbs: selectBbsNttList.do 계열 — 제목 <a>의 href에 nttNo가 있다.
# sejong: href에 불투명 nttId가 있다. href를 그대로 쓴다.
# donggu: 제목 <a>의 href는 '#', onclick article.view('<seq>')에서 seq를 쓴다.
# paju: onclick jsView('2001', '<seq>', ...)에서 seq를 쓴다.
# icheon: data-req-get-p-idx에서 idx를 쓴다.
# jongno: javascript:viewMove('<nttId>')에서 nttId를 쓴다.
# mapo: 제목 <a>의 href가 /site/main/board/notice/<숫자> 형태이다.
LIST_SOURCES = [
    {"region": "경기 하남시", "board": "하남시청 공지사항", "kind": "bbs",
     "list_url": "https://www.hanam.go.kr/www/selectBbsNttList.do?key=170&bbsNo=30",
     "bbs_no": 30},
    {"region": "경기 가평군", "board": "가평군청 공지사항", "kind": "bbs",
     "list_url": "https://www.gp.go.kr/portal/selectBbsNttList.do?key=501&bbsNo=150",
     "bbs_no": 150},
    {"region": "경기 군포시", "board": "군포시청 공지사항", "kind": "bbs",
     "list_url": "https://www.gunpo.go.kr/www/selectBbsNttList.do?key=3890&bbsNo=675",
     "bbs_no": 675},
    {"region": "경기 양주시", "board": "양주시청 공지사항", "kind": "bbs",
     "list_url": "https://www.yangju.go.kr/www/selectBbsNttList.do?bbsNo=13&key=202",
     "bbs_no": 13},
    {"region": "경기 파주시", "board": "파주시청 새소식", "kind": "paju",
     "list_url": "https://www.paju.go.kr/user/plan_news/board/BD_board.list.do?seq=20171219114930714&bbsCd=2001"},
    {"region": "경기 이천시", "board": "이천시청 공지사항", "kind": "icheon",
     "list_url": "https://www.icheon.go.kr/portal/board/post/list.do?bcIdx=698&mid=0401010000"},
    {"region": "경기 김포시", "board": "김포시청 공지사항", "kind": "bbs",
     "list_url": "https://gimpo.go.kr/portal/selectBbsNttList.do?key=3309&bbsNo=56",
     "bbs_no": 56,
     "board_note": "최근 글이 하성면 위주라 시 전체 게시판인지 추후 재확인 필요. RSS 버튼은 있으나 피드가 404이다."},
    {"region": "서울 송파구", "board": "송파구청 공지사항", "kind": "bbs",
     "list_url": "https://www.songpa.go.kr/www/selectBbsNttList.do?bbsNo=92&pageUnit=10&key=2775&pageIndex=1",
     "bbs_no": 92,
     "board_note": "http는 리다이렉트 페이지만 반환하므로 https로 가져온다."},
    {"region": "서울 영등포구", "board": "영등포구청 공지사항", "kind": "bbs",
     "list_url": "https://www.ydp.go.kr/www/selectBbsNttList.do?bbsNo=40&key=2848",
     "bbs_no": 40},
    {"region": "서울 종로구", "board": "종로구청 공지사항", "kind": "jongno",
     "list_url": "http://jongno.go.kr/portal/bbs/selectBoardList.do?bbsId=BBSMSTR_000000000201&menuId=1752&menuNo=1752"},
    {"region": "서울 마포구", "board": "마포구청 공지사항", "kind": "mapo",
     "list_url": "https://www.mapo.go.kr/site/main/board/notice/list"},
    {"region": "세종특별자치시", "board": "세종시청 공지사항", "kind": "sejong",
     "list_url": "https://www.sejong.go.kr/bbs/R0071/list.do"},
    {"region": "대전 동구", "board": "대전 동구청 공지사항", "kind": "donggu",
     "list_url": "https://donggu.go.kr/dg/kor/article/newsNotice"},
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
    '수, 18 11월 2026 14:00:03 +0900', '2026년11월18일'"""
    raw = (raw or "").strip()
    if not raw:
        return ""
    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", raw)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
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
            "User-Agent": "Mozilla/5.0 (udong/0.5)",
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
            "User-Agent": "Mozilla/5.0 (udong/0.5)",
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


# ---------------------------------------------------------------------------
# 목록 HTML 파싱 (v0.5)
# ---------------------------------------------------------------------------

def fetch_html(url: str, timeout: int = 25):
    """목록 페이지를 가져와 디코드된 HTML 텍스트를 돌려준다.
    실패하면 (None, 상태문자열)을 돌려준다."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            ctype = resp.headers.get_content_charset() or ""
    except Exception as e:
        return None, f"fetch_failed:{type(e).__name__}"
    charset = ctype or "utf-8"
    try:
        text = raw.decode(charset, errors="replace")
    except Exception:
        text = raw.decode("utf-8", errors="replace")
    m = re.search(r'<meta[^>]*charset=["\']?([A-Za-z0-9_-]+)', text, re.I)
    if m and m.group(1).lower() not in ("utf-8", charset.lower()):
        try:
            text = raw.decode(m.group(1), errors="replace")
        except Exception:
            pass
    return text, "ok"


def _strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html_lib.unescape(s)).strip()


def _clean_title(t: str) -> str:
    t = _strip_tags(t)
    # 제목 뒤에 붙는 새글/핫이슈/NEW 배지 제거
    t = re.sub(r"\s*(새\s?글|핫이슈|NEW)\s*$", "", t, flags=re.I)
    return t.strip()


def _tr_rows(html_text: str):
    return re.findall(r"<tr[^>]*>(.*?)</tr>", html_text, re.S | re.I)


def _td_cells(row: str):
    return re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)


def _is_fixed_row(row: str) -> bool:
    """상단 고정 공지 행인지. 고정글은 일반글과 중복되거나 날짜순이 아니라서 제외한다."""
    if re.search(r"p-notice", row):
        return True
    cells = _td_cells(row)
    if cells and _strip_tags(cells[0]) in ("공지", ""):
        return True
    return False


_DATE_FULL = re.compile(r"^(\d{4})[-./](\d{1,2})[-./](\d{1,2})(\([A-Za-z]+\))?$")
_DATE_KO = re.compile(r"^(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일$")


def _norm_date_cell(text: str) -> str:
    text = (text or "").strip()
    m = _DATE_FULL.match(text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = _DATE_KO.match(text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def _extract_date(row_html: str, cells=None) -> str:
    """행에서 날짜를 찾아 YYYY-MM-DD로. 날짜 셀을 먼저 보고, 없으면 행 전체에서 찾는다."""
    if cells:
        for c in cells:
            d = _norm_date_cell(_strip_tags(c))
            if d:
                return d
    t = _strip_tags(row_html)
    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", t)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", t)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def _notice(region, board, title, date, url):
    return {"title": title, "category": classify(title), "date": date,
            "region": region, "source": board, "url": url}


def parse_bbs_list(html_text: str, src: dict):
    """selectBbsNttList.do 계열. 제목 <a>의 href에 bbsNo와 nttNo가 있다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(r'<a[^>]*href="([^"]*selectBbsNttView\.do[^"]*)"[^>]*>(.*?)</a>',
                      row, re.S | re.I)
        if not m:
            continue
        href, atitle = m.group(1), m.group(2)
        bbs = re.search(r"bbsNo=(\d+)", href)
        if not bbs or bbs.group(1) != str(src["bbs_no"]):
            continue
        ntt = re.search(r"nttNo=(\d+)", href)
        if not ntt or ntt.group(1) in seen:
            continue
        seen.add(ntt.group(1))
        title = _clean_title(atitle)
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = urllib.parse.urljoin(src["list_url"], html_lib.unescape(href))
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices[:10]


def parse_sejong(html_text: str, src: dict):
    """세종시. 제목 <a>의 href에 불투명 nttId가 있다. href를 그대로 쓴다.
    jsessionid가 붙은 두 번째 view.do 링크는 제목 링크가 아니므로 제외한다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        anchors = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', row, re.S | re.I)
        pick = None
        for href, atitle in anchors:
            if "view.do" in href and "nttId=" in href and "jsessionid" not in href:
                pick = (href, atitle)
                break
        if not pick:
            continue
        href, atitle = pick
        m = re.search(r"nttId=([A-Za-z0-9]+)", href)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        title = _clean_title(atitle)
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = urllib.parse.urljoin(src["list_url"], html_lib.unescape(href))
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices[:10]


def parse_donggu(html_text: str, src: dict):
    """대전 동구. 제목 <a>의 href는 '#'이고 onclick article.view('<seq>')로 이동한다.
    사이트 JS에서 확인한 패턴으로 상세 URL을 구성한다."""
    notices, seen = [], set()
    for li in re.findall(r"<li[^>]*>(.*?)</li>", html_text, re.S | re.I):
        if re.search(r"\[\s*공지\s*\]", li):
            continue
        m = re.search(r"article\.view\('(\d+)'\)", li)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        am = re.search(r"<a[^>]*>(.*?)</a>", li, re.S)
        title = _clean_title(am.group(1)) if am else ""
        if not title:
            continue
        date = _extract_date(li)
        url = f"https://donggu.go.kr/dg/kor/article/newsNotice/{m.group(1)}"
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices[:10]


def parse_paju(html_text: str, src: dict):
    """파주시. 제목 링크는 javascript:void(0)이고 onclick jsView('2001', '<seq>', ...)로 이동한다.
    사이트 JS(board.js)에서 확인한 패턴으로 상세 URL을 구성한다.
    주의: 공지 1건이 바깥 <li> 안에 안쪽 <li>(날짜 등)를 포함하므로, <li> 단위로
    자르지 않고 jsView 위치를 기준으로 제목과 날짜를 찾는다."""
    notices, seen = [], set()
    pat = re.compile(r"jsView\('2001',\s*'(\d+)'[^>]*>\s*<strong class=\"subject\">(.*?)</strong>",
                     re.S)
    for m in pat.finditer(html_text):
        seq, raw_title = m.group(1), m.group(2)
        if seq in seen:
            continue
        seen.add(seq)
        raw_title = re.sub(r'<span class="category">.*?</span>', "", raw_title, flags=re.S)
        raw_title = re.sub(r'<i class="ico-new">.*?</i>', "", raw_title, flags=re.S)
        title = _clean_title(raw_title)
        if not title:
            continue
        # 날짜: 이 항목 앞쪽에서 가장 가까운 <li>YYYY/MM/DD</li> (머리말의 등록일)
        before = html_text[max(0, m.start() - 1200):m.start()]
        dm = None
        for dm in re.finditer(r"<li>\s*(\d{4})/(\d{1,2})/(\d{1,2})\s*</li>", before):
            pass
        date = ""
        if dm:
            date = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}"
        url = f"https://www.paju.go.kr/user/plan_news/board/BD_board.view.do?bbsCd=2001&seq={seq}"
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices[:10]


def parse_icheon(html_text: str, src: dict):
    """이천시. 제목 <a>에 data-req-get-p-idx가 있다. 상세는 GET view.do?idx=... 로 열린다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(r'data-req-get-p-idx="(\d+)"', row)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        am = re.search(r'<a[^>]*data-req-get-p-idx="\d+"[^>]*>(.*?)</a>', row, re.S)
        title = _clean_title(am.group(1)) if am else ""
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = f"https://www.icheon.go.kr/portal/board/post/view.do?bcIdx=698&mid=0401010000&idx={m.group(1)}"
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices[:10]


def parse_jongno(html_text: str, src: dict):
    """종로구. 제목 링크는 javascript:viewMove('<nttId>')이다.
    페이지 내 JS(viewMove)에서 확인한 패턴으로 상세 URL을 구성한다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(r"viewMove\('(\d+)'\)", row)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        am = re.search(r"<a[^>]*viewMove[^>]*>(.*?)</a>", row, re.S)
        title = _clean_title(am.group(1)) if am else ""
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = ("https://jongno.go.kr/portal/bbs/selectBoardArticle.do"
               f"?bbsId=BBSMSTR_000000000201&menuNo=1752&menuId=1752&nttId={m.group(1)}")
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices[:10]


def parse_mapo(html_text: str, src: dict):
    """마포구. 제목 <a>의 href가 /site/main/board/notice/<숫자> 형태이다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(r'<a[^>]*href="(/site/main/board/notice/\d+\?[^"]*)"[^>]*>(.*?)</a>',
                      row, re.S | re.I)
        if not m:
            continue
        href, atitle = m.group(1), m.group(2)
        num = re.search(r"/notice/(\d+)", href)
        if not num or num.group(1) in seen:
            continue
        seen.add(num.group(1))
        title = _clean_title(atitle)
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = urllib.parse.urljoin(src["list_url"], html_lib.unescape(href))
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices[:10]


LIST_PARSERS = {
    "bbs": parse_bbs_list,
    "sejong": parse_sejong,
    "donggu": parse_donggu,
    "paju": parse_paju,
    "icheon": parse_icheon,
    "jongno": parse_jongno,
    "mapo": parse_mapo,
}


def fetch_list(src: dict):
    html_text, status = fetch_html(src["list_url"])
    if html_text is None:
        return [], {"region": src["region"], "source": src["board"],
                    "status": status, "url": src["list_url"],
                    "note": "목록 가져오기가 실패했다. 기존 소식을 유지한다."}
    try:
        notices = LIST_PARSERS[src["kind"]](html_text, src)
    except Exception as e:
        return [], {"region": src["region"], "source": src["board"],
                    "status": f"parse_failed:{type(e).__name__}", "url": src["list_url"]}
    # 목록 순서는 게시판마다 어긋날 수 있어(예: 마포구 첫 행이 08-24) 날짜 내림차순으로 정리한다.
    notices.sort(key=lambda n: n.get("date", ""), reverse=True)
    return notices, {"region": src["region"], "source": src["board"],
                     "status": "ok", "url": src["list_url"], "count": len(notices)}


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
                        "note": "v0.5는 소식 중심이다. 예약은 다음 단계에서 확인한다."})

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

    # --- 전국 (data_nationwide.json, 성동구 제외) ---
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
        else:
            # 실패 시 기존 소식을 유지하고, 새로 만든 가짜 소식은 넣지 않는다.
            region_notices = old_regions.get(feed["region"], {}).get("notices", [])
        total += len(region_notices)
        entry = {
            "region": feed["region"],
            "board": feed["board"],
            "rss": feed["rss"],
            "list_url": feed.get("list_url", ""),
            "status": status["status"],
            "count": len(region_notices),
            "notices": region_notices,
        }
        if feed.get("board_note"):
            entry["board_note"] = feed["board_note"]
        regions.append(entry)
        print(f"  {feed['region']}: {status['status']} notices={len(region_notices)}")

    for src in LIST_SOURCES:
        items, status = fetch_list(src)
        if items:
            region_notices = items[:10]
        else:
            # 실패 시 기존 소식을 유지하고, 새로 만든 가짜 소식은 넣지 않는다.
            region_notices = old_regions.get(src["region"], {}).get("notices", [])
        total += len(region_notices)
        entry = {
            "region": src["region"],
            "board": src["board"],
            "list_url": src["list_url"],
            "method": "html_list",
            "status": status["status"],
            "count": len(region_notices),
            "notices": region_notices,
        }
        if src.get("board_note"):
            entry["board_note"] = src["board_note"]
        regions.append(entry)
        print(f"  {src['region']}: {status['status']} notices={len(region_notices)}")

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
            {"region": "경기 연천군",
             "list_url": "https://www.yeoncheon.go.kr/www/selectBbsNttList.do?key=4799&bbsNo=220",
             "reason": "목록 가져오기가 안 된다. 서버 직접 가져오기는 연결이 끊기고(RemoteDisconnected), browser.open도 가져오기 실패였다(2026-11-18)."},
            {"region": "경기 안성시",
             "list_url": "https://www.anseong.go.kr/portal/bbs/list.do?ptIdx=16&mId=0501010000",
             "reason": "목록은 파싱되나 상세 링크가 POST 폼 제출 방식이라 GET 주소가 미검증이다. bIdx GET은 타임아웃, idx GET은 '게시판이 삭제되었거나 존재하지 않습니다' 알림만 반환했다(2026-11-18)."},
            {"region": "서울 용산구",
             "list_url": "http://yongsan.go.kr/portal/bbs/B0000041/list.do?menuNo=200228&pageUnit=10&pageIndex=241",
             "reason": "서버 직접 가져오기가 끊기고, 확인된 스냅샷은 66일 전(2026-09-13)이라 최신 목록을 알 수 없다. 주어진 URL은 pageIndex=241이라 2021년 구간을 가리킨다(2026-11-18)."},
            {"region": "서울 중구",
             "list_url": "https://www.junggu.seoul.kr/content.do?cmsid=14231",
             "reason": "서버 직접 가져오기가 끊기고, browser.open 스냅샷으로는 제목·날짜만 보이고 개별 글의 cid가 노출되지 않아 원문 URL을 확정할 수 없다(2026-11-18)."},
        ],
        "note": "동네 소식 중심이다. 제목·날짜·원문 링크만 저장하고 본문은 복사하지 않는다. 한 지역 가져오기가 실패하면 그 지역의 기존 소식을 유지한다. 성동구는 data.json에 따로 있다.",
    }
    OUT_NATIONWIDE.write_text(json.dumps(nw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_NATIONWIDE} regions={len(regions)} total_notices={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
