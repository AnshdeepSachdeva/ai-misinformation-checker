# researcher.py
import json, re, requests
from urllib.parse import quote

HEADERS = {
    "User-Agent": "ai-judgement/0.2 (contact: you@example.com)",
    "Accept": "application/json",
}
SEARCH_API  = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={q}&srlimit={k}&format=json&utf8=1"
SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

QUERIES = [
    "{topic}",
    "{topic} facts",
    "{topic} controversy",
    "{topic} hoax",
    "{topic} timeline",
]

def _clean(txt: str, max_len=320):
    txt = re.sub(r"\[[0-9]+\]", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:max_len]

def _wiki_once(query: str, k: int):
    r = requests.get(SEARCH_API.format(q=quote(query), k=k), headers=HEADERS, timeout=20)
    r.raise_for_status()
    hits = r.json().get("query", {}).get("search", [])
    out = []
    for h in hits:
        title = h.get("title")
        if not title:
            continue
        s = requests.get(SUMMARY_API.format(title=quote(title.replace(" ", "_"))), headers=HEADERS, timeout=20)
        if s.status_code != 200:
            continue
        sj = s.json()
        summary = sj.get("extract") or sj.get("description") or ""
        summary = _clean(summary)
        if not summary:
            continue
        url = f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
        out.append({"title": title, "text": summary, "source": url})
    return out

def wiki_research(topic: str, k: int = 6):
    items = []
    for q in QUERIES:
        items += _wiki_once(q.format(topic=topic), k=3)
    # de-dup by title, cap to k
    seen, out = set(), []
    for it in items:
        if it["title"] in seen:
            continue
        seen.add(it["title"])
        out.append(it)
        if len(out) == k:
            break
    # assign IDs R1…Rn
    for i, it in enumerate(out, 1):
        it["id"] = f"R{i}"
        it["text"] = it["text"][:320]
    return out

def build_evidence(topic: str, k: int = 6, out_json="research_evidence.json", out_txt="research_evidence.txt"):
    items = wiki_research(topic, k=k)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    with open(out_txt, "w", encoding="utf-8") as f:
        for it in items:
            f.write(f"{it['id']}|{it['title']}: {it['text']} (src: {it['source']})\n")
    return items, out_json, out_txt

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "Example headline"
    items, j, t = build_evidence(topic)
    print(f"Wrote {len(items)} items -> {j} and {t}")
