# AppChurch Website — Installation & Maintenance Guide

**Version 2.0** · April 2026  
**Stack:** Static HTML · GitHub Pages · GitHub Actions · Python RSS Crawler

---

## What Changed in v2.0

| Feature | Before (v1) | After (v2) |
|---|---|---|
| News autoscan | Anthropic API (paid, $) | RSS crawler (free, no API key) |
| Scan config | Hardcoded in workflow | Editable via `editor.html` |
| Source list | Fixed 10 sources | Editable via `editor.html`, saved to `data/news-sources.json` |
| Manual trigger | GitHub Actions UI only | `editor.html` → Run Scan button |
| Hero section | Static stats bar | Live ticker with announcements + news |
| Editor | Basic | Full source manager + algorithm config + scan trigger |

---

## File Structure

```
appchurch/
├── index.html                  ← Main website (auto-updated by scanner)
├── editor.html                 ← Admin editor (access via /editor.html)
├── data/
│   └── news-sources.json       ← RSS sources + algorithm config (editable)
├── scripts/
│   └── scan_news.py            ← RSS crawler script (no API key needed)
├── .github/
│   └── workflows/
│       └── scan-news.yml       ← GitHub Actions workflow
├── img/                        ← Images (unchanged)
├── 404.html
├── CNAME
└── robots.txt
```

---

## 1. Initial Setup

### Step 1 — Upload Files to GitHub

1. Go to your GitHub repo: `https://github.com/dvpwemake/appchurch`
2. Upload all files from this zip, maintaining the folder structure.
3. Key: make sure `scripts/scan_news.py` and `data/news-sources.json` are committed.

> **Note:** The `img/` folder is unchanged — no need to re-upload images.

### Step 2 — Verify GitHub Actions

1. Go to **Actions** tab in your repo.
2. You should see the workflow **"Good News Auto-Scan"**.
3. The old workflow used `ANTHROPIC_API_KEY` — **this is no longer needed**. You can delete that secret from Settings → Secrets → Actions if you wish.
4. Test it: click **"Run workflow"** → **"Run workflow"** button.
5. Wait ~2 minutes. Check that it completes successfully (green ✓).

### Step 3 — Verify the Site

1. Go to `https://appchurchglobal.org`
2. You should see the **Live Feed ticker** at the bottom of the hero section scrolling through news and announcements.
3. The **Good News** section should show 6 stories.

---

## 2. Using the Editor

Access: `https://appchurchglobal.org/editor.html`  
Default password: **`appchurch2024`** ← Change this immediately in Settings!

### First-Time Editor Setup

1. **Open the editor** and log in.
2. **Set your GitHub credentials** (shown at the top of every panel):
   - Repository: `dvpwemake/appchurch`
   - Personal Access Token: create one at [github.com/settings/tokens](https://github.com/settings/tokens)
     - Type: Fine-grained token
     - Required permissions: **Contents** (Read & Write) + **Actions** (Read & Write)
3. Click **Save & Test** — you should see a green ✓ confirmation.
4. Change your editor password in the **Security** panel.

---

## 3. Managing News Sources

**Panel:** `editor.html` → 📡 News Sources

### Adding a Source
1. Click **+ Add Source**
2. Paste the RSS feed URL (e.g. `https://www.example.com/feed.rss`)
3. Give it a name and category
4. Toggle it **on**
5. Click **Save Source**
6. Click **💾 Save to GitHub** to push `data/news-sources.json`
7. Run a scan to apply changes

### Finding RSS URLs
Most Christian news sites have RSS feeds. Common patterns:
- `https://example.com/feed/`
- `https://example.com/rss.xml`
- `https://example.com/news.rss`

To test a feed URL, paste it in your browser. You should see XML content.

### Pre-installed Sources (12 enabled)
| Source | Category | URL |
|---|---|---|
| Christianity Today | Christian | christianitytoday.com |
| The Gospel Coalition | Faith | thegospelcoalition.org |
| Christian Post | Christian | christianpost.com |
| Religion News Service | Religion | religionnews.com |
| World Magazine | Christian | wng.org |
| Baptist Press | Mission | baptistpress.com |
| Church Leaders | Faith | churchleaders.com |
| Intl Christian Concern | Persecution | persecution.org |
| Open Doors USA | Persecution | opendoorsusa.org |
| Mission Frontiers | Mission | missionfrontiers.org |
| CBN News | Christian | cbn.com |
| Catholic News Agency | Christian | catholicnewsagency.com |

---

## 4. Tuning the Algorithm

**Panel:** `editor.html` → ⚙️ Scan Algorithm

### Key Settings

| Setting | Default | Description |
|---|---|---|
| Max stories | 6 | How many stories per daily scan |
| Lookback window | 48 hours | Only consider articles published in this window |
| Min relevance score | 1 | Stories below this score are excluded |

### How Scoring Works

Each story gets a score based on:

- **+2** per matched relevance keyword (e.g. "gospel", "church", "revival")
- **+30** if published < 3 hours ago
- **+22** if published 3–6 hours ago
- **+16** if published 6–12 hours ago
- **+10** if published 12–24 hours ago
- **+4** if published 24–48 hours ago
- **-100** if it matches any exclude keyword (effectively removed)

Stories are then deduplicated (similar titles merged) and the top N are selected.

### Category Detection

A story's category is determined by matching its title + summary against the **Category Keywords** lists. If no match, it inherits the source's default category.

---

## 5. Announcements

**Panel:** `editor.html` → 📢 Announcements

Announcements appear in two places on the site:
1. **Top banner** — a dismissible bar above the navigation
2. **Announcements section** — card grid in the page body
3. **Hero ticker** — shown in the Live Feed strip at bottom of hero

### Adding an Announcement
1. Click **+ New Announcement**
2. Fill in: title, body, date, optional tag (e.g. "Event", "Update")
3. Click **Save Announcement**
4. Click **💾 Save to GitHub** — this patches `ANNOUNCEMENT_DATA` in `index.html` directly

### Announcement Priority
The **first** announcement in the list is shown in the top banner. Reorder by deleting and re-adding if needed.

---

## 6. Running a Manual Scan

**Panel:** `editor.html` → 🔄 Run Scan

Click **▶ Run Scan Now** — this triggers the GitHub Actions workflow via `workflow_dispatch`.

**What happens:**
1. GitHub spins up a runner (Ubuntu)
2. Python fetches all enabled RSS feeds
3. Stories are scored, deduplicated, and ranked
4. `index.html` is updated with the new `GOOD_NEWS_DATA`
5. GitHub Pages redeploys (~30 seconds after commit)

**Total time:** ~2–3 minutes.

Click **🔍 Check Last Run Status** to see the latest workflow run result.

---

## 7. Editing the Script Directly

For advanced users: `scripts/scan_news.py` is fully documented Python 3.

### Manual local test
```bash
pip install requests
python3 scripts/scan_news.py --dry-run   # Preview without writing
python3 scripts/scan_news.py             # Actually update index.html
```

### Key functions
| Function | Purpose |
|---|---|
| `load_config()` | Reads `data/news-sources.json` (or uses defaults) |
| `fetch_rss(url)` | Downloads an RSS feed |
| `parse_rss(content, ...)` | Parses RSS 2.0 and Atom feeds |
| `score_item(item, ...)` | Calculates relevance score |
| `detect_category(item, ...)` | Assigns category from keywords |
| `title_similar(a, b)` | Deduplicates by title word overlap |

### Adding a custom scoring rule
In `score_item()`, add:
```python
# Example: boost stories mentioning your city
if 'new york' in text:
    score += 5
```

---

## 8. Hero Ticker

The ticker at the bottom of the hero section automatically pulls:
- Up to **3 announcements** (from `ANNOUNCEMENT_DATA`)
- Up to **6 latest news items** (from `GOOD_NEWS_DATA`)

**Speed:** ~55 px/second (comfortable reading pace).  
**Pause on hover:** Yes — the ticker pauses when the mouse hovers over it.  
**Clicking a news item:** Opens the article in a new tab.

To **hide the ticker**: remove the `hero-ticker-wrap` div from `index.html`, or add `display:none` to its CSS.

---

## 9. Schedule & Automation

The scan runs automatically every day:
- **Time:** 09:00 AM EST (14:00 UTC)
- **Cron:** `0 14 * * *`
- **No API key needed** — uses RSS feeds only

To change the schedule, edit `.github/workflows/scan-news.yml`:
```yaml
on:
  schedule:
    - cron: '0 14 * * *'   # Change this line
```

Common cron examples:
- `0 9 * * *` — 9AM UTC
- `0 14 * * *` — 2PM UTC (9AM EST)
- `0 14 * * 1-5` — Weekdays only

---

## 10. Troubleshooting

### Scan fails with "No items selected"
- Check that your RSS URLs are reachable (test in browser)
- Lower `minKeywordScore` to `0` in the editor config
- Increase `hoursWindow` to `72` or `96`
- Add more keywords in the algorithm config

### "GOOD_NEWS_DATA placeholder not found"
The script couldn't find the `const GOOD_NEWS_DATA = [...]` marker in `index.html`. This means the HTML was manually edited in a way that broke the pattern. Restore from git history: `git log`, then `git checkout <sha> -- index.html`.

### GitHub Actions says "No changes to commit"
The scan ran but produced identical results to the last scan. This is normal if news hasn't changed. It's not an error.

### Editor can't connect to GitHub
- Verify your token has **Contents** + **Actions** permissions
- Check the repo name format: `owner/repo` (e.g. `dvpwemake/appchurch`)
- Fine-grained tokens expire — check the expiry date

### Ticker not showing
- Check browser console for JS errors
- Make sure `GOOD_NEWS_DATA` in `index.html` is valid JSON (not empty `[]`)
- The ticker hides itself if there are no items

---

## 11. Security Notes

- The editor password is stored in `localStorage` — it's device/browser specific.
- Your GitHub token is stored in `localStorage` — **do not use a shared computer**.
- The editor is linked from the footer with `rel="nofollow"` and low opacity — it's obscure but not hidden. Consider adding HTTP Basic Auth at the hosting level for extra protection.
- The scanner script does not use any paid APIs. Running costs = $0.

---

## 12. Quick Reference

| Task | Where |
|---|---|
| Add/remove RSS sources | editor.html → Sources |
| Tune ranking algorithm | editor.html → Scan Algorithm |
| Run scan immediately | editor.html → Run Scan |
| Add announcement | editor.html → Announcements |
| Change editor password | editor.html → Security |
| View workflow logs | github.com/dvpwemake/appchurch/actions |
| Edit Python script | scripts/scan_news.py |
| Edit source config | data/news-sources.json |

---

*AppChurch · appchurchglobal.org · Where Faith Meets the Future*
