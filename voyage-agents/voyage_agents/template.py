"""
HTML template for Voyage Agents travel guide.
The builder agent outputs JSON data, which gets injected into this template.
"""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{{TITLE}}</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>✈️</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    :root {
      --primary: {{PRIMARY_COLOR}};
      --primary-light: {{PRIMARY_LIGHT}};
      --secondary: #F5C7A9;
      --accent: #E8967D;
      --bg: #F7FBFD;
      --card: #FFFFFF;
      --text: #3A4F5C;
      --muted: #8A9BAA;
      --radius: 14px;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      overflow-x: hidden;
      padding-bottom: 80px;
    }
    h1, h2, h3 { font-family: 'Playfair Display', serif; }

    .hero {
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 50%, var(--primary) 100%);
      padding: 3rem 1.5rem 4rem;
      text-align: center;
      color: white;
      position: relative;
    }
    .hero h1 { font-size: 2.4rem; margin-bottom: 0.3rem; letter-spacing: -0.5px; }
    .hero p { opacity: 0.9; font-size: 1rem; margin-bottom: 0.8rem; }
    .hero .date-badge {
      display: inline-block;
      background: rgba(255,255,255,0.2);
      backdrop-filter: blur(8px);
      padding: 0.4rem 1.2rem;
      border-radius: 999px;
      font-weight: 600;
      font-size: 0.85rem;
    }
    .wave { position: absolute; bottom: -1px; left: 0; width: 100%; overflow: hidden; line-height: 0; }
    .wave svg { display: block; width: 100%; height: 40px; }

    .bottom-nav {
      position: fixed; bottom: 0; left: 0; right: 0;
      display: flex; background: white;
      box-shadow: 0 -2px 16px rgba(0,0,0,0.1);
      z-index: 1000;
      padding-bottom: env(safe-area-inset-bottom);
    }
    .bottom-nav button {
      flex: 1; padding: 0.6rem 0.2rem; border: none; background: none;
      display: flex; flex-direction: column; align-items: center; gap: 2px;
      font-size: 0.65rem; font-weight: 600; color: var(--muted);
      cursor: pointer; transition: color 0.2s; font-family: 'Inter', sans-serif;
      border-top: 2.5px solid transparent;
    }
    .bottom-nav button.active { color: var(--primary); border-top-color: var(--primary); }
    .bottom-nav button svg { width: 22px; height: 22px; }

    .tab-content { display: none; }
    .tab-content.active { display: block; animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

    .sub-tabs {
      display: flex; gap: 0.4rem; padding: 1rem 1rem 0.5rem;
      overflow-x: auto; -webkit-overflow-scrolling: touch;
    }
    .sub-tabs::-webkit-scrollbar { display: none; }
    .sub-tab {
      padding: 0.45rem 1rem; border-radius: 999px; border: none;
      background: var(--primary-light); color: var(--primary);
      font-weight: 600; font-size: 0.8rem; white-space: nowrap;
      cursor: pointer; transition: all 0.2s; font-family: 'Inter', sans-serif;
      opacity: 0.7;
    }
    .sub-tab.active { background: var(--primary); color: white; opacity: 1; }

    .section-title { padding: 1rem 1rem 0.5rem; font-size: 1.3rem; color: var(--text); }

    .day-card {
      margin: 0.75rem 1rem; border-radius: var(--radius); overflow: hidden;
      background: var(--card); box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    .day-header {
      padding: 1rem 1.2rem; cursor: pointer;
      display: flex; align-items: center; gap: 0.8rem;
      background: linear-gradient(135deg, var(--primary), var(--primary-light)); color: white;
      user-select: none;
    }
    .day-emoji { font-size: 1.6rem; }
    .day-info { flex: 1; }
    .day-info .day-label { font-size: 0.7rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px; }
    .day-info .day-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; }
    .day-chevron { transition: transform 0.3s; font-size: 1.2rem; }
    .day-card.open .day-chevron { transform: rotate(180deg); }
    .day-slots { display: none; }
    .day-card.open .day-slots { display: block; }
    .time-slot {
      display: flex; gap: 0.8rem; padding: 0.8rem 1.2rem;
      border-bottom: 1px solid #f0f0f0; align-items: flex-start;
    }
    .time-slot:last-child { border-bottom: none; }
    .time-slot.highlight { background: #FEF7F0; border-left: 3px solid var(--secondary); }
    .slot-time { font-size: 0.72rem; font-weight: 700; color: var(--primary); min-width: 65px; padding-top: 2px; }
    .slot-activity { font-size: 0.88rem; font-weight: 500; }
    .slot-note { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }

    .venue-card {
      background: var(--card); border-radius: var(--radius);
      padding: 1rem; margin: 0.5rem 1rem;
      box-shadow: 0 2px 10px rgba(0,0,0,0.06);
      transition: transform 0.15s;
    }
    .venue-card:active { transform: scale(0.98); }
    .venue-card.highlight { border-left: 3px solid var(--secondary); }
    .venue-name { font-weight: 700; font-size: 1.05rem; margin-bottom: 0.35rem; }
    .venue-rating { color: var(--accent); font-size: 0.85rem; }
    .venue-area { font-size: 0.75rem; color: var(--muted); margin-bottom: 0.4rem; }
    .tags { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.5rem; }
    .tag { padding: 2px 8px; border-radius: 999px; font-size: 0.68rem; font-weight: 600; }
    .tag-food { background: #E8F5E9; color: #5A8F6A; }
    .tag-nightlife { background: #EDE7F6; color: #8B7BB8; }
    .tag-beach { background: #E3F2FD; color: #6BA3BE; }
    .tag-activity { background: #FFF3E0; color: #C48B5C; }
    .tag-local { background: #FCE4EC; color: #C28A8A; }
    .tag-aesthetic { background: #F3E5F5; color: #A07CB5; }
    .venue-desc { font-size: 0.8rem; color: var(--muted); margin-bottom: 0.5rem; line-height: 1.4; }
    .venue-bottom { display: flex; justify-content: space-between; align-items: center; margin-top: 0.4rem; }
    .cost { font-weight: 700; color: var(--accent); font-size: 0.9rem; }
    .links { display: flex; gap: 0.6rem; }
    .links a {
      display: flex; align-items: center; gap: 3px;
      color: var(--primary); text-decoration: none; font-size: 0.75rem; font-weight: 600;
      padding: 0.25rem 0.5rem; border-radius: 8px; background: rgba(107,163,190,0.1);
    }

    .map-container { height: 280px; margin: 0.75rem 1rem; border-radius: var(--radius); overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }

    .sub-content { display: none; }
    .sub-content.active { display: block; }

    .budget-card {
      background: var(--card); border-radius: var(--radius);
      padding: 1.2rem; margin: 0.75rem 1rem;
      box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    .budget-card h3 { font-size: 1rem; margin-bottom: 0.8rem; color: var(--text); }
    .budget-total {
      background: linear-gradient(135deg, var(--primary), var(--primary-light));
      color: white; padding: 1.5rem; border-radius: var(--radius);
      margin: 0.75rem 1rem; text-align: center;
    }
    .budget-total .amount { font-size: 2rem; font-weight: 700; font-family: 'Playfair Display', serif; }
    .budget-total .label { font-size: 0.85rem; opacity: 0.9; }
    .budget-row { display: flex; justify-content: space-between; padding: 0.6rem 0; border-bottom: 1px solid #f0f0f0; font-size: 0.88rem; }
    .budget-row:last-child { border-bottom: none; }
    .budget-row .cat { color: var(--text); }
    .budget-row .amt { font-weight: 700; color: var(--accent); }
    .budget-row .pct { font-size: 0.75rem; color: var(--muted); margin-left: 0.5rem; }
    .tip-card {
      background: #FEF7F0; border-left: 3px solid var(--secondary);
      padding: 0.8rem 1rem; margin: 0.5rem 1rem; border-radius: 0 var(--radius) var(--radius) 0;
      font-size: 0.85rem;
    }

    .leaflet-popup-content { font-family: 'Inter', sans-serif; font-size: 0.82rem; }
    .leaflet-popup-content b { color: var(--text); }
    .leaflet-popup-content a { color: var(--primary); }

    @media (min-width: 768px) {
      .venue-cards-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
      .hero h1 { font-size: 3rem; }
    }
  </style>
</head>
<body>

  <header class="hero">
    <h1 id="hero-title"></h1>
    <p id="hero-tagline"></p>
    <span class="date-badge" id="hero-dates"></span>
    <div class="wave">
      <svg viewBox="0 0 1200 40" preserveAspectRatio="none">
        <path d="M0,20 C300,40 900,0 1200,20 L1200,40 L0,40Z" fill="#F7FBFD"/>
      </svg>
    </div>
  </header>

  <main>
    <section id="tab-itinerary" class="tab-content active"></section>
    <section id="tab-explore" class="tab-content"></section>
    <section id="tab-budget" class="tab-content"></section>
  </main>

  <nav class="bottom-nav">
    <button class="active" onclick="switchTab('itinerary')" id="nav-itinerary">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
      Itinerary
    </button>
    <button onclick="switchTab('explore')" id="nav-explore">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 10-16 0c0 3 2.7 7 8 11.7z"/></svg>
      Explore
    </button>
    <button onclick="switchTab('budget')" id="nav-budget">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
      Budget
    </button>
  </nav>

<script>
// ==================== DATA (injected by Voyage Agents) ====================
const TRIP_DATA = {{TRIP_DATA}};

// ==================== TAG HELPERS ====================
const TAG_CLASSES = {
  'restaurant': 'tag-food', 'cafe': 'tag-food', 'food': 'tag-food', 'Food': 'tag-food',
  'Brunch': 'tag-food', 'Coffee': 'tag-food', 'Healthy': 'tag-food', 'Street Food': 'tag-food',
  'bar': 'tag-nightlife', 'nightlife': 'tag-nightlife', 'beach_club': 'tag-nightlife',
  'Nightlife': 'tag-nightlife', 'Cocktails': 'tag-nightlife', 'DJ': 'tag-nightlife', 'Party': 'tag-nightlife',
  'beach': 'tag-beach', 'Beach': 'tag-beach', 'Surf': 'tag-beach', 'Ocean': 'tag-beach',
  'Pool': 'tag-beach', 'Sunset': 'tag-beach', 'Beachfront': 'tag-beach',
  'activity': 'tag-activity', 'cultural': 'tag-activity', 'wellness': 'tag-activity',
  'Adventure': 'tag-activity', 'Temple': 'tag-activity', 'Tour': 'tag-activity', 'Yoga': 'tag-activity',
  'Hiking': 'tag-activity', 'Diving': 'tag-activity', 'Snorkeling': 'tag-activity',
  'Local': 'tag-local', 'Authentic': 'tag-local', 'Local favorite': 'tag-local', 'Hidden gem': 'tag-local',
  'Aesthetic': 'tag-aesthetic', 'Trendy': 'tag-aesthetic', 'Instagram': 'tag-aesthetic',
  'Rooftop': 'tag-aesthetic', 'Chic': 'tag-aesthetic', 'Upscale': 'tag-aesthetic',
};
function getTagClass(tag) { return TAG_CLASSES[tag] || 'tag-activity'; }

function starRating(r) {
  if (!r) return '';
  const full = Math.floor(r);
  let s = '';
  for (let i = 0; i < full; i++) s += '★';
  if (r - full >= 0.5) s += '½';
  return s + ' ' + r;
}

// ==================== RENDER ITINERARY ====================
function renderItinerary() {
  const container = document.getElementById('tab-itinerary');
  container.innerHTML = '<h2 class="section-title">Your Itinerary</h2>';
  TRIP_DATA.days.forEach((day, idx) => {
    const isOpen = idx === 0 ? ' open' : '';
    let slotsHtml = '';
    (day.slots || []).forEach(slot => {
      const hl = slot.highlight ? ' highlight' : '';
      const note = slot.note ? '<div class="slot-note">' + slot.note + '</div>' : '';
      const venue = slot.venue ? ' — ' + slot.venue : '';
      slotsHtml += '<div class="time-slot' + hl + '">'
        + '<div class="slot-time">' + (slot.time || '') + '</div>'
        + '<div><div class="slot-activity">' + (slot.activity || '') + venue + '</div>' + note + '</div>'
        + '</div>';
    });
    container.innerHTML += '<div class="day-card' + isOpen + '" onclick="this.classList.toggle(\'open\')">'
      + '<div class="day-header">'
      + '<div class="day-emoji">' + (day.emoji || '📅') + '</div>'
      + '<div class="day-info"><div class="day-label">Day ' + (idx + 1) + (day.date ? ' — ' + day.date : '') + '</div>'
      + '<div class="day-title">' + (day.title || 'Day ' + (idx + 1)) + '</div></div>'
      + '<div class="day-chevron">▼</div></div>'
      + '<div class="day-slots">' + slotsHtml + '</div></div>';
  });
}

// ==================== RENDER EXPLORE ====================
function renderExplore() {
  const container = document.getElementById('tab-explore');
  const categories = {};
  (TRIP_DATA.venues || []).forEach(v => {
    const cat = v.type || 'other';
    let label;
    if (['restaurant','cafe'].includes(cat)) label = 'Food & Cafes';
    else if (['bar','nightlife','beach_club'].includes(cat)) label = 'Bars & Nightlife';
    else if (['activity','cultural','wellness'].includes(cat)) label = 'Activities';
    else if (['beach','viewpoint'].includes(cat)) label = 'Beaches & Nature';
    else label = 'Other';
    if (!categories[label]) categories[label] = [];
    categories[label].push(v);
  });
  const catKeys = Object.keys(categories);

  let subTabsHtml = '<div class="sub-tabs">';
  catKeys.forEach((key, i) => {
    subTabsHtml += '<button class="sub-tab' + (i === 0 ? ' active' : '') + '" onclick="switchSubTab(this, \'' + key + '\')">' + key + '</button>';
  });
  subTabsHtml += '<button class="sub-tab" onclick="switchSubTab(this, \'map\')">Map</button></div>';
  container.innerHTML = subTabsHtml;

  catKeys.forEach((key, i) => {
    let html = '<div class="sub-content' + (i === 0 ? ' active' : '') + '" data-sub="' + key + '"><div class="venue-cards-grid">';
    categories[key].forEach(v => {
      const hl = v.highlight ? ' highlight' : '';
      const tagsHtml = (v.tags || []).map(t => '<span class="tag ' + getTagClass(t) + '">' + t + '</span>').join('');
      const dest = TRIP_DATA.destination || '';
      const mapsUrl = v.coords ? 'https://www.google.com/maps?q=' + v.coords[0] + ',' + v.coords[1] : '#';
      const searchUrl = 'https://www.google.com/search?q=' + encodeURIComponent(v.name + ' ' + dest);
      html += '<div class="venue-card' + hl + '">'
        + '<div style="display:flex;justify-content:space-between;align-items:baseline;">'
        + '<div class="venue-name">' + v.name + '</div>'
        + '<div class="venue-rating">' + starRating(v.rating) + '</div></div>'
        + '<div class="venue-area">' + (v.area || '') + '</div>'
        + '<div class="tags">' + tagsHtml + '</div>'
        + (v.description ? '<div class="venue-desc">' + v.description + '</div>' : '')
        + '<div class="venue-bottom">'
        + '<div class="cost">' + (v.cost || '') + '</div>'
        + '<div class="links">'
        + '<a href="' + mapsUrl + '" target="_blank">📍 Map</a>'
        + '<a href="' + searchUrl + '" target="_blank">🔍 Search</a>'
        + '</div></div></div>';
    });
    html += '</div></div>';
    container.innerHTML += html;
  });

  // Map sub-content
  container.innerHTML += '<div class="sub-content" data-sub="map"><div class="map-container" id="main-map"></div></div>';
}

// ==================== RENDER BUDGET ====================
function renderBudget() {
  const container = document.getElementById('tab-budget');
  const b = TRIP_DATA.budget || {};

  container.innerHTML = '<div class="budget-total">'
    + '<div class="amount">' + (b.total_per_person || 'N/A') + '</div>'
    + '<div class="label">estimated per person</div>'
    + (b.verdict ? '<div style="margin-top:0.5rem;font-size:0.85rem;opacity:0.9;">' + b.verdict + '</div>' : '')
    + '</div>';

  if (b.categories && b.categories.length) {
    let rows = '';
    b.categories.forEach(c => {
      rows += '<div class="budget-row"><span class="cat">' + c.name + '</span>'
        + '<span><span class="amt">' + c.cost + '</span>'
        + (c.percent ? '<span class="pct">' + c.percent + '</span>' : '')
        + '</span></div>';
    });
    container.innerHTML += '<div class="budget-card"><h3>Breakdown</h3>' + rows + '</div>';
  }

  if (b.splurge && b.splurge.length) {
    let html = '<div class="budget-card"><h3>💎 Worth the Splurge</h3>';
    b.splurge.forEach(s => { html += '<div style="padding:0.3rem 0;font-size:0.85rem;">• ' + s + '</div>'; });
    container.innerHTML += html + '</div>';
  }

  if (b.saves && b.saves.length) {
    let html = '<div class="budget-card"><h3>💰 Easy Saves</h3>';
    b.saves.forEach(s => { html += '<div style="padding:0.3rem 0;font-size:0.85rem;">• ' + s + '</div>'; });
    container.innerHTML += html + '</div>';
  }

  if (b.tips && b.tips.length) {
    b.tips.forEach(tip => {
      container.innerHTML += '<div class="tip-card">💡 ' + tip + '</div>';
    });
  }
}

// ==================== MAP ====================
let mapInitialized = false;
function initMap() {
  if (mapInitialized) return;
  const mapEl = document.getElementById('main-map');
  if (!mapEl) return;
  mapInitialized = true;

  const venues = TRIP_DATA.venues || [];
  const validVenues = venues.filter(v => v.coords && v.coords.length === 2);
  if (validVenues.length === 0) return;

  const map = L.map('main-map').setView(validVenues[0].coords, 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
  }).addTo(map);

  const colorMap = {
    'restaurant': '#5A8F6A', 'cafe': '#5A8F6A', 'food': '#5A8F6A',
    'bar': '#8B7BB8', 'nightlife': '#8B7BB8', 'beach_club': '#8B7BB8',
    'activity': '#C48B5C', 'cultural': '#C48B5C', 'wellness': '#C48B5C',
    'beach': '#6BA3BE', 'viewpoint': '#6BA3BE',
  };

  const bounds = [];
  validVenues.forEach(v => {
    const color = colorMap[v.type] || '#8A9BAA';
    const marker = L.circleMarker(v.coords, { radius: 7, fillColor: color, color: '#fff', weight: 2, fillOpacity: 0.9 }).addTo(map);
    const tagsStr = (v.tags || []).join(', ');
    const dest = TRIP_DATA.destination || '';
    marker.bindPopup('<b>' + v.name + '</b><br>' + tagsStr + '<br>' + (v.cost || '')
      + '<br><a href="https://www.google.com/maps?q=' + v.coords[0] + ',' + v.coords[1] + '" target="_blank">Open in Maps</a>'
      + ' | <a href="https://www.google.com/search?q=' + encodeURIComponent(v.name + ' ' + dest) + '" target="_blank">Search</a>');
    bounds.push(v.coords);
  });
  if (bounds.length > 1) map.fitBounds(bounds, { padding: [30, 30] });
}

// ==================== TAB SWITCHING ====================
function switchTab(tab) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.bottom-nav button').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  document.getElementById('nav-' + tab).classList.add('active');
  if (tab === 'explore') setTimeout(initMap, 100);
}

function switchSubTab(btn, key) {
  const parent = btn.closest('.tab-content');
  parent.querySelectorAll('.sub-tab').forEach(el => el.classList.remove('active'));
  parent.querySelectorAll('.sub-content').forEach(el => el.classList.remove('active'));
  btn.classList.add('active');
  const target = parent.querySelector('[data-sub="' + key + '"]');
  if (target) target.classList.add('active');
  if (key === 'map') setTimeout(initMap, 100);
}

// ==================== INIT ====================
document.getElementById('hero-title').textContent = TRIP_DATA.destination || 'Trip Guide';
document.getElementById('hero-tagline').textContent = TRIP_DATA.tagline || '';
document.getElementById('hero-dates').textContent = TRIP_DATA.dates || '';
document.title = (TRIP_DATA.destination || 'Trip') + ' Travel Guide';

renderItinerary();
renderExplore();
renderBudget();
</script>
</body>
</html>"""
