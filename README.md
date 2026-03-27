# Energy News Briefing

한국 에너지/전력 관련 뉴스를 자동 수집하여 카드뉴스 형태로 보여주는 서비스입니다.

## 기능
- Google News RSS 기반 자동 뉴스 수집 (매일 08:00, 14:00 KST)
- VPP/가상발전소 관련 기사 우선 표시
- 카테고리별 필터링
- 모바일/PC 반응형 디자인

## 검색 카테고리
VPP | 전력시장 | ESS | 태양광/RPS | 차세대전력망 | 전기요금 | 제도개선 | AI

## 설정 방법

### 1. GitHub 레포지토리 생성
```bash
cd energy-news
git init
git add .
git commit -m "초기 설정"
git remote add origin https://github.com/본인아이디/energy-news.git
git branch -M main
git push -u origin main
```

### 2. GitHub Pages 활성화
1. 레포지토리 → Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: **main** / **(root)**
4. Save

### 3. 첫 실행 (수동)
1. 레포지토리 → Actions 탭
2. "에너지 뉴스 수집" 워크플로우 선택
3. "Run workflow" 클릭

이후 매일 08:00, 14:00 KST에 자동 실행됩니다.

## 접속
`https://본인아이디.github.io/energy-news`

## 키워드 수정
`scripts/fetch_news.py`의 `SEARCH_QUERIES` 리스트를 수정하세요.
