#!/usr/bin/env python3
"""
AppChurch Good News Scanner — RSS-based crawler, no API key required.
Reads data/news-sources.json for source/algorithm config (editable from editor.html).
Writes updated GOOD_NEWS_DATA into index.html.

Usage: python3 scripts/scan_news.py [--dry-run]
"""
import json, os, re, sys, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import requests

# ── Paths ───────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(SCRIPT_DIR)
SOURCES_FILE = os.path.join(ROOT_DIR, 'data', 'news-sources.json')
INDEX_FILE   = os.path.join(ROOT_DIR, 'index.html')

DRY_RUN = '--dry-run' in sys.argv

# ── Defaults (used when news-sources.json missing or incomplete) ─────────────
DEFAULT_SOURCES = [
    {"url": "https://www.christianitytoday.com/news/rss.xml",        "name": "Christianity Today",            "category": "christian",    "enabled": True},
    {"url": "https://www.thegospelcoalition.org/feed/",               "name": "The Gospel Coalition",          "category": "faith",        "enabled": True},
    {"url": "https://www.christianpost.com/rss/news.rss",             "name": "Christian Post",                "category": "christian",    "enabled": True},
    {"url": "https://religionnews.com/feed/",                         "name": "Religion News Service",         "category": "religion",     "enabled": True},
    {"url": "https://wng.org/feed",                                   "name": "World Magazine",                "category": "christian",    "enabled": True},
    {"url": "https://www.baptistpress.com/feed/",                     "name": "Baptist Press",                 "category": "mission",      "enabled": True},
    {"url": "https://churchleaders.com/feed/",                        "name": "Church Leaders",                "category": "faith",        "enabled": True},
    {"url": "https://persecution.org/feed/",                          "name": "Intl Christian Concern",        "category": "persecution",  "enabled": True},
    {"url": "https://www.opendoorsusa.org/feed/",                     "name": "Open Doors USA",                "category": "persecution",  "enabled": True},
    {"url": "https://missionfrontiers.org/feed/",                     "name": "Mission Frontiers",             "category": "mission",      "enabled": True},
    {"url": "https://www1.cbn.com/rss-cbn-news-finance-headlines",   "name": "CBN News",                      "category": "christian",    "enabled": True},
    {"url": "https://www.catholicnewsagency.com/rssfeed/news/en/rss.xml", "name": "Catholic News Agency",      "category": "christian",    "enabled": True},
    {"url": "https://www.crosswalk.com/blogs/feeds/",                 "name": "Crosswalk",                     "category": "faith",        "enabled": False},
    {"url": "https://www.churchtimes.co.uk/rss/news",                 "name": "Church Times",                  "category": "religion",     "enabled": False},
]

DEFAULT_CONFIG = {
    "maxItems": 6,
    "hoursWindow": 48,
    "minKeywordScore": 1,
    "keywords": [
        "christian", "church", "faith", "jesus", "bible", "gospel",
        "prayer", "mission", "revival", "persecution", "worship",
        "ministry", "pastor", "theology", "evangelical", "protestant",
        "catholic", "orthodox", "baptism", "holy spirit", "resurrection",
        "salvation", "cross", "sermon", "congregation", "disciples"
    ],
    "excludeKeywords": ["casino", "gambling", "sex scandal", "explicit", "pornography"],
    "categoryKeywords": {
        "revival":      ["revival", "awakening", "outpouring", "pentecost", "movement", "thousands saved", "healing"],
        "persecution":  ["persecution", "martyr", "jailed", "prison", "arrested", "killed", "attacked", "ban", "outlawed", "imprisoned"],
        "mission":      ["mission", "missionary", "unreached", "evangelism", "church planting", "global", "international"],
        "faith":        ["faith", "discipleship", "devotion", "spiritual growth", "prayer movement", "bible study"]
    }
}

# ── RSS Fetching ─────────────────────────────────────────────────────────────
HEADERS = {'User-Agent': 'AppChurch-NewsCrawler/2.0 (+https://appchurchglobal.org)'}

def fetch_rss(url, timeout=25):
    try:
        r = requests.get(url, timeout=timeout, headers=HEADERS, allow_redirects=True)
        r.raise_for_status()
        return r.content
    except requests.exceptions.RequestException as e:
        print(f'  ✗ SKIP {url[:60]}: {e}')
        return None

def strip_tags(s):
    """Remove HTML tags and collapse whitespace."""
    if not s: return ''
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def parse_date(s):
    if not s: return None
    s = s.strip()
    for fmt in [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S GMT',
        '%a, %d %b %Y %H:%M:%S +0000',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S+00:00',
    ]:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass
    return None

def parse_rss(content, source_name, source_category):
    items = []
    try:
        # Handle BOM / encoding declaration issues
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f'  ✗ XML parse error: {e}')
        return items

    ATOM_NS = 'http://www.w3.org/2005/Atom'
    DC_NS   = 'http://purl.org/dc/elements/1.1/'

    def txt(el):
        return strip_tags(el.text) if el is not None and el.text else ''

    def find_any(parent, *tags):
        for tag in tags:
            el = parent.find(tag)
            if el is not None and el.text:
                return strip_tags(el.text)
        return ''

    # ─ RSS 2.0 ─
    for item in root.iter('item'):
        title   = txt(item.find('title'))
        link    = txt(item.find('link')) or (item.find('guid') and txt(item.find('guid'))) or ''
        desc    = find_any(item, 'description', 'summary', '{http://purl.org/rss/1.0/modules/content/}encoded')
        pub_raw = txt(item.find('pubDate')) or txt(item.find(f'{{{DC_NS}}}date'))
        dt      = parse_date(pub_raw)
        if title and link:
            items.append({'title': title[:200], 'summary': desc[:300], 'link': link,
                          'dt': dt, 'source': source_name, 'category': source_category})

    # ─ Atom ─
    if not items:
        for entry in root.findall(f'{{{ATOM_NS}}}entry'):
            title_el = entry.find(f'{{{ATOM_NS}}}title')
            link_el  = entry.find(f'{{{ATOM_NS}}}link[@rel="alternate"]') or entry.find(f'{{{ATOM_NS}}}link')
            sum_el   = entry.find(f'{{{ATOM_NS}}}summary') or entry.find(f'{{{ATOM_NS}}}content')
            pub_el   = entry.find(f'{{{ATOM_NS}}}published') or entry.find(f'{{{ATOM_NS}}}updated')
            title  = txt(title_el)
            link   = link_el.get('href', '') if link_el is not None else ''
            desc   = txt(sum_el)[:300]
            dt     = parse_date(txt(pub_el))
            if title and link:
                items.append({'title': title[:200], 'summary': desc, 'link': link,
                              'dt': dt, 'source': source_name, 'category': source_category})
    return items

# ── Scoring & Ranking ────────────────────────────────────────────────────────
def score_item(item, config, now):
    text = (item['title'] + ' ' + item['summary']).lower()
    score = 0
    for kw in config.get('keywords', []):
        if kw.lower() in text:
            score += 2
    for kw in config.get('excludeKeywords', []):
        if kw.lower() in text:
            score -= 100      # Hard exclude
    if item['dt']:
        age_h = (now - item['dt']).total_seconds() / 3600
        if   age_h <  3: score += 30
        elif age_h <  6: score += 22
        elif age_h < 12: score += 16
        elif age_h < 24: score += 10
        elif age_h < 48: score +=  4
    else:
        score += 2            # No date: mild penalty vs fresh news
    return score

def detect_category(item, config):
    text = (item['title'] + ' ' + item['summary']).lower()
    for cat, kws in config.get('categoryKeywords', {}).items():
        if any(kw.lower() in text for kw in kws):
            return cat
    return item.get('category', 'christian')

def title_similar(a, b, threshold=0.55):
    wa = set(re.findall(r'\w+', a.lower()))
    wb = set(re.findall(r'\w+', b.lower()))
    if not wa or not wb: return False
    return len(wa & wb) / max(len(wa), len(wb)) > threshold

# ── Main ─────────────────────────────────────────────────────────────────────
def load_config():
    if os.path.exists(SOURCES_FILE):
        with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        sources = data.get('sources', DEFAULT_SOURCES)
        config  = {**DEFAULT_CONFIG, **data.get('config', {})}
        print(f'Loaded config from {SOURCES_FILE}: {len(sources)} sources')
    else:
        sources = DEFAULT_SOURCES
        config  = DEFAULT_CONFIG
        print(f'Using built-in defaults ({len(sources)} sources) — create data/news-sources.json to customise')
    return sources, config

def main():
    print('══════════════════════════════════════════════')
    print('  AppChurch Good News Scanner  v2.0')
    print('══════════════════════════════════════════════')
    if DRY_RUN:
        print('  ⚠  DRY RUN — index.html will NOT be modified\n')

    sources, config = load_config()
    now    = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=config.get('hoursWindow', 48))
    TODAY  = now.strftime('%B %d, %Y')

    # ─ Fetch & parse all feeds ─
    all_items = []
    enabled   = [s for s in sources if s.get('enabled', True)]
    print(f'\nFetching {len(enabled)} enabled sources …\n')
    for src in enabled:
        print(f'→ {src["name"]}')
        content = fetch_rss(src['url'])
        if not content: continue
        items = parse_rss(content, src['name'], src.get('category', 'christian'))
        print(f'  ✓ {len(items)} items parsed')
        all_items.extend(items)

    print(f'\nTotal raw items: {len(all_items)}')

    # ─ Filter by time window ─
    recent = [i for i in all_items if not i['dt'] or i['dt'] >= cutoff]
    print(f'Within {config["hoursWindow"]}h window: {len(recent)}')

    # ─ Score ─
    for i in recent:
        i['_score'] = score_item(i, config, now)

    # ─ Sort ─
    recent.sort(key=lambda i: i['_score'], reverse=True)

    # ─ Select top N, deduplicating ─
    min_score = config.get('minKeywordScore', 1)
    selected  = []
    for item in recent:
        if item['_score'] < min_score:
            continue
        if any(title_similar(item['title'], s['title']) for s in selected):
            continue
        item['category'] = detect_category(item, config)
        selected.append(item)
        if len(selected) >= config.get('maxItems', 6):
            break

    if not selected:
        print('\n⚠  WARNING: No stories selected. Keeping existing data.')
        return

    # ─ Build output ─
    output = [
        {'rank': i+1, 'title': s['title'], 'summary': s['summary'][:250],
         'source': s['source'], 'sourceUrl': s['link'],
         'category': s['category'], 'image': ''}
        for i, s in enumerate(selected)
    ]

    batch = {'scannedAt': now.isoformat(), 'scanDate': TODAY, 'items': output}

    print(f'\nSelected {len(output)} stories for {TODAY}:')
    for it in output:
        print(f'  [{it["rank"]}] [{it["category"]:12s}] {it["title"][:65]}')

    if DRY_RUN:
        print('\n[DRY RUN] JSON output:')
        print(json.dumps(batch, indent=2, ensure_ascii=False))
        return

    # ─ Patch index.html ─
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    om = re.search(r'const GOOD_NEWS_DATA\s*=\s*(\[.*?\]);', html, re.DOTALL)
    old_batches = json.loads(om.group(1)) if om else []
    all_batches = [batch] + old_batches[:6]   # keep rolling 7 days

    new_json = json.dumps(all_batches, ensure_ascii=False, separators=(',', ':'))
    new_html = re.sub(
        r'const GOOD_NEWS_DATA\s*=\s*\[.*?\];',
        f'const GOOD_NEWS_DATA = {new_json};',
        html, flags=re.DOTALL
    )
    if new_html == html:
        raise ValueError('GOOD_NEWS_DATA placeholder not found in index.html — check the marker comment.')

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f'\n✓ index.html updated — {len(all_batches)} batches stored (rolling 7-day history)')
    print('══════════════════════════════════════════════')

if __name__ == '__main__':
    main()
