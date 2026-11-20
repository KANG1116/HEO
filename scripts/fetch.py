#!/usr/bin/env python3
"""
우동 자동 수집 스크립트 v0.10 (핵심: 동네 소식 자동 보기)

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
  - 동 행정복지센터 (v0.6, 2026-11-19 확인): 성동구 17개 동 '우리동 소식'
    게시판(selectBbsNttList.do 계열, v0.5 파서 재사용)과 송파구 27개 동
    (게시판 1개 bbsNo=36·key=2619 공유, 동 이름 카테고리 필터) -> data_dong.json.
    송파구는 26개가 아니라 27개 동이다(위례동 포함. 잠실1동·잠실5동은 없음).
    성동구는 이 서버에서 직접 가져오기가 끊겨 브라우저 경유가 필요하다.
    동 소식은 주민등록 공시송달·최고공고 비중이 높아 선별이 필요할 수 있다.
    동별 레지스트리는 sources_dong.yaml에도 기록돼 있다.
  - 동 행정복지센터 (v0.8, 2026-11-19 확인): 13개 구 238개 동 -> data_dong.json.
    관악구 21개 동(게시판 1개 cbIdx=366 공유, deptCode 필터), 강동구 19개 동
    (동별 서브사이트 새소식), 광진구 15개 동(동별 게시판 B0000127, 1~3페이지 합산),
    동대문구 15개 동(게시판 1개 bbsNo=72 공유, 동 카테고리 필터),
    동작구 15개 동(동별 게시판 B0000301, 1~3페이지 합산),
    서대문구 14개 동(동별 시민게시판, EUC-KR),
    성북구 20개 동(게시판 1개 bbsNo=90 공유, 동 카테고리 필터),
    양천구 18개 동(동별 게시판 cbIdx, 1~2페이지 합산),
    은평구 16개 동(게시판 1개 bbsNo=43 공유, 동 카테고리 필터, ep.go.kr www 없음).
    제외: 강북구(동 게시판 B0000199 확인, 목록 URL 미검증, gangbuk.go.kr:18000 직접
    가져오기 타임아웃), 강서구(동 게시판 목록 URL 미확인), 중랑구(동 게시판 목록 URL
    미확인, jungnang.go.kr 연결 실패). 제외 사유는 sources_dong.yaml excluded에 기록.
    카테고리는 기존 classify() 그대로 공사·교통 글을 'work'로 묶는다.
  - 동 행정복지센터 (v0.9, 2026-11-19 확인): 20개 구 343개 동 -> data_dong.json.
    서초구 18개 동(동별 DongList cbIdx=57 + dongCode), 영등포구 18개 동
    (동별 게시판 bbsNo·key, parse_bbs_list 재사용), 마포구 16개 동
    (동별 서브사이트 우리동네소식), 도봉구 14개 동(동별 bbs.asp?code),
    강북구 13개 동(동별 게시판 B0000199, menuNo·dongCd, gangbuk.go.kr:18000),
    구로구 16개 동(게시판 1개 bbsNo=794 공유, 동 카테고리 필터),
    금천구 10개 동(게시판 bbsNo=4 + 부서코드 필터).
    강북구는 이 서버 urllib로는 :18000 포트가 프록시에서 막혀(403) fetch가
    실패할 수 있고, 그 경우 기존 소식을 유지한다(curl로는 200 확인).
    제외: 종로구·중구·용산구·강서구·중랑구(동 게시판 목록 URL 미확인).
  - 동 행정복지센터 (v0.10, 2026-11-20 확인): 21개 구 358개 동 -> data_dong.json.
    중구 15개 동(동별 CMS 게시판 content.do?cmsid, parse_junggu_dong_list 신규).
    중구는 이 서버 직접 가져오기가 끊겨 브라우저 경유로 채웠다(150개).
    목록 텍스트에 개별 글 cid가 노출되지 않아 원문 링크는 목록 URL이다.
    종로구·중랑구는 목록 URL 확인됐으나 라이브 소식 채우기가 대기 중이다
    (종로구: 통합 게시판 1개 + 담당부서 구분, bbsId BBSMSTR_000000000911;
    중랑구: 동별 우리동소식 B0000262, menuNo 규칙 확인).
    두 구 파서 초안은 work/*/parser_note.md에만 있고, 실측 HTML 검증 전에는
    fetch.py 동 수집 루프에 연결하지 않는다. 제외: 용산구·강서구(목록 URL 미확인).

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
  -> data.json (성동구, 기존과 동일), data_nationwide.json (성동 제외 21곳),
     data_dong.json (20개 구 343개 동)
"""
import html as html_lib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data.json"
OUT_NATIONWIDE = ROOT / "data_nationwide.json"
OUT_DONG = ROOT / "data_dong.json"
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

# ---------------------------------------------------------------------------
# 동 행정복지센터 '우리동 소식' (v0.6)
# ---------------------------------------------------------------------------
# 성동구 17개 동: 동별 서브사이트 + 동별 게시판(selectBbsNttList.do 계열).
#   2026-11-19 확인. 마장동만 pageUnit=8, 나머지는 10. 직접 가져오기는 끊긴다.
# 송파구 27개 동: 게시판 1개(bbsNo=36, key=2619) 공유, 동 이름 카테고리 필터.
#   2026-11-19 전수 확인. 서버 직접 가져오기 HTTP 200. 26개가 아니라 27개(위례동 포함).
#   동별 레지스트리는 sources_dong.yaml에도 기록돼 있다.
SEONGDONG_DONGS = [
    ("금호1가동", "geumho1ga", 277, 2570),
    ("금호2.3가동", "geumho23ga", 280, 2594),
    ("금호4가동", "geumho4ga", 283, 2618),
    ("마장동", "majang", 292, 2690),
    ("사근동", "sageun", 298, 2738),
    ("성수1가제1동", "seongsu1ga1", 301, 2762),
    ("성수1가제2동", "seongsu1ga2", 304, 2786),
    ("성수2가제1동", "seongsu2ga1", 307, 2810),
    ("성수2가제3동", "seongsu2ga3", 310, 2834),
    ("송정동", "songjeong", 313, 2858),
    ("옥수동", "oksu", 295, 2714),
    ("왕십리도선동", "wangsimnidoseon", 319, 2906),
    ("왕십리제2동", "wangsimni2", 316, 2882),
    ("용답동", "yongdap", 322, 2930),
    ("응봉동", "eungbong", 274, 2546),
    ("행당제1동", "haengdang1", 286, 2642),
    ("행당제2동", "haengdang2", 289, 2666),
]

SONGPA_DONGS = [
    "가락1동", "가락2동", "가락본동", "거여1동", "거여2동",
    "마천1동", "마천2동", "문정1동", "문정2동", "방이1동", "방이2동",
    "삼전동", "석촌동", "송파1동", "송파2동", "오금동", "오륜동",
    "위례동", "잠실2동", "잠실3동", "잠실4동", "잠실6동", "잠실7동",
    "잠실본동", "장지동", "풍납1동", "풍납2동",
]

# 노원구 19개 동: 구청 통합 게시판 '부서·동 소식'(q_bbsCode=1103).
#   2026-11-19 확인. 목록 URL 1개를 페이지 순회하며 담당부서로 동을 나눈다.
#   제목 앞 '[ 동명 ]' 태그만 믿으면 안 된다. 담당부서(목록) ≒ 상세 태그 > 제목 접두사.
#   동명 표기가 제각각이라(상계3.4동/상계3·4동/상계 3.4 동) 정규화해서 비교한다.
#   날짜는 목록에 비어 있는 경우가 많아 q_bbscttSn 앞 8자리(YYYYMMDD)에서 파생한다.
NOWON_DONGS = [
    "월계1동", "월계2동", "월계3동", "공릉1동", "공릉2동",
    "하계1동", "하계2동", "중계본동", "중계1동", "중계2·3동", "중계4동",
    "상계1동", "상계2동", "상계3·4동", "상계5동", "상계6·7동",
    "상계8동", "상계9동", "상계10동",
]
NOWON_LIST_URL = "https://www.nowon.kr/www/user/bbs/BD_selectBbsList.do?q_bbsCode=1103"

# 강남구 22개 동: 동별 센터 게시판(B_000282), 동 식별은 office 코드.
#   2026-11-19 확인. 목록 URL은 office-only 형태(list.do?office=...)로, 서버가
#   표준 URL(list.do?mid=MC...&office=...)로 302 리다이렉트한다. 서버 직접 가져오기 된다.
GANGNAM_DONGS = [
    ("신사동", "3220040"), ("논현1동", "3220041"), ("논현2동", "3220042"),
    ("삼성1동", "3220047"), ("삼성2동", "3220048"), ("대치1동", "3220049"),
    ("대치2동", "3220050"), ("대치4동", "3220052"), ("역삼1동", "3220053"),
    ("역삼2동", "3220054"), ("도곡1동", "3220055"), ("도곡2동", "3220056"),
    ("개포1동", "3220057"), ("개포2동", "3220058"), ("개포4동", "3220060"),
    ("세곡동", "3220061"), ("일원본동", "3220062"), ("일원1동", "3220063"),
    ("수서동", "3220065"), ("압구정동", "3220141"), ("청담동", "3220142"),
    ("개포3동", "3220272"),
]

# 관악구 21개 동: 게시판 1개(cbIdx=366, '우리동소식') 공유, deptCode로 동 구분.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. deptCode는 구청 메인 페이지의
#   동 선택 <option>에서 확인했고, 21개 동 목록을 전부 직접 가져와 페이지 제목으로 검증했다.
#   상세 URL은 목록 행의 onclick doBbsFView('366','<bcIdx>','16010100','<parentSeq>')에서 확인.
GWANAK_DONGS = [
    ("낙성대동", "D3200157"), ("난곡동", "D3200169"), ("난향동", "D3200163"),
    ("남현동", "D3200052"), ("대학동", "D3200168"), ("미성동", "D3200162"),
    ("보라매동", "D3200150"), ("삼성동", "D3200167"), ("서림동", "D3200166"),
    ("서원동", "D3200164"), ("성현동", "D3200152"), ("신림동", "D3200159"),
    ("신사동", "D3200160"), ("신원동", "D3200165"), ("은천동", "D3200151"),
    ("인헌동", "D3200158"), ("조원동", "D3200161"), ("중앙동", "D3200153"),
    ("청룡동", "D3200156"), ("청림동", "D3200154"), ("행운동", "D3200155"),
]

# 강동구 19개 동: 동별 서브사이트(/web/dongrenew/{slug}/main) 아래 '우리동소식'
#   섹션의 동별 '새소식' 게시판. 2026-11-19 확인. 서버 직접 가져오기 HTTP 200.
#   상세 URL은 목록 행의 <a class="art" href="/web/dongrenew/bbs{slug}/news_{slug}/{id}?...">를 그대로 쓴다.
GANGDONG_DONGS = [
    ("강일동", "gangil"), ("고덕1동", "godeog1"), ("고덕2동", "godeog2"),
    ("길동", "gil"), ("둔촌1동", "dunchon1"), ("둔촌2동", "dunchon2"),
    ("명일1동", "myeongil1"), ("명일2동", "myeongil2"),
    ("상일1동", "sangil"), ("상일2동", "sangil2"),
    ("성내1동", "seongnae1"), ("성내2동", "seongnae2"), ("성내3동", "seongnae3"),
    ("암사1동", "amsa1"), ("암사2동", "amsa2"), ("암사3동", "amsa3"),
    ("천호1동", "cheonho1"), ("천호2동", "cheonho2"), ("천호3동", "cheonho3"),
]

# 광진구 15개 동: 동별 서브사이트 + 동별 게시판 B0000127 '우리마을소식'.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. 목록은 <div class="bdList"> 구조.
#   1페이지는 고정글만 나오고 최신 일반글이 2페이지에 섞여 있어 1~3페이지를 합쳐
#   날짜 내림차순 상위 10개를 뽑는다. 고정글도 최신 실제 글이라 포함한다.
GWANGJIN_DONGS = [
    ("중곡1동", "01", "600009"), ("중곡2동", "02", "600209"), ("중곡3동", "03", "600309"),
    ("중곡4동", "04", "600409"), ("능동", "05", "600509"), ("구의1동", "06", "600609"),
    ("구의2동", "07", "600709"), ("구의3동", "08", "600809"), ("광장동", "09", "600909"),
    ("자양1동", "10", "601009"), ("자양2동", "11", "601109"), ("자양3동", "12", "601209"),
    ("자양4동", "13", "601309"), ("화양동", "14", "601409"), ("군자동", "15", "601509"),
]

# 동대문구 15개 동: 구청 공유 게시판 1개(bbsNo=72, key=390) + 동 이름 카테고리 필터.
#   송파구(bbsNo=36) 패턴과 동일해 parse_bbs_list를 재사용한다. 2026-11-19 확인.
#   서버 직접 가져오기 HTTP 200. 동 카테고리 15개는 목록 페이지의 '동 선택' 옵션에서 확인했다.
DONGDAEMUN_DONGS = [
    "신설동", "용두동", "제기동", "전농1동", "전농2동", "답십리1동", "답십리2동",
    "장안1동", "장안2동", "청량리동", "회기동", "휘경1동", "휘경2동", "이문1동", "이문2동",
]
DONGDAEMUN_BBS_NO = 72
DONGDAEMUN_KEY = 390

# 동작구 15개 동: 동별 서브사이트 + 동별 게시판 B0000301 '동네소식'.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. 목록은 <tr> 행
#   [번호|공지, 제목, 동, 날짜, 조회수], 상세 링크는 view.do?nttId=... 이다.
#   고정글(공지) 행도 최신 실제 글이라 포함하고 nttId로 중복을 제거한다.
#   게시판 글 수가 적어 1페이지에 10개가 안 차는 동이 있어 1~3페이지를 합친다.
#   동작동은 법정동이라 별도 동 페이지가 없다. 행정동 사당2동이 관할한다.
DONGJAK_DONGS = [
    ("노량진1동", "01", "800107"), ("노량진2동", "02", "800207"), ("상도1동", "03", "800307"),
    ("상도2동", "04", "800407"), ("상도3동", "05", "800507"), ("상도4동", "06", "800607"),
    ("흑석동", "07", "800707"), ("사당1동", "08", "800807"), ("사당2동", "09", "800907"),
    ("사당3동", "10", "801007"), ("사당4동", "11", "801107"), ("사당5동", "12", "801207"),
    ("대방동", "13", "801307"), ("신대방1동", "14", "801407"), ("신대방2동", "15", "801507"),
]

# 서대문구 14개 동: 동별 서브사이트 시민게시판 '우리동소식'.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. 단, 페이지는 EUC-KR이다.
#   meta에는 utf-8이 적혀 있어도 실제 바이트는 EUC-KR이라 fetch_html()을 그대로
#   쓰면 한글이 깨진다. _fetch_euckr()로 바이트를 받아 euc-kr로 직접 디코드한다.
#   제목 링크는 javascript:goView('{seq}') 형태라 상세 URL은
#   .../notice.do?mode=view&sdmBoardSeq={seq} 패턴으로 구성한다(충현동 seq 317274로 검증).
SEODAEMUN_DONGS = [
    ("충현동", "ch"), ("천연동", "cy"), ("북아현동", "bah"), ("신촌동", "sc"),
    ("연희동", "yh"), ("홍제1동", "hj1"), ("홍제2동", "hj2"), ("홍제3동", "hj3"),
    ("홍은1동", "he1"), ("홍은2동", "he2"), ("남가좌1동", "ngj1"), ("남가좌2동", "ngj2"),
    ("북가좌1동", "bgj1"), ("북가좌2동", "bgj2"),
]

# 성북구 20개 동: 구청 공유 게시판 1개(bbsNo=90, key=6171, '우리 동 소식') +
#   동 이름 카테고리(searchCtgry) 필터. 송파구 패턴과 동일해 parse_bbs_list를 재사용한다.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. 20개 동 연속 요청 시 0.5초 간격을 둔다.
SEONGBUK_DONGS = [
    "성북동", "삼선동", "동선동", "돈암1동", "돈암2동", "안암동", "보문동",
    "정릉1동", "정릉2동", "정릉3동", "정릉4동", "길음1동", "길음2동",
    "월곡1동", "월곡2동", "장위1동", "장위2동", "장위3동", "석관동", "종암동",
]
SEONGBUK_BBS_NO = 90
SEONGBUK_KEY = 6171

# 양천구 18개 동: 동별 서브사이트(/dong/<slug>/main.do) 안에 동별 게시판 '우리동소식'.
#   게시판 식별자 cbIdx가 동마다 다르다. 2026-11-19 확인. 서버 직접 가져오기 HTTP 200.
#   목록 1페이지에는 상단 고정글(동마다 0~4건)이 포함돼 일반글이 10건이 안 되므로
#   2페이지까지 본다. 고정글은 <tr class="notice"> 행이라 건너뛴다.
#   신정5동은 없다. 양천구 행정동은 18개이다.
YANGCHEON_DONGS = [
    ("목1동", "mok01", 423), ("목2동", "mok02", 431),
    ("목3동", "mok03", 438), ("목4동", "mok04", 445),
    ("목5동", "mok05", 452),
    ("신월1동", "sinwol01", 508), ("신월2동", "sinwol02", 515),
    ("신월3동", "sinwol03", 522), ("신월4동", "sinwol04", 529),
    ("신월5동", "sinwol05", 536), ("신월6동", "sinwol06", 543),
    ("신월7동", "sinwol07", 550),
    ("신정1동", "sinjeong01", 459), ("신정2동", "sinjeong02", 466),
    ("신정3동", "sinjeong03", 473), ("신정4동", "sinjeong04", 480),
    ("신정6동", "sinjeong06", 494), ("신정7동", "sinjeong07", 501),
]

# 은평구 16개 동: 구청 공유 게시판 1개(bbsNo=43, key=745, '동주민센터 공지사항') +
#   동 이름 카테고리(searchCtgry) 필터. 성북구·송파구와 같은 방식이라 parse_bbs_list를 재사용한다.
#   2026-11-19 확인. 서버 직접 가져오기가 되나 간헐적으로 타임아웃이 난다(16개 동 중 5개 동이
#   한 번씩 TimeoutError, 재시도하면 성공). 재시도 3회 + 요청 간 0.8초 간격을 둔다.
#   호스트는 반드시 ep.go.kr(www 없음)로 할 것. www.ep.go.kr로는 417이 난다.
EUNPYEONG_DONGS = [
    "녹번동", "불광1동", "불광2동", "갈현1동", "갈현2동", "구산동", "대조동",
    "응암1동", "응암2동", "응암3동", "역촌동", "신사1동", "신사2동",
    "증산동", "수색동", "진관동",
]
EUNPYEONG_BBS_NO = 43
EUNPYEONG_KEY = 745

# 서초구 18개 동: 동별 공지사항은 구 공지 게시판(cbIdx=57)을 dongCode로 필터한 DongList.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. 서초1동만 별도 '1동 소식'
#   게시판(cbIdx=442)이 있으나 다른 17개 동에는 없어 균일하게 DongList를 쓴다.
#   상세 URL은 목록 href의 소문자 bcidx를 DongMain 검증 형태
#   DongView.do?cbIdx=57&bcIdx={id}&dongCode={code}로 구성한다(bcIdx 412276 검증).
#   낡은 동: 반포본동 최신 2026-08-25, 잠원동 2026-09-03, 내곡동 2026-09-23.
SEOCHO_DONGS = [
    ("서초1동", "v0"), ("서초2동", "v1"), ("서초3동", "v2"), ("서초4동", "v3"),
    ("잠원동", "v4"), ("반포본동", "v5"), ("반포1동", "v6"), ("반포2동", "v7"),
    ("반포3동", "v8"), ("반포4동", "v9"), ("방배본동", "va"), ("방배1동", "vb"),
    ("방배2동", "vc"), ("방배3동", "vd"), ("방배4동", "ve"), ("양재1동", "vf"),
    ("양재2동", "vg"), ("내곡동", "vh"),
]

# 영등포구 18개 동: 동마다 bbsNo·key가 다른 동별 '우리동 소식' 게시판.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. parse_bbs_list를 재사용한다.
#   bbsNo=60 공유 게시판은 별개 게시판이라 쓰지 않는다. 18개 동 최신이 모두 2026-10-15~11-19.
YEONGDEUNGPO_DONGS = [
    ("영등포본동", 56, 4914), ("영등포동", 61, 2966),
    ("여의동", 66, 2983), ("당산1동", 71, 3000),
    ("당산2동", 76, 3017), ("도림동", 81, 3034),
    ("문래동", 86, 3051), ("양평1동", 91, 3068),
    ("양평2동", 96, 3085), ("신길1동", 101, 3102),
    ("신길3동", 106, 3119), ("신길4동", 111, 3136),
    ("신길5동", 116, 3153), ("신길6동", 121, 3170),
    ("신길7동", 126, 3187), ("대림1동", 131, 3204),
    ("대림2동", 136, 3221), ("대림3동", 141, 3238),
]

# 마포구 16개 동: 동별 서브사이트(/site/{slug}/home) 아래 '우리동네소식' 게시판.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. 염리동 슬러그는 yeomni이다
#   (yeomri는 구청 대표사이트로 리다이렉트된다). 상세 URL은 bare 형태
#   /site/{slug}/board/townnews/{id}로 쓴다(공덕동 3265번 검증).
#   낡은 동: 연남동 최신 2026-08-28.
MAPO_DONGS = [
    ("공덕동", "gongdeok"), ("아현동", "ahyeon"), ("도화동", "dohwa"),
    ("용강동", "yonggang"), ("대흥동", "daeheung"), ("염리동", "yeomni"),
    ("신수동", "sinsu"), ("서강동", "seogang"), ("서교동", "seogyo"),
    ("합정동", "hapjeong"), ("망원1동", "mangwon1"), ("망원2동", "mangwon2"),
    ("연남동", "yeonnam"), ("성산1동", "seongsan1"), ("성산2동", "seongsan2"),
    ("상암동", "sangam"),
]

# 도봉구 14개 동: 동별 bbs.asp?code={code} '동 소식 공지사항' 게시판.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. 상세 URL은
#   bbs.asp?bmode=D&pcode={pcode}&code={code}이다. 방학1동 RSS(code=10009682)는
#   data_nationwide.json의 구청급 게시판과 별개이다.
DOBONG_DONGS = [
    ("쌍문1동", "10009626"),
    ("쌍문2동", "10009640"),
    ("쌍문3동", "10009654"),
    ("쌍문4동", "10009668"),
    ("방학1동", "10009682"),
    ("방학2동", "10009696"),
    ("방학3동", "10009710"),
    ("창1동", "10009724"),
    ("창2동", "10009738"),
    ("창3동", "10009752"),
    ("창4동", "10009766"),
    ("창5동", "10009780"),
    ("도봉1동", "10009794"),
    ("도봉2동", "10009808"),
]

# 강북구 13개 동: 동별 게시판 B0000199 '우리동소식', menuNo·dongCd로 동 구분.
#   2026-11-19 확인. 목록 URL은 동 메인 페이지의 '우리동소식' 앵커에서 확인했다.
#   curl로는 gangbuk.go.kr:18000 직접 가져오기 HTTP 200이나, 이 서버 urllib로는
#   프록시에서 :18000이 막혀 실패할 수 있다. 실패 시 기존 소식을 유지한다.
#   낡은 동: 수유1동 최신 2026-11-03.
GANGBUK_DONGS = [
    ("삼양동", "01", "600042"),
    ("미아동", "02", "600016"),
    ("송중동", "03", "600040"),
    ("송천동", "04", "600060"),
    ("삼각산동", "05", "600092"),
    ("번1동", "06", "600109"),
    ("번2동", "07", "600126"),
    ("번3동", "08", "600143"),
    ("수유1동", "09", "600160"),
    ("수유2동", "10", "600177"),
    ("수유3동", "11", "600194"),
    ("우이동", "12", "600211"),
    ("인수동", "13", "600228"),
]

# 구로구 16개 동: 구청 공유 게시판 1개(bbsNo=794, '우리동 소식') + 동 이름 카테고리 필터.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. parse_bbs_list를 재사용한다.
#   동별 key는 동 서브페이지의 '우리동 소식' 메뉴 링크에서 확인했다.
#   구로구는 15개가 아니라 16개 동이다(신도림동 포함, 천왕동은 법정동).
#   낡은 동: 가리봉동 최신 2026-05-04, 신도림동·수궁동·항동 2026-09-23~30.
GURO_BBS_NO = 794

# (동명, board key, 서브페이지 key, 동 코드)
GURO_DONGS = [
    ("신도림동", 3049, 1942, "D3160041"),
    ("구로1동", 1955, 1951, "D3160042"),
    ("구로2동", 1964, 1960, "D3160043"),
    ("구로3동", 1973, 1969, "D3160044"),
    ("구로4동", 1983, 1978, "D3160045"),
    ("구로5동", 1992, 1987, "D3160046"),
    ("가리봉동", 2001, 1996, "D3160144"),
    ("고척1동", 2010, 2005, "D3160051"),
    ("고척2동", 2019, 2014, "D3160052"),
    ("개봉1동", 2028, 2023, "D3160053"),
    ("개봉2동", 2037, 2032, "D3160054"),
    ("개봉3동", 2046, 2041, "D3160055"),
    ("오류1동", 2055, 2050, "D3160057"),
    ("오류2동", 2064, 2059, "D3160058"),
    ("수궁동", 2073, 2068, "D3160059"),
    ("항동", 2082, 2077, "D3160252"),
]

# 금천구 10개 동: 구청 공유 게시판 1개(bbsNo=4) + 동 주민센터 부서코드(searchDeptCode) 필터.
#   2026-11-19 확인. 서버 직접 가져오기 HTTP 200. parse_bbs_list를 재사용한다.
#   동별 key·부서코드는 동 소개 페이지의 '공지사항' 탭 링크에서 확인했다.
#   보조 게시판 '골목회의'(bbsNo=150128)는 일부 동에서만 확인돼 이번 단계에서는 수집하지 않는다.
#   낡은 동: 시흥5동 최신 2026-10-08.
GEUMCHEON_BBS_NO = 4

# (동명, 소개 페이지 contents key, 공지사항 탭 key, 부서코드, 골목회의 key|None)
GEUMCHEON_DONGS = [
    ("가산동", 651, 653, "31700420000", 2222),
    ("독산1동", 661, 663, "31700430000", 2223),
    ("독산2동", 669, 671, "31700440000", 2224),
    ("독산3동", 677, 679, "31700450000", 2225),
    ("독산4동", 685, 687, "31700460000", 2226),
    ("시흥1동", 693, 695, "31700490000", 2227),
    ("시흥2동", 701, 703, "31700500000", None),
    ("시흥3동", 709, 711, "31700510000", None),
    ("시흥4동", 717, 719, "31700520000", None),
    ("시흥5동", 726, 728, "31700530000", 2231),
]

# 중구 15개 동: 동별 CMS 게시판(content.do?cmsid, '우리동 소식').
#   2026-11-20 확인. cmsid 13300(소공동)~13331(중림동) 연속.
#   이 서버 직접 가져오기는 차단(RemoteDisconnected)이라 브라우저 경유로 채웠다.
#   목록 텍스트에 개별 글 cid가 노출되지 않아 원문 링크는 목록 URL(url_kind=list).
#   상세 URL 패턴 content.do?cmsid=<id>&mode=view&cid=<9~10자리>는 실링크로 확인됐으나
#   cid 추출 정규식은 실측 HTML 미검증이라, 매칭될 때만 상세 URL을 쓰고 아니면 목록 URL이다.
#   회현동·광희동은 게시판 번호가 재구성됐을 가능성이 있어 번호가 아닌 cid(또는 제목+날짜)로 중복 판정한다.
# (동명, slug, cmsid)
JUNGGU_DONGS = [
    ("소공동", "sogong", "13300"),
    ("회현동", "hoehyeon", "13318"),
    ("명동", "myeong", "13319"),
    ("필동", "pil", "13320"),
    ("장충동", "jangchung", "13321"),
    ("광희동", "gwanghui", "13322"),
    ("을지로동", "euljiro", "13323"),
    ("신당동", "sindang", "13324"),
    ("다산동", "dasan", "13325"),
    ("약수동", "yaksoo", "13326"),
    ("청구동", "cheonggu", "13327"),
    ("신당제5동", "sindang5", "13328"),
    ("동화동", "donghwa", "13329"),
    ("황학동", "hwanghak", "13330"),
    ("중림동", "jungnim", "13331"),
]


def dong_sources():
    srcs = []
    for dong, slug, bbs, key in SEONGDONG_DONGS:
        srcs.append({
            "gu": "서울 성동구", "dong": dong, "slug": slug,
            "region": f"서울 성동구 {dong}", "board": "우리동 소식",
            "kind": "bbs", "bbs_no": bbs, "key": key,
            "list_url": f"https://www.sd.go.kr/{slug}/selectBbsNttList.do?bbsNo={bbs}&key={key}",
            "timeout": 10,
        })
    for dong in SONGPA_DONGS:
        srcs.append({
            "gu": "서울 송파구", "dong": dong,
            "region": f"서울 송파구 {dong}", "board": "송파구 동 소식",
            "kind": "bbs", "bbs_no": 36,
            "list_url": ("https://www.songpa.go.kr/www/selectBbsNttList.do?bbsNo=36&key=2619"
                         f"&searchCtgry={urllib.parse.quote(dong)}"),
            "timeout": 25, "sleep_before": 0.5,
        })
    for dong, office in GANGNAM_DONGS:
        srcs.append({
            "gu": "서울 강남구", "dong": dong, "office": office,
            "region": f"서울 강남구 {dong}", "board": "우리동이야기 새소식",
            "kind": "gangnam",
            "list_url": ("https://www.gangnam.go.kr/center/board/B_000282/list.do"
                         f"?office={office}"),
            "timeout": 25,
        })
    for dong, dept_code in GWANAK_DONGS:
        srcs.append({
            "gu": "서울 관악구", "dong": dong, "dept_code": dept_code,
            "region": f"서울 관악구 {dong}", "board": "우리동소식",
            "kind": "gwanak",
            "list_url": ("https://www.gwanak.go.kr/site/gwanak/ex/bbs/List.do"
                         f"?cbIdx=366&deptCode={dept_code}"),
            "timeout": 25,
        })
    for dong, slug in GANGDONG_DONGS:
        srcs.append({
            "gu": "서울 강동구", "dong": dong, "slug": slug,
            "region": f"서울 강동구 {dong}", "board": "새소식",
            "kind": "gangdong",
            "list_url": (f"https://www.gangdong.go.kr/web/dongrenew/bbs{slug}"
                         f"/news_{slug}"),
            "timeout": 25,
        })
    for dong in DONGDAEMUN_DONGS:
        srcs.append({
            "gu": "서울 동대문구", "dong": dong,
            "region": f"서울 동대문구 {dong}", "board": "동주민센터 공지사항",
            "kind": "bbs", "bbs_no": DONGDAEMUN_BBS_NO, "key": DONGDAEMUN_KEY,
            "list_url": ("https://www.ddm.go.kr/www/selectBbsNttList.do?bbsNo=72&key=390"
                         f"&searchCtgry={urllib.parse.quote(dong)}"),
            "timeout": 25, "sleep_before": 0.5,
        })
    for dong in SEONGBUK_DONGS:
        srcs.append({
            "gu": "서울 성북구", "dong": dong,
            "region": f"서울 성북구 {dong}", "board": "우리 동 소식",
            "kind": "bbs", "bbs_no": SEONGBUK_BBS_NO, "key": SEONGBUK_KEY,
            "list_url": ("https://sb.go.kr/www/selectBbsNttList.do?key=6171&bbsNo=90"
                         f"&searchCtgry={urllib.parse.quote(dong)}"),
            "timeout": 25, "sleep_before": 0.5,
        })
    for dong in EUNPYEONG_DONGS:
        srcs.append({
            "gu": "서울 은평구", "dong": dong,
            "region": f"서울 은평구 {dong}", "board": "동주민센터 공지사항",
            "kind": "bbs", "bbs_no": EUNPYEONG_BBS_NO, "key": EUNPYEONG_KEY,
            # 호스트 주의: www 없음(ep.go.kr). www.ep.go.kr은 417.
            "list_url": ("https://ep.go.kr/www/selectBbsNttList.do?key=745&bbsNo=43"
                         f"&searchCtgry={urllib.parse.quote(dong)}"),
            "timeout": 60, "sleep_before": 0.8, "retries": 3,
        })
    for dong, bbs_no, key in YEONGDEUNGPO_DONGS:
        srcs.append({
            "gu": "서울 영등포구", "dong": dong,
            "region": f"서울 영등포구 {dong}", "board": "우리동소식",
            "kind": "bbs", "bbs_no": bbs_no, "key": key,
            "list_url": ("https://www.ydp.go.kr/www/selectBbsNttList.do"
                         f"?bbsNo={bbs_no}&key={key}"),
            "timeout": 25, "sleep_before": 0.5,
        })
    for dong, key, sub_key, dong_code in GURO_DONGS:
        srcs.append({
            "gu": "서울 구로구", "dong": dong, "dong_cd": dong_code,
            "sub_key": sub_key,
            "region": f"서울 구로구 {dong}", "board": "우리동 소식",
            "kind": "bbs", "bbs_no": GURO_BBS_NO, "key": key,
            "list_url": ("https://www.guro.go.kr/www/selectBbsNttList.do?bbsNo=794"
                         f"&key={key}&searchCtgry={urllib.parse.quote(dong)}"),
            "timeout": 25, "sleep_before": 0.5,
        })
    for dong, contents_key, key, dept_code, _golmok_key in GEUMCHEON_DONGS:
        srcs.append({
            "gu": "서울 금천구", "dong": dong,
            "region": f"서울 금천구 {dong}", "board": "공지사항",
            "kind": "bbs", "bbs_no": GEUMCHEON_BBS_NO, "key": key,
            "dept_code": dept_code, "contents_key": contents_key,
            "list_url": ("https://www.geumcheon.go.kr/portal/selectBbsNttList.do"
                         f"?bbsNo=4&key={key}&searchDeptCode={dept_code}"),
            "timeout": 25, "sleep_before": 0.5,
        })
    for dong, slug, cmsid in JUNGGU_DONGS:
        srcs.append({
            "gu": "서울 중구", "dong": dong, "slug": slug, "cmsid": cmsid,
            "region": f"서울 중구 {dong}", "board": "우리동 소식",
            "kind": "junggu",
            "list_url": (f"https://www.junggu.seoul.kr/dong/{slug}/content.do"
                         f"?cmsid={cmsid}"),
            "timeout": 25,
        })
    return srcs


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


_DATE_FULL = re.compile(r"^(\d{4})[-./](\d{1,2})[-./](\d{1,2})(\([^)]*\))?$")
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
    """행에서 날짜를 찾아 YYYY-MM-DD로. 셀 전체가 날짜 형식인 셀만 작성일로 취한다.
    제목 안에 날짜가 들어 있어도(예: '현장구청장실(2026.10.13)...') 작성일로 오인하지 않는다.
    셀 목록이 없으면(대전 동구 <li>형) 제목 링크를 뺀 나머지 텍스트에서 날짜를 찾는다."""
    if cells:
        for c in cells:
            d = _norm_date_cell(_strip_tags(c))
            if d:
                return d
        return ""
    t = _strip_tags(re.sub(r"<a[^>]*>.*?</a>", " ", row_html, flags=re.S | re.I))
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


def parse_gangnam(html_text: str, src: dict):
    """강남구 동별 센터 게시판(B_000282). 제목 <a>의 href에 게시글 id가 있다.
    목록 1페이지에 최신 10개가 있다. 작성일은 행의 날짜 셀에서 읽는다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(r'<a[^>]*href="(/center/board/B_000282/(\d+)/view\.do\?[^"]*)"[^>]*>(.*?)</a>',
                      row, re.S | re.I)
        if not m:
            continue
        href, num, atitle = m.group(1), m.group(2), m.group(3)
        if num in seen:
            continue
        seen.add(num)
        title = _clean_title(atitle)
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = urllib.parse.urljoin(src["list_url"], html_lib.unescape(href))
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices[:10]


def parse_junggu_dong_list(html_text: str, src: dict):
    """중구 동별 CMS 게시판(content.do?cmsid, '우리동 소식').
    목록 1페이지에 최신 10개가 있다. 담당부서 셀은 동 이름 자체라 동별 필터가 필요 없다.
    상세 URL 패턴(content.do?cmsid=<id>&mode=view&cid=<cid>)은 실링크로 확인됐으나,
    cid 추출 정규식은 실측 HTML 미검증이다. cid를 읽지 못하면 목록 URL로 기록한다
    (url_kind="list" — 성동구 방식). 회현동·광희동은 게시판 번호가 재구성됐을
    가능성이 있어 번호가 아닌 cid(또는 제목+날짜)로 중복 판정한다."""
    notices, seen = [], set()
    cmsid = str(src["cmsid"])
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(
            r'<a[^>]*href="[^"]*content\.do\?cmsid=' + re.escape(cmsid) +
            r'(?:&amp;|&)mode=view(?:&amp;|&)cid=(\d+)[^"]*"[^>]*>(.*?)</a>',
            row, re.S | re.I)
        title = ""
        url = src["list_url"]
        url_kind = "list"
        if m:
            cid, atitle = m.group(1), m.group(2)
            if cid in seen:
                continue
            seen.add(cid)
            title = _clean_title(atitle)
            url = (f"https://www.junggu.seoul.kr/dong/{src['slug']}/content.do"
                   f"?cmsid={cmsid}&mode=view&cid={cid}")
            url_kind = "detail"
        else:
            # href에 cid가 없으면 제목 셀 텍스트만으로 기록한다.
            cells = _td_cells(row)
            if len(cells) < 2:
                continue
            title = _clean_title(cells[1])
            key = (title, _extract_date(row, cells))
            if key in seen:
                continue
            seen.add(key)
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        item = _notice(src["region"], src["board"], title, date, url)
        item["url_kind"] = url_kind
        notices.append(item)
    return notices[:10]


def parse_gwanak(html_text: str, src: dict):
    """관악구 우리동소식(cbIdx=366). 제목 링크는 onclick doBbsFView(...)이다.
    목록 1페이지에 최신 10개가 있다. 작성일은 행의 날짜 셀(YYYY.MM.DD)에서 읽는다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(
            r"doBbsFView\('(\d+)','(\d+)','16010100','(\d+)'\)", row)
        if not m:
            continue
        cb_idx, bc_idx, parent_seq = m.group(1), m.group(2), m.group(3)
        if bc_idx in seen:
            continue
        seen.add(bc_idx)
        am = re.search(r"<a[^>]*doBbsFView[^>]*>(.*?)</a>", row, re.S)
        title = _clean_title(am.group(1)) if am else ""
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = ("https://www.gwanak.go.kr/site/gwanak/ex/bbs/View.do"
               f"?cbIdx=366&bcIdx={bc_idx}&deptCode={src['dept_code']}"
               f"&parentSeq={parent_seq}")
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices[:10]


def parse_gangdong(html_text: str, src: dict):
    """강동구 동별 새소식 게시판. 제목 <a class="art">의 href에 게시글 id가 있다.
    목록 1페이지에 최신 10개가 있다(상일2동은 15개 반환 — 상위 10개만 쓴다).
    번호 셀이 숫자가 아닌 행(상단 고정 공지)은 건너뛴다. 작성일은 행의 날짜 셀에서 읽는다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        cells = _td_cells(row)
        # 번호 셀이 숫자가 아니면 상단 고정 공지 행이라 건너뛴다.
        if not cells or not _strip_tags(cells[0]).isdigit():
            continue
        m = re.search(
            r'<a[^>]*class="art"[^>]*href="(/web/dongrenew/bbs[^"]*/news_[^"]*/(\d+)\?[^"]*)"[^>]*>(.*?)</a>',
            row, re.S | re.I)
        if not m:
            continue
        href, num, atitle = m.group(1), m.group(2), m.group(3)
        if num in seen:
            continue
        seen.add(num)
        title = _clean_title(atitle)
        if not title:
            continue
        date = _extract_date(row, cells)
        url = urllib.parse.urljoin(src["list_url"], html_lib.unescape(href))
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices[:10]


def parse_gwangjin_list(html_text: str, src: dict):
    """광진구 우리마을소식 1페이지. {nttId: (title, date, url)}를 돌려준다.
    목록은 <div class="bdList"> 구조라 기존 <tr> 파서는 안 맞는다.
    날짜 <span class="date">는 첨부파일 블록 뒤에 있어, 다음 항목 앵커까지를
    구간으로 잡아 그 안에서 찾는다."""
    items = {}
    anchors = list(re.finditer(
        r'href="(/dong/bbs/B0000127/view\.do\?nttId=(\d+)&menuNo=\d+&dongCd=\d+&pageIndex=\d+)"[^>]*>\s*<span class="tit">(.*?)</span>',
        html_text, re.S))
    for i, a in enumerate(anchors):
        ntt, title = a.group(2), _clean_title(a.group(3))
        if not title or ntt in items:
            continue
        seg = html_text[a.end():anchors[i + 1].start() if i + 1 < len(anchors) else len(html_text)]
        d = re.search(r'<span class="date">\s*(\d{4}-\d{2}-\d{2})\s*</span>', seg)
        date = d.group(1) if d else ""
        url = urllib.parse.urljoin(src["list_url"], html_lib.unescape(a.group(1)))
        items[ntt] = (title, date, url)
    return items


def fetch_gwangjin(max_pages: int = 3):
    """광진구 15개 동을 돌아 {dong: [notices]}와 상태를 돌려준다.
    1페이지는 고정글만 나오고 최신 일반글이 2페이지에 섞여 있어 1~3페이지를
    합쳐 날짜 내림차순 상위 10개를 뽑는다. 고정글도 최신 실제 글이라 포함한다.
    날짜가 안 보이는 항목은 상세 페이지를 직접 확인한다(드물다)."""
    base = "https://www.gwangjin.go.kr"
    per_dong, status = {}, "ok"
    for dong, cd, menu in GWANGJIN_DONGS:
        list_url = f"{base}/dong/bbs/B0000127/list.do?menuNo={menu}&dongCd={cd}"
        src = {"region": f"서울 광진구 {dong}", "board": "우리마을소식", "list_url": list_url}
        merged = {}
        for page in range(1, max_pages + 1):
            html_text, st = fetch_html(f"{list_url}&pageIndex={page}", timeout=25)
            if html_text is None:
                status = st
                continue
            for ntt, (title, date, url) in parse_gwangjin_list(html_text, src).items():
                if ntt not in merged:
                    merged[ntt] = (title, date, url)
            time.sleep(0.3)
            if len(merged) >= 10 and page >= 2:
                break
        notices = []
        for title, date, url in sorted(merged.values(), key=lambda x: x[1], reverse=True)[:10]:
            if not date:
                # 날짜가 목록에 없으면 상세 페이지에서 확인한다.
                try:
                    vt, _ = fetch_html(url, timeout=25)
                    d = re.search(r'<span class="date">\s*(\d{4}-\d{2}-\d{2})\s*</span>', vt or "")
                    date = d.group(1) if d else ""
                except Exception:
                    pass
            notices.append({"title": title, "category": classify(title), "date": date,
                            "region": f"서울 광진구 {dong}", "source": "우리마을소식",
                            "url": url, "gu": "서울 광진구", "dong": dong, "url_kind": "detail"})
        per_dong[dong] = notices
        print(f"  서울 광진구 {dong}: ok notices={len(notices)}")
    return per_dong, status


def parse_dongjak_list(html_text: str, src: dict):
    """동작구 동네소식 1페이지. 고정글(공지) 행도 최신 실제 글이라 포함한다.
    nttId로 중복을 제거한다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        m = re.search(
            r'href="(/dong/bbs/B0000301/view\.do\?nttId=(\d+)&menuNo=\d+&dongCd=\d+&pageIndex=\d+)"',
            row)
        if not m or m.group(2) in seen:
            continue
        seen.add(m.group(2))
        cells = _td_cells(row)
        txt = [_strip_tags(c) for c in cells]
        if len(txt) < 4:
            continue
        title = txt[1]
        if not title:
            continue
        date = txt[3] if re.match(r"\d{4}-\d{2}-\d{2}", txt[3]) else ""
        url = urllib.parse.urljoin(src["list_url"], html_lib.unescape(m.group(1)))
        notices.append({"title": title, "category": classify(title), "date": date,
                        "region": src["region"], "source": src["board"], "url": url,
                        "gu": src["gu"], "dong": src["dong"], "url_kind": "detail"})
    return notices


def fetch_dongjak(max_pages: int = 3):
    """동작구 15개 동을 돌아 {dong: [notices]}와 상태를 돌려준다.
    1페이지에 10개가 안 차는 동이 있어 페이지 순회하며 nttId 중복을 제거하고
    날짜 내림차순 상위 10개를 뽑는다."""
    base = "https://www.dongjak.go.kr"
    per_dong, status = {}, "ok"
    for dong, cd, menu in DONGJAK_DONGS:
        list_url = f"{base}/dong/bbs/B0000301/list.do?menuNo={menu}&dongCd={cd}"
        src = {"gu": "서울 동작구", "dong": dong, "region": f"서울 동작구 {dong}",
               "board": "동네소식", "list_url": list_url}
        merged, seen = {}, set()
        for page in range(1, max_pages + 1):
            html_text, st = fetch_html(f"{list_url}&pageIndex={page}", timeout=25)
            if html_text is None:
                status = st
                continue
            for n in parse_dongjak_list(html_text, src):
                key = re.search(r"nttId=(\d+)", n["url"])
                key = key.group(1) if key else n["url"]
                if key not in seen:
                    seen.add(key)
                    merged[key] = n
            time.sleep(0.3)
            if len(merged) >= 10:
                break
        lst = sorted(merged.values(), key=lambda n: n.get("date", ""), reverse=True)[:10]
        per_dong[dong] = lst
        print(f"  서울 동작구 {dong}: ok notices={len(lst)}")
    return per_dong, status


def _fetch_euckr(url: str, timeout: int = 25):
    """서대문구 동 페이지는 EUC-KR이다. 바이트를 받아 euc-kr로 직접 디코드한다.
    meta에는 utf-8이 적혀 있어도 실제 바이트는 EUC-KR이라 fetch_html()을 그대로
    쓰면 한글이 깨진다. 실패하면 (None, 상태문자열)을 돌려준다."""
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
    except Exception as e:
        return None, f"fetch_failed:{type(e).__name__}"
    return raw.decode("euc-kr", errors="replace"), "ok"


def parse_seodaemun_list(html_text: str, slug: str, dong: str):
    """서대문구 우리동소식 1페이지. 제목이 '...'으로 잘린 항목은
    ('_truncated': True)로 표시해 호출자가 상세 페이지에서 채우게 한다."""
    base = "https://www.sdm.go.kr"
    list_url = f"{base}/dong/{slug}/citizen/notice.do"
    items = []
    for row in _tr_rows(html_text):
        vm = re.search(r"goView\('(\d+)'\)", row)
        if not vm:
            continue
        seq = vm.group(1)
        cells = _td_cells(row)
        txt = [_strip_tags(c) for c in cells]
        if len(txt) < 4:
            continue
        title = txt[1]
        date = ""
        dm = re.search(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", txt[3])
        if dm:
            date = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}"
        view_url = f"{list_url}?mode=view&sdmBoardSeq={seq}"
        items.append({"title": title, "category": classify(title), "date": date,
                      "region": f"서울 서대문구 {dong}", "source": "우리동소식",
                      "url": view_url, "gu": "서울 서대문구", "dong": dong,
                      "url_kind": "detail", "_seq": seq,
                      "_truncated": title.endswith("...") or title.endswith("…")})
    return items


def fetch_seodaemun():
    """서대문구 14개 동을 돌아 {dong: [notices]}와 상태를 돌려준다.
    목록 제목이 잘린 글은 상세 페이지를 직접 가져와 전체 제목으로 바꾼다."""
    per_dong, status = {}, "ok"
    for dong, slug in SEODAEMUN_DONGS:
        list_url = f"https://www.sdm.go.kr/dong/{slug}/citizen/notice.do"
        html_text, st = _fetch_euckr(list_url, timeout=25)
        if html_text is None:
            status = st
            per_dong[dong] = []
            print(f"  서울 서대문구 {dong}: {st} notices=0")
            continue
        items = parse_seodaemun_list(html_text, slug, dong)
        for n in items:
            if n.pop("_truncated", False):
                vt, vst = _fetch_euckr(n["url"], timeout=25)
                if vt is not None:
                    fm = re.search(r"<th[^>]*>제목</th>\s*<td[^>]*>(.*?)</td>", vt, re.S)
                    if fm:
                        n["title"] = _strip_tags(fm.group(1))
                        n["category"] = classify(n["title"])
                time.sleep(0.3)
            n.pop("_seq", None)
        items.sort(key=lambda n: n.get("date", ""), reverse=True)
        per_dong[dong] = items[:10]
        print(f"  서울 서대문구 {dong}: ok notices={len(per_dong[dong])}")
        time.sleep(0.3)
    return per_dong, status


def parse_yangcheon(html_text: str, src: dict):
    """양천구 동별 '우리동소식' 목록 1페이지.
    고정글(<tr class="notice">)은 건너뛴다. 제목은 wdigm_title('...') 안에 있고,
    상세 식별자는 onclick doBbsFView('cbIdx','bcIdx',...)에서 읽는다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if re.search(r'class="notice"', row) or "post-notice" in row:
            continue
        m = re.search(r"doBbsFView\('(\d+)','(\d+)'", row)
        if not m:
            continue
        cb_idx, bc_idx = m.group(1), m.group(2)
        if bc_idx in seen:
            continue
        seen.add(bc_idx)
        tm = re.search(r"wdigm_title\('((?:[^'\\]|\\.)*)'\)", row)
        if not tm:
            continue
        title = _clean_title(tm.group(1).replace("\\'", "'")
                                     .replace('\\"', '"')
                                     .replace("\\\\", "\\"))
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = (f"https://www.yangcheon.go.kr/site/{src['slug']}/ex/bbs/View.do"
               f"?cbIdx={cb_idx}&bcIdx={bc_idx}&parentSeq={bc_idx}")
        notices.append(_notice(src["region"], src["board"], title, date, url))
    return notices


def fetch_yangcheon(max_pages: int = 2):
    """양천구 18개 동을 돈다. {dong: [notices]}와 상태를 돌려준다.
    cbIdx는 레지스트리(registry-yangcheon.yaml)에 이미 기록된 값을 쓴다.
    목록 1페이지에 고정글이 섞여 일반글이 10건이 안 되므로 2페이지까지 본다."""
    per_dong = {}
    status = "ok"
    for dong, slug, cb_idx in YANGCHEON_DONGS:
        list_url = (f"https://www.yangcheon.go.kr/site/{slug}/ex/bbs/List.do"
                    f"?cbIdx={cb_idx}")
        src = {"gu": "서울 양천구", "dong": dong, "slug": slug,
               "region": f"서울 양천구 {dong}", "board": "우리동소식",
               "list_url": list_url}
        collected, seen_urls = [], set()
        for page in range(1, max_pages + 1):
            html_text, st = fetch_html(f"{list_url}&pageIndex={page}", timeout=25)
            if html_text is None:
                status = st
                break
            for n in parse_yangcheon(html_text, src):
                if n["url"] in seen_urls:
                    continue
                seen_urls.add(n["url"])
                collected.append(n)
            if len(collected) >= 10:
                break
            time.sleep(0.5)
        collected.sort(key=lambda n: n.get("date", ""), reverse=True)
        per_dong[dong] = collected[:10]
        print(f"  서울 양천구 {dong}: {status} notices={len(per_dong[dong])}")
    return per_dong, status

def parse_seocho(html_text: str, gu: str, dong: str, code: str):
    """서초구 동별 공지사항(DongList) 1페이지."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(r"DongView\.do\?cbIdx=57&(?:amp;)?bcidx=(\d+)", row, re.I)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        am = re.search(r"<a[^>]*DongView[^>]*>(.*?)</a>", row, re.S | re.I)
        title = _clean_title(am.group(1)) if am else ""
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = (f"https://www.seocho.go.kr/site/seocho/ex/bbs/DongView.do"
               f"?cbIdx=57&bcIdx={m.group(1)}&dongCode={code}")
        notices.append({"title": title, "category": classify(title), "date": date,
                        "region": f"{gu} {dong}", "source": "공지사항",
                        "url": url, "gu": gu, "dong": dong, "url_kind": "detail"})
    notices.sort(key=lambda n: n.get("date", ""), reverse=True)
    return notices[:10]


def fetch_seocho():
    """서초구 18개 동을 돌아 {dong: [notices]}와 상태를 돌려준다.
    목록 1페이지에 최신 10개가 있다. 실패한 동은 빈 리스트를 돌려주고
    호출자(main)가 기존 소식을 유지한다."""
    per_dong, status = {}, "ok"
    for dong, code in SEOCHO_DONGS:
        list_url = ("https://www.seocho.go.kr/site/seocho/ex/bbs/DongList.do"
                    f"?cbIdx=57&dongCode={code}")
        html_text, st = fetch_html(list_url, timeout=25)
        if html_text is None:
            status = st
            per_dong[dong] = []
            print(f"  서울 서초구 {dong}: {st} notices=0")
            continue
        per_dong[dong] = parse_seocho(html_text, "서울 서초구", dong, code)
        print(f"  서울 서초구 {dong}: ok notices={len(per_dong[dong])}")
        time.sleep(0.4)
    return per_dong, status


def parse_mapo_dong(html_text: str, gu: str, dong: str, slug: str):
    """마포구 우리동네소식 1페이지. 제목 <a>의 townnews/{id}를 상세 식별자로 쓴다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(rf"/site/{re.escape(slug)}/board/townnews/(\d+)", row)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        am = re.search(r"<a[^>]*townnews/\d+[^>]*>(.*?)</a>", row, re.S)
        title = _clean_title(am.group(1)) if am else ""
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = f"https://www.mapo.go.kr/site/{slug}/board/townnews/{m.group(1)}"
        notices.append({"title": title, "category": classify(title), "date": date,
                        "region": f"{gu} {dong}", "source": "우리동네소식",
                        "url": url, "gu": gu, "dong": dong, "url_kind": "detail"})
    notices.sort(key=lambda n: n.get("date", ""), reverse=True)
    return notices[:10]


def fetch_mapo_dong():
    """마포구 16개 동을 돌아 {dong: [notices]}와 상태를 돌려준다.
    목록 1페이지에 최신 10개가 있다. 실패한 동은 빈 리스트를 돌려주고
    호출자(main)가 기존 소식을 유지한다."""
    per_dong, status = {}, "ok"
    for dong, slug in MAPO_DONGS:
        list_url = f"https://www.mapo.go.kr/site/{slug}/board/townnews/list"
        html_text, st = fetch_html(list_url, timeout=25)
        if html_text is None:
            status = st
            per_dong[dong] = []
            print(f"  서울 마포구 {dong}: {st} notices=0")
            continue
        per_dong[dong] = parse_mapo_dong(html_text, "서울 마포구", dong, slug)
        print(f"  서울 마포구 {dong}: ok notices={len(per_dong[dong])}")
        time.sleep(0.4)
    return per_dong, status



def parse_dobong(html_text: str, gu: str, dong: str, code: str):
    """도봉구 동별 '동 소식 공지사항'(bbs.asp) 1페이지.
    제목 <a>의 bbs.asp?bmode=D&pcode=<id>&code=<code>를 상세 식별자로 쓴다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(r"bbs\.asp\?bmode=D(?:&amp;|&)pcode=(\d+)(?:&amp;|&)code=(\d+)", row)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        am = re.search(r"<a[^>]*bmode=D[^>]*>(.*?)</a>", row, re.S)
        title = _clean_title(am.group(1)) if am else ""
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = (f"https://www.dobong.go.kr/dong/bbs.asp"
               f"?bmode=D&pcode={m.group(1)}&code={code}")
        notices.append({"title": title, "category": classify(title), "date": date,
                        "region": f"{gu} {dong}", "source": "동 소식 공지사항",
                        "url": url, "gu": gu, "dong": dong, "url_kind": "detail"})
    notices.sort(key=lambda n: n.get("date", ""), reverse=True)
    return notices[:10]


def fetch_dobong():
    """도봉구 14개 동을 돌아 {dong: [notices]}와 상태를 돌려준다.
    목록 1페이지에 최신 10개가 있다. 실패한 동은 빈 리스트를 돌려주고
    호출자(main)가 기존 소식을 유지한다."""
    per_dong, status = {}, "ok"
    for dong, code in DOBONG_DONGS:
        list_url = f"https://www.dobong.go.kr/dong/bbs.asp?code={code}"
        html_text, st = fetch_html(list_url, timeout=25)
        if html_text is None:
            status = st
            per_dong[dong] = []
            print(f"  서울 도봉구 {dong}: {st} notices=0")
            continue
        per_dong[dong] = parse_dobong(html_text, "서울 도봉구", dong, code)
        print(f"  서울 도봉구 {dong}: ok notices={len(per_dong[dong])}")
        time.sleep(0.4)
    return per_dong, status


def parse_gangbuk(html_text: str, gu: str, dong: str, menu_no: str, dong_cd: str):
    """강북구 동별 게시판 B0000199 '우리동소식' 1페이지.
    제목 <a>의 view.do?nttId=<id>를 상세 식별자로 쓴다."""
    notices, seen = [], set()
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(r"/dong/bbs/B0000199/view\.do\?menuNo=(\d+)&(?:amp;)?nttId=(\d+)&(?:amp;)?dongCd=(\d+)", row)
        if not m or m.group(2) in seen:
            continue
        seen.add(m.group(2))
        am = re.search(r"<a[^>]*view\.do[^>]*>(.*?)</a>", row, re.S)
        title = _clean_title(am.group(1)) if am else ""
        if not title:
            continue
        date = _extract_date(row, _td_cells(row))
        url = (f"https://gangbuk.go.kr:18000/dong/bbs/B0000199/view.do"
               f"?menuNo={menu_no}&nttId={m.group(2)}&dongCd={dong_cd}")
        notices.append({"title": title, "category": classify(title), "date": date,
                        "region": f"{gu} {dong}", "source": "우리동소식",
                        "url": url, "gu": gu, "dong": dong, "url_kind": "detail"})
    notices.sort(key=lambda n: n.get("date", ""), reverse=True)
    return notices[:10]


def fetch_gangbuk():
    """강북구 13개 동을 돌아 {dong: [notices]}와 상태를 돌려준다.
    curl로는 gangbuk.go.kr:18000 직접 가져오기 HTTP 200이나, 이 서버 urllib로는
    프록시에서 :18000이 막혀 실패할 수 있다. 실패한 동은 빈 리스트를 돌려주고
    호출자(main)가 기존 소식을 유지한다."""
    per_dong, status = {}, "ok"
    for dong, dong_cd, menu_no in GANGBUK_DONGS:
        list_url = (f"https://gangbuk.go.kr:18000/dong/bbs/B0000199/list.do"
                    f"?menuNo={menu_no}&dongCd={dong_cd}")
        html_text, st = fetch_html(list_url, timeout=25)
        if html_text is None:
            status = st
            per_dong[dong] = []
            print(f"  서울 강북구 {dong}: {st} notices=0")
            continue
        per_dong[dong] = parse_gangbuk(html_text, "서울 강북구", dong, menu_no, dong_cd)
        print(f"  서울 강북구 {dong}: ok notices={len(per_dong[dong])}")
        time.sleep(0.4)
    return per_dong, status


def _norm_dong_name(name: str) -> str:
    """노원구 동명 표기 정규화: 공백·'.'·'·'를 통일한다. '상계3.4동' → '상계3·4동'."""
    n = re.sub(r"\s+", "", name or "")
    n = n.replace(".", "·")
    return n


def parse_nowon_page(html_text: str):
    """노원구 통합 게시판 1페이지. 행 단위로 (담당부서, 제목, 날짜, URL)을 뽑는다.
    날짜는 목록에 비어 있는 경우가 많아 q_bbscttSn 앞 8자리(YYYYMMDD)에서 파생한다.
    담당부서가 노원구 동명이 아닌 행(구청 부서 글)은 제외한다."""
    items = []
    for row in _tr_rows(html_text):
        if _is_fixed_row(row):
            continue
        m = re.search(
            r'<a[^>]*href="BD_selectBbs\.do\?q_bbsCode=1103(?:&amp;|&)q_bbscttSn=(\d+)"[^>]*>(.*?)</a>',
            row, re.S | re.I)
        if not m:
            continue
        sn, atitle = m.group(1), m.group(2)
        title = _clean_title(atitle)
        # 제목 끝의 '등'은 한 게시글 안에 복수 소식이 묶였다는 뜻이라 떼고 기록한다.
        title = re.sub(r"\s+등$", "", title)
        if not title:
            continue
        cells = _td_cells(row)
        dept = _strip_tags(cells[2]) if len(cells) > 2 else ""
        dong = _norm_dong_name(dept)
        if dong not in NOWON_DONGS:
            continue
        if len(sn) < 8 or not sn[:8].isdigit():
            continue
        date = f"{sn[0:4]}-{sn[4:6]}-{sn[6:8]}"
        url = (f"https://www.nowon.kr/www/user/bbs/BD_selectBbs.do"
               f"?q_bbsCode=1103&q_bbscttSn={sn}")
        items.append({"dong": dong, "title": title, "date": date, "url": url, "sn": sn})
    return items


def fetch_nowon(max_pages: int = 30):
    """노원구 통합 게시판을 페이지 순회하며 동별 최신 10개씩 모은다.
    모든 동이 10개를 채우면 조기 종료한다. 페이지 한 번의 일시적 실패에는
    3번까지 재시도하고, 그래도 안 되면 다음 페이지로 넘어간다(3페이지 연속
    실패하면 중단 — 성공하면 연속 실패 카운터가 초기화된다). 스캔이 끝난 뒤
    실패한 페이지는 한 번 더 재시도한다. {dong: [notices]}와 상태를 돌려준다.
    실패 페이지가 있으면 status는 'ok'가 아니라 partial로 기록한다."""
    per_dong = {d: [] for d in NOWON_DONGS}
    seen_sn = set()
    status = "ok"
    pages = 0
    failed_pages = []
    consec_failed = 0

    def _scan_page(page):
        url = f"{NOWON_LIST_URL}&q_currPage={page}"
        html_text, st = None, ""
        for _attempt in range(3):
            html_text, st = fetch_html(url, timeout=25)
            if html_text is not None:
                break
            time.sleep(1)
        if html_text is None:
            return None, st
        for item in parse_nowon_page(html_text):
            if item["sn"] in seen_sn:
                continue
            seen_sn.add(item["sn"])
            if len(per_dong[item["dong"]]) >= 10:
                continue
            per_dong[item["dong"]].append(_notice(
                f"서울 노원구 {item['dong']}", "부서·동 소식",
                item["title"], item["date"], item["url"]))
        return True, "ok"

    for page in range(1, max_pages + 1):
        pages = page
        got, st = _scan_page(page)
        if got is None:
            status = st
            failed_pages.append(page)
            consec_failed += 1
            if consec_failed >= 3:
                break
            continue
        consec_failed = 0
        if all(len(v) >= 10 for v in per_dong.values()):
            break
    # 실패 페이지는 스캔 종료 후 한 번 더 재시도한다.
    for page in list(failed_pages):
        got, st = _scan_page(page)
        if got is not None:
            failed_pages.remove(page)
    notices = {}
    for dong, lst in per_dong.items():
        lst.sort(key=lambda n: n.get("date", ""), reverse=True)
        notices[dong] = lst[:10]
    if failed_pages:
        status = (f"partial:pages={pages}/{max_pages},"
                  f"failed_pages={failed_pages}")
    else:
        status = "ok"
    print(f"  nowon: pages={pages} status={status}")
    return notices, status


LIST_PARSERS = {
    "bbs": parse_bbs_list,
    "gwanak": parse_gwanak,
    "gangdong": parse_gangdong,
    "sejong": parse_sejong,
    "donggu": parse_donggu,
    "paju": parse_paju,
    "icheon": parse_icheon,
    "jongno": parse_jongno,
    "mapo": parse_mapo,
    "gangnam": parse_gangnam,
    "junggu": parse_junggu_dong_list,
}


def fetch_list(src: dict, timeout: int = 25):
    attempts = max(1, src.get("retries", 1))
    html_text, status = None, ""
    for _try in range(attempts):
        html_text, status = fetch_html(src["list_url"], timeout=timeout)
        if html_text is not None:
            break
        if _try < attempts - 1:
            time.sleep(0.8)
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


def _merge_keep_old(new_items, old_items, limit=10):
    """새 수집 결과와 기존 소식을 URL 기준으로 합집합해 날짜순 상위 limit개로 자른다.
    부분 수집으로 새 건수가 기존보다 적어도 기존 글이 통째로 날아가지 않는다.
    동별 상한 밖으로 밀린 오래된 글은 합집합에서도 잘린다."""
    by_url = {}
    for n in (old_items or []):
        by_url[n.get("url") or n.get("title", "")] = n
    for n in (new_items or []):
        by_url[n.get("url") or n.get("title", "")] = n
    merged = sorted(by_url.values(), key=lambda n: n.get("date", ""), reverse=True)
    return merged[:limit]


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

    # --- 동 행정복지센터 (data_dong.json, v0.8) ---
    old_dong = {}
    if OUT_DONG.exists():
        try:
            old_dong = json.loads(OUT_DONG.read_text(encoding="utf-8"))
        except Exception:
            old_dong = {}
    old_dongs = {}
    for gu in old_dong.get("gus", []):
        for d in gu.get("dongs", []):
            old_dongs[(gu.get("gu"), d.get("dong"))] = d

    gu_map = {}
    dong_total = 0
    for src in dong_sources():
        if src.get("sleep_before"):
            time.sleep(src["sleep_before"])
        items, status = fetch_list(src, timeout=src.get("timeout", 25))
        old_items = old_dongs.get((src["gu"], src["dong"]), {}).get("notices", [])
        if items:
            # 부분 수집으로 기존보다 적게 와도 기존 글을 통째로 버리지 않는다.
            # 새 결과와 기존 소식을 합집합해 날짜순 상위 10개로 자른다.
            dong_notices = _merge_keep_old(items[:10], old_items)
        else:
            # 실패 시 기존 소식을 유지하고, 새로 만든 가짜 소식은 넣지 않는다.
            dong_notices = old_items
        for n in dong_notices:
            n.setdefault("gu", src["gu"])
            n.setdefault("dong", src["dong"])
        dong_total += len(dong_notices)
        entry = {
            "dong": src["dong"],
            "board": src["board"],
            "list_url": src["list_url"],
            "method": "html_list",
            "status": status["status"],
            "count": len(dong_notices),
            "notices": dong_notices,
        }
        if src.get("slug"):
            entry["slug"] = src["slug"]
        if src.get("bbs_no") is not None:
            entry["bbs_no"] = src["bbs_no"]
        if src.get("key") is not None:
            entry["key"] = src["key"]
        if src.get("dept_code"):
            entry["dept_code"] = src["dept_code"]
        if src.get("dong_cd"):
            entry["dong_cd"] = src["dong_cd"]
        if src.get("sub_key"):
            entry["sub_key"] = src["sub_key"]
        if src.get("contents_key"):
            entry["contents_key"] = src["contents_key"]
        if src.get("menu_no"):
            entry["menu_no"] = src["menu_no"]
        if src.get("cb_idx"):
            entry["cb_idx"] = src["cb_idx"]
        if src.get("office"):
            entry["office"] = src["office"]
        if src.get("cmsid"):
            entry["cmsid"] = src["cmsid"]
        # 브라우저 경유로 채운 동(성동구)은 확인 시점·URL 주의사항을 유지한다.
        _old_entry = old_dongs.get((src["gu"], src["dong"]), {})
        for _k in ("note", "url_note", "checked_at_kst", "crawled_at_kst"):
            if _old_entry.get(_k):
                entry[_k] = _old_entry[_k]
        gu_map.setdefault(src["gu"], []).append(entry)
        print(f"  {src['region']}: {status['status']} notices={len(dong_notices)}")

    # --- 노원구 (통합 게시판 1개를 페이지 순회, 동별로 나눔) ---
    nowon_notices, nowon_status = fetch_nowon()
    nowon_entries = []
    for dong in NOWON_DONGS:
        old_items = old_dongs.get(("서울 노원구", dong), {}).get("notices", [])
        items = nowon_notices.get(dong, [])
        if items:
            # 부분 스캔 결과로 통째로 덮지 않는다. 합집합 후 동별 top-10.
            items = _merge_keep_old(items, old_items)
        else:
            items = old_items
        for n in items:
            n.setdefault("gu", "서울 노원구")
            n.setdefault("dong", dong)
        dong_total += len(items)
        nowon_entries.append({
            "dong": dong,
            "board": "부서·동 소식",
            "list_url": NOWON_LIST_URL,
            "method": "html_list",
            "status": nowon_status if items else f"no_items:{nowon_status}",
            "count": len(items),
            "notices": items,
        })
        print(f"  서울 노원구 {dong}: {nowon_status} notices={len(items)}")
    gu_map["서울 노원구"] = nowon_entries

    # --- 광진구 (1~3페이지 합쳐 날짜순 상위 10개) ---
    gwangjin_notices, gwangjin_status = fetch_gwangjin()
    gwangjin_entries = []
    for dong, cd, menu in GWANGJIN_DONGS:
        old_items = old_dongs.get(("서울 광진구", dong), {}).get("notices", [])
        items = gwangjin_notices.get(dong, [])
        items = _merge_keep_old(items, old_items) if items else old_items
        for n in items:
            n.setdefault("gu", "서울 광진구")
            n.setdefault("dong", dong)
        dong_total += len(items)
        gwangjin_entries.append({
            "dong": dong, "board": "우리마을소식",
            "list_url": f"https://www.gwangjin.go.kr/dong/bbs/B0000127/list.do?menuNo={menu}&dongCd={cd}",
            "method": "html_list",
            "status": gwangjin_status if items else f"no_items:{gwangjin_status}",
            "count": len(items), "notices": items,
            "dong_cd": cd, "menu_no": menu,
        })
    gu_map["서울 광진구"] = gwangjin_entries

    # --- 동작구 (1~3페이지 합쳐 날짜순 상위 10개) ---
    dongjak_notices, dongjak_status = fetch_dongjak()
    dongjak_entries = []
    for dong, cd, menu in DONGJAK_DONGS:
        old_items = old_dongs.get(("서울 동작구", dong), {}).get("notices", [])
        items = dongjak_notices.get(dong, [])
        items = _merge_keep_old(items, old_items) if items else old_items
        for n in items:
            n.setdefault("gu", "서울 동작구")
            n.setdefault("dong", dong)
        dong_total += len(items)
        dongjak_entries.append({
            "dong": dong, "board": "동네소식",
            "list_url": f"https://www.dongjak.go.kr/dong/bbs/B0000301/list.do?menuNo={menu}&dongCd={cd}",
            "method": "html_list",
            "status": dongjak_status if items else f"no_items:{dongjak_status}",
            "count": len(items), "notices": items,
            "dong_cd": cd, "menu_no": menu,
        })
    gu_map["서울 동작구"] = dongjak_entries

    # --- 서대문구 (EUC-KR, _fetch_euckr 경유) ---
    seodaemun_notices, seodaemun_status = fetch_seodaemun()
    seodaemun_entries = []
    for dong, slug in SEODAEMUN_DONGS:
        old_items = old_dongs.get(("서울 서대문구", dong), {}).get("notices", [])
        items = seodaemun_notices.get(dong, [])
        items = _merge_keep_old(items, old_items) if items else old_items
        for n in items:
            n.setdefault("gu", "서울 서대문구")
            n.setdefault("dong", dong)
        dong_total += len(items)
        seodaemun_entries.append({
            "dong": dong, "board": "우리동소식",
            "list_url": f"https://www.sdm.go.kr/dong/{slug}/citizen/notice.do",
            "method": "html_list",
            "status": seodaemun_status if items else f"no_items:{seodaemun_status}",
            "count": len(items), "notices": items,
            "slug": slug,
        })
    gu_map["서울 서대문구"] = seodaemun_entries

    # --- 양천구 (동별 cbIdx, 1~2페이지 합쳐 일반글 상위 10개) ---
    yangcheon_notices, yangcheon_status = fetch_yangcheon()
    yangcheon_entries = []
    for dong, slug, cb_idx in YANGCHEON_DONGS:
        old_items = old_dongs.get(("서울 양천구", dong), {}).get("notices", [])
        items = yangcheon_notices.get(dong, [])
        items = _merge_keep_old(items, old_items) if items else old_items
        for n in items:
            n.setdefault("gu", "서울 양천구")
            n.setdefault("dong", dong)
        dong_total += len(items)
        yangcheon_entries.append({
            "dong": dong, "board": "우리동소식",
            "list_url": (f"https://www.yangcheon.go.kr/site/{slug}/ex/bbs/List.do"
                         f"?cbIdx={cb_idx}"),
            "method": "html_list",
            "status": yangcheon_status if items else f"no_items:{yangcheon_status}",
            "count": len(items), "notices": items,
            "slug": slug, "cb_idx": cb_idx,
        })
    gu_map["서울 양천구"] = yangcheon_entries

    # --- 서초구 (동별 DongList, cbIdx=57 + dongCode) ---
    seocho_notices, seocho_status = fetch_seocho()
    seocho_entries = []
    for dong, code in SEOCHO_DONGS:
        old_items = old_dongs.get(("서울 서초구", dong), {}).get("notices", [])
        items = seocho_notices.get(dong, [])
        items = _merge_keep_old(items, old_items) if items else old_items
        for n in items:
            n.setdefault("gu", "서울 서초구")
            n.setdefault("dong", dong)
        dong_total += len(items)
        seocho_entries.append({
            "dong": dong, "board": "공지사항",
            "list_url": ("https://www.seocho.go.kr/site/seocho/ex/bbs/DongList.do"
                         f"?cbIdx=57&dongCode={code}"),
            "method": "html_list",
            "status": seocho_status if items else f"no_items:{seocho_status}",
            "count": len(items), "notices": items,
            "dong_code": code,
        })
    gu_map["서울 서초구"] = seocho_entries

    # --- 마포구 (동별 서브사이트 우리동네소식) ---
    mapo_notices, mapo_status = fetch_mapo_dong()
    mapo_entries = []
    for dong, slug in MAPO_DONGS:
        old_items = old_dongs.get(("서울 마포구", dong), {}).get("notices", [])
        items = mapo_notices.get(dong, [])
        items = _merge_keep_old(items, old_items) if items else old_items
        for n in items:
            n.setdefault("gu", "서울 마포구")
            n.setdefault("dong", dong)
        dong_total += len(items)
        mapo_entries.append({
            "dong": dong, "board": "우리동네소식",
            "list_url": f"https://www.mapo.go.kr/site/{slug}/board/townnews/list",
            "method": "html_list",
            "status": mapo_status if items else f"no_items:{mapo_status}",
            "count": len(items), "notices": items,
            "slug": slug,
        })
    gu_map["서울 마포구"] = mapo_entries

    # --- 도봉구 (동별 bbs.asp) ---
    dobong_notices, dobong_status = fetch_dobong()
    dobong_entries = []
    for dong, code in DOBONG_DONGS:
        old_items = old_dongs.get(("서울 도봉구", dong), {}).get("notices", [])
        items = dobong_notices.get(dong, [])
        items = _merge_keep_old(items, old_items) if items else old_items
        for n in items:
            n.setdefault("gu", "서울 도봉구")
            n.setdefault("dong", dong)
        dong_total += len(items)
        dobong_entries.append({
            "dong": dong, "board": "동 소식 공지사항",
            "list_url": f"https://www.dobong.go.kr/dong/bbs.asp?code={code}",
            "method": "html_list",
            "status": dobong_status if items else f"no_items:{dobong_status}",
            "count": len(items), "notices": items,
            "code": code,
        })
    gu_map["서울 도봉구"] = dobong_entries

    # --- 강북구 (동별 게시판 B0000199) ---
    gangbuk_notices, gangbuk_status = fetch_gangbuk()
    gangbuk_entries = []
    for dong, dong_cd, menu_no in GANGBUK_DONGS:
        old_items = old_dongs.get(("서울 강북구", dong), {}).get("notices", [])
        items = gangbuk_notices.get(dong, [])
        items = _merge_keep_old(items, old_items) if items else old_items
        for n in items:
            n.setdefault("gu", "서울 강북구")
            n.setdefault("dong", dong)
        dong_total += len(items)
        gangbuk_entries.append({
            "dong": dong, "board": "우리동소식",
            "list_url": (f"https://gangbuk.go.kr:18000/dong/bbs/B0000199/list.do"
                         f"?menuNo={menu_no}&dongCd={dong_cd}"),
            "method": "html_list",
            "status": gangbuk_status if items else f"no_items:{gangbuk_status}",
            "count": len(items), "notices": items,
            "dong_cd": dong_cd, "menu_no": menu_no,
        })
    gu_map["서울 강북구"] = gangbuk_entries

    gus = [{"gu": gu, "dongs": dongs} for gu, dongs in gu_map.items()]
    dong_data = {
        "service": "udong",
        "generated_at_kst": now.strftime("%Y-%m-%d %H:%M KST"),
        "generated_at": now.isoformat(),
        "gus": gus,
        "total_dongs": sum(len(g["dongs"]) for g in gus),
        "total_notices": dong_total,
        "note": ("동 행정복지센터 소식이다. 제목·날짜·원문 링크만 저장하고 본문은 복사하지 않는다. "
                 "한 동 가져오기가 실패하면 그 동의 기존 소식을 유지한다. "
                 "성동구는 이 서버에서 직접 가져오기가 끊겨 브라우저 경유가 필요하다. "
                 "동 소식은 주민등록 공시송달·최고공고 비중이 높아 선별이 필요할 수 있다. "
                 "종로구·중랑구는 목록 URL 확인됐으나 라이브 소식 채우기가 대기 중이고, "
                 "용산구·강서구는 동 게시판 목록 URL 미확인으로 제외했다."),
    }
    OUT_DONG.write_text(json.dumps(dong_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_DONG} dongs={dong_data['total_dongs']} total_notices={dong_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
