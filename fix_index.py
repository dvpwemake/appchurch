import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update form action and condition
text = text.replace('action="https://formspree.io/f/https://formspree.io/f/mqeggedw"', 'action="https://formspree.io/f/mqeggedw"')
text = text.replace("if(this.action.includes('https://formspree.io/f/mqeggedw')){", "if(this.action.includes('YOUR_FORM_ID')){")

# 2. Move Good News sector
# It's bounded by <!-- GOOD NEWS --> and <!-- ANNOUNCEMENTS SECTION
gn_match = re.search(r'<!-- GOOD NEWS -->\s.*?<!-- ANNOUNCEMENTS SECTION \([^)]+\) -->', text, flags=re.DOTALL)
if gn_match:
    gn_content = gn_match.group(0).replace('<!-- ANNOUNCEMENTS SECTION (hidden by default, shown when active data exists) -->', '')
    text = text.replace(gn_match.group(0), '<!-- ANNOUNCEMENTS SECTION (hidden by default, shown when active data exists) -->')

    contact_pos = text.find('<!-- CONTACT -->')
    if contact_pos != -1:
        text = text[:contact_pos] + gn_content.rstrip() + '\n\n' + text[contact_pos:]

# 3. Add hero announcement card
hero_card = """    <!-- Announcement overlay -->
    <a href="announcements.html" class="hero-ann-card" id="hero-ann-card" style="display:none">
      <div class="hero-ann-badge">Latest Announcement</div>
      <h3 class="hero-ann-title" id="hero-ann-title"></h3>
      <p class="hero-ann-desc" id="hero-ann-desc"></p>
      <span class="hero-ann-arrow">→</span>
    </a>
"""
# Find where to place the hero card: preferably after <p class="hero-p"> or in hero-body
hero_p_pos = text.find('</p>\n    <div class="hero-btns">')
if hero_p_pos != -1:
    text = text[:hero_p_pos+4] + '\n' + hero_card + text[hero_p_pos+4:]
else:
    # Fallback if text differs slightly
    body_pos = text.find('<div class="hero-btns">')
    if body_pos != -1:
        text = text[:body_pos] + hero_card + text[body_pos:]

# 4. Insert styling for the card
css_content = """
/* === HERO ANNOUNCEMENT CARD === */
.hero-ann-card {
  display: block;
  margin-top: 1.5rem;
  margin-bottom: 2rem;
  padding: 1.25rem 1.5rem;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-left: 4px solid var(--gold);
  border-radius: var(--r-lg);
  box-shadow: 0 10px 30px rgba(184, 145, 58, 0.15);
  max-width: 480px;
  text-decoration: none;
  transition: all var(--tr);
  position: relative;
  overflow: hidden;
  z-index: 10;
}
.hero-ann-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 35px rgba(184, 145, 58, 0.25);
  background: rgba(255, 255, 255, 0.95);
}
.hero-ann-badge {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 0.4rem;
}
.hero-ann-title {
  font-family: var(--ff);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.3rem;
  line-height: 1.3;
}
.hero-ann-desc {
  font-size: 0.85rem;
  color: var(--text-mid);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.hero-ann-arrow {
  position: absolute;
  top: 50%;
  right: 1.5rem;
  transform: translateY(-50%);
  font-size: 1.2rem;
  color: var(--gold);
  transition: transform var(--tr);
}
.hero-ann-card:hover .hero-ann-arrow {
  transform: translate(5px, -50%);
}
"""
text = text.replace('/* === ABOUT === */', css_content + '\n/* === ABOUT === */')

# 5. Connect JS to populate hero card
js_banner_pos = text.find("  // Section: show all")
if js_banner_pos != -1:
    js_hero = """
  // Hero Overlay Card
  const heroCard = document.getElementById('hero-ann-card');
  if (heroCard) {
    document.getElementById('hero-ann-title').textContent = first.title || '';
    document.getElementById('hero-ann-desc').textContent = first.body || '';
    heroCard.style.display = 'block';
  }

"""
    text = text[:js_banner_pos] + js_hero + text[js_banner_pos:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(text)

