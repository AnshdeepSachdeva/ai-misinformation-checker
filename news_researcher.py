# news_researcher.py
import feedparser, trafilatura, json, re, time
from urllib.parse import quote
from datetime import date, timedelta
from dateparser import parse as dparse
from trafilatura.settings import use_config

# Configure Trafilatura
CFG = use_config()
CFG.set("DEFAULT", "USER_AGENT", "ai-misinfo/0.3 (contact: you@example.com)")

def _clean(txt, n=420):
    if not txt:
        return ""
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:n]

def _fetch_article(url):
    try:
        html = trafilatura.fetch_url(url, no_ssl=True, config=CFG)
        if not html:
            return None
        text = trafilatura.extract(html, include_links=False, include_tables=False, config=CFG)
        return _clean(text, 800)
    except Exception:
        return None

def _norm_date(s):
    dt = dparse(s, settings={"RETURN_AS_TIMEZONE_AWARE": False})
    return dt.date().isoformat() if dt else None

def google_news_rss(query, lang="en", country="IN"):
    q = quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl={lang}-{country}&gl={country}&ceid={country}:{lang}"
    return feedparser.parse(url)

def build_news_evidence(headline: str, k: int = 6,
                        out_json="news_evidence.json", out_txt="news_evidence.txt"):
    feed = google_news_rss(headline)
    items = []
    for entry in feed.entries:
        link = entry.get("link")
        title = (entry.get("title") or "").strip()
        if not link or not title:
            continue
        summary = _clean(entry.get("summary") or entry.get("description") or "")
        text = _fetch_article(link) or summary
        pub = entry.get("published") or entry.get("updated") or ""
        norm_date = _norm_date(pub)
        if not text:
            continue
        rec = {"title": title, "text": text, "source": link, "date": norm_date}
        items.append(rec)
        if len(items) >= k * 2:  # fetch a few extra to filter later
            break
        time.sleep(0.2)

    # Keep only recent articles (last 5 days)
    cutoff = date.today() - timedelta(days=5)
    items = [it for it in items if not it["date"] or it["date"] >= cutoff.isoformat()]
    items = items[:k]

    # Assign R1..Rn
    for i, it in enumerate(items, 1):
        it["id"] = f"R{i}"
        it["text"] = it["text"][:600]

    # Fallback if no items
    if not items:
        items = [{"id": "R1", "title": "No recent news found",
                  "text": "No relevant articles retrieved.",
                  "source": "none", "date": None}]

    # Save evidence
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    with open(out_txt, "w", encoding="utf-8") as f:
        for it in items:
            f.write(f"{it['id']}|{it['title']} ({it['date']}): {it['text']} (src: {it['source']})\n")

    return items, out_json, out_txt

if __name__ == "__main__":
    items, j, t = build_news_evidence("Example headline")
    print(f"Found {len(items)} items -> {j}, {t}")
