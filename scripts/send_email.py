"""
에너지 뉴스 이메일 발송
수집된 뉴스를 마크다운 형태의 HTML 이메일로 발송
"""

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "news.json")


def load_news() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_email_html(data: dict) -> str:
    """뉴스 데이터를 이메일용 HTML로 변환한다."""
    articles = data.get("articles", [])
    now_kst = datetime.now(KST)
    date_str = now_kst.strftime("%Y년 %m월 %d일 %H:%M")

    priority_articles = [a for a in articles if a.get("priority")]
    normal_articles = [a for a in articles if not a.get("priority")]

    html = f"""
    <div style="max-width:700px;margin:0 auto;font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;color:#1a1a2e;line-height:1.7;">
      <div style="background:linear-gradient(135deg,#0f172a,#1d4ed8);color:white;padding:28px 24px;border-radius:12px 12px 0 0;text-align:center;">
        <h1 style="margin:0;font-size:22px;font-weight:700;">Energy News Briefing</h1>
        <p style="margin:6px 0 0;font-size:13px;opacity:0.7;">{date_str} KST</p>
        <div style="margin-top:16px;display:flex;justify-content:center;gap:12px;">
          <div style="background:rgba(255,255,255,0.12);border-radius:8px;padding:8px 18px;text-align:center;">
            <div style="font-size:22px;font-weight:700;">{len(articles)}</div>
            <div style="font-size:11px;opacity:0.6;">전체</div>
          </div>
          <div style="background:rgba(255,255,255,0.12);border-radius:8px;padding:8px 18px;text-align:center;">
            <div style="font-size:22px;font-weight:700;">{len(priority_articles)}</div>
            <div style="font-size:11px;opacity:0.6;">VPP 주요</div>
          </div>
        </div>
      </div>
      <div style="background:#ffffff;padding:20px 24px;border:1px solid #e2e8f0;border-top:none;">
    """

    # VPP 주요 기사
    if priority_articles:
        html += '<h2 style="font-size:14px;color:#d97706;margin:16px 0 10px;border-bottom:2px solid #fef3c7;padding-bottom:6px;">VPP 주요 기사</h2>'
        for a in priority_articles:
            html += _article_html(a, is_priority=True)

    # 일반 기사
    if normal_articles:
        html += '<h2 style="font-size:14px;color:#3b82f6;margin:20px 0 10px;border-bottom:2px solid #eff6ff;padding-bottom:6px;">최신 기사</h2>'
        for a in normal_articles:
            html += _article_html(a, is_priority=False)

    html += """
      </div>
      <div style="background:#f8fafc;padding:14px 24px;border-radius:0 0 12px 12px;border:1px solid #e2e8f0;border-top:none;text-align:center;">
        <p style="margin:0;font-size:12px;color:#94a3b8;">Energy News Briefing &mdash; 자동 수집 by GitHub Actions</p>
      </div>
    </div>
    """
    return html


def _article_html(article: dict, is_priority: bool) -> str:
    """개별 기사 HTML 블록."""
    source = article.get("source", "")
    title = article.get("title", "")
    link = article.get("link", "")
    description = article.get("description", "")
    category = article.get("category", "")
    pub_date = article.get("pubDate", "")

    # 시간 포맷
    time_str = ""
    if pub_date:
        try:
            dt = datetime.fromisoformat(pub_date)
            time_str = dt.strftime("%m/%d %H:%M")
        except Exception:
            time_str = ""

    border_color = "#f59e0b" if is_priority else "#e2e8f0"
    bg_color = "#fffbeb" if is_priority else "#ffffff"

    return f"""
    <div style="border-left:3px solid {border_color};background:{bg_color};padding:10px 14px;margin-bottom:8px;border-radius:0 8px 8px 0;">
      <div style="margin-bottom:4px;">
        <span style="background:{'#fef3c7' if is_priority else '#eff6ff'};color:{'#92400e' if is_priority else '#1d4ed8'};font-size:11px;font-weight:600;padding:2px 8px;border-radius:4px;">{category}</span>
        {' <span style="background:#fef3c7;color:#92400e;font-size:11px;font-weight:600;padding:2px 8px;border-radius:4px;">VPP 주요</span>' if is_priority else ''}
      </div>
      <a href="{link}" style="color:#0f172a;text-decoration:none;font-size:14px;font-weight:600;line-height:1.5;">{title}</a>
      {f'<p style="font-size:12px;color:#64748b;margin:4px 0 0;line-height:1.5;">{description}</p>' if description else ''}
      <div style="font-size:11px;color:#94a3b8;margin-top:6px;">
        <strong style="color:#475569;">{source}</strong> · {time_str}
      </div>
    </div>
    """


def send_email(html_body: str):
    """Gmail SMTP로 이메일 발송."""
    gmail_addr = os.environ.get("GMAIL_ADDRESS", "")
    gmail_pw = os.environ.get("GMAIL_APP_PASSWORD", "")
    recipient = os.environ.get("RECIPIENT_EMAIL", "")

    if not all([gmail_addr, gmail_pw, recipient]):
        print("[SKIP] 이메일 환경변수가 설정되지 않음")
        return

    now_kst = datetime.now(KST)
    subject = f"[Energy News] {now_kst.strftime('%m/%d %H:%M')} 에너지 뉴스 브리핑"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Energy News <{gmail_addr}>"
    recipients = [r.strip() for r in recipient.split(",") if r.strip()]
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_addr, gmail_pw)
        server.sendmail(gmail_addr, recipients, msg.as_string())

    print(f"[OK] 이메일 발송 완료 → {recipient}")


def main():
    data = load_news()
    articles = data.get("articles", [])

    if not articles:
        print("[SKIP] 수집된 기사 없음, 이메일 발송 건너뜀")
        return

    html = build_email_html(data)
    send_email(html)


if __name__ == "__main__":
    main()
