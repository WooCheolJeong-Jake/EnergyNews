"""
에너지 뉴스 수집기
Google News RSS에서 한국 에너지/전력 관련 기사를 수집하여 JSON으로 저장
"""

import json
import os
import re
import hashlib
import urllib.request
import urllib.parse
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

# ============================================================
# 검색 키워드 설정 (원하는 대로 수정 가능)
# ============================================================
SEARCH_QUERIES = [
    # (검색어, 카테고리)
    ("VPP 가상발전소 통합발전소", "VPP"),
    ("전력시장 전력거래", "전력시장"),
    ("ESS 에너지저장장치", "ESS"),
    ("태양광 신재생에너지 RPS", "태양광/RPS"),
    ("차세대전력망 마이크로그리드", "차세대전력망"),
    ("전기요금 요금제도", "전기요금"),
    ("에너지 신사업 제도개선", "제도개선"),
    ("에너지 AI 인공지능 전력", "AI"),
]

# VPP 관련 우선 키워드
PRIORITY_KEYWORDS = ["VPP", "vpp", "가상발전소", "통합발전소", "분산에너지"]

# 수집 기간 (시간 단위)
FETCH_HOURS = 24

# 출력 경로
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "news.json")

KST = timezone(timedelta(hours=9))


def fetch_rss(query: str) -> bytes:
    """Google News RSS를 가져온다."""
    encoded = urllib.parse.quote(query)
    url = (
        f"https://news.google.com/rss/search?"
        f"q={encoded}+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def parse_rss(xml_bytes: bytes, category: str) -> list[dict]:
    """RSS XML을 파싱하여 기사 리스트를 반환한다."""
    articles = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return articles

    for item in root.iter("item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date_str = item.findtext("pubDate", "").strip()
        source_elem = item.find("source")
        source = source_elem.text.strip() if source_elem is not None and source_elem.text else ""
        description = item.findtext("description", "").strip()
        # HTML 태그 제거
        description = re.sub(r"<[^>]+>", "", description).strip()

        # 날짜 파싱
        pub_date = None
        if pub_date_str:
            try:
                pub_date = parsedate_to_datetime(pub_date_str)
            except Exception:
                pub_date = None

        # 최근 FETCH_HOURS 이내 기사만
        if pub_date:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=FETCH_HOURS)
            if pub_date < cutoff:
                continue

        # 우선순위 판별
        is_priority = any(kw in title or kw in description for kw in PRIORITY_KEYWORDS)

        # 고유 ID 생성
        article_id = hashlib.md5(link.encode()).hexdigest()[:12]

        articles.append({
            "id": article_id,
            "title": title,
            "link": link,
            "source": source,
            "pubDate": pub_date.isoformat() if pub_date else "",
            "description": description[:200],
            "category": category,
            "priority": is_priority,
        })

    return articles


def deduplicate(articles: list[dict]) -> list[dict]:
    """중복 기사 제거 (링크 기준)."""
    seen = set()
    unique = []
    for a in articles:
        if a["id"] not in seen:
            seen.add(a["id"])
            unique.append(a)
    return unique


def main():
    all_articles = []

    for query, category in SEARCH_QUERIES:
        try:
            xml_data = fetch_rss(query)
            articles = parse_rss(xml_data, category)
            all_articles.extend(articles)
            print(f"[OK] '{query}' → {len(articles)}건")
        except Exception as e:
            print(f"[ERR] '{query}' → {e}")

    # 중복 제거
    all_articles = deduplicate(all_articles)

    # 우선순위 → 최신순 정렬
    all_articles.sort(key=lambda x: (not x["priority"], x.get("pubDate", "")), reverse=False)
    all_articles.sort(key=lambda x: x.get("pubDate", ""), reverse=True)
    # 우선순위 기사를 상단으로
    priority = [a for a in all_articles if a["priority"]]
    normal = [a for a in all_articles if not a["priority"]]
    all_articles = priority + normal

    # 수집 메타 정보
    now_kst = datetime.now(KST)
    output = {
        "lastUpdated": now_kst.isoformat(),
        "totalCount": len(all_articles),
        "articles": all_articles,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(all_articles)}건 저장 완료 → {OUTPUT_PATH}")
    print(f"수집 시각: {now_kst.strftime('%Y-%m-%d %H:%M KST')}")


if __name__ == "__main__":
    main()
