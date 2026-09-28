(() => {
  const WHITE = '#ffffff';

  function parseHex(hex) {
    const value = String(hex || '').trim();
    const short = /^#([0-9a-f]{3})$/i.exec(value);
    const full = /^#([0-9a-f]{6})$/i.exec(value);
    if (short) return short[1].split('').map(ch => parseInt(ch + ch, 16));
    if (full) return [0, 2, 4].map(i => parseInt(full[1].slice(i, i + 2), 16));
    return null;
  }

  function luminance(hex) {
    const rgb = parseHex(hex);
    if (!rgb) return null;
    const linear = rgb.map(v => {
      const c = v / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
  }

  function contrastRatio(a, b) {
    const la = luminance(a), lb = luminance(b);
    if (la == null || lb == null) return 1;
    const lighter = Math.max(la, lb), darker = Math.min(la, lb);
    return (lighter + 0.05) / (darker + 0.05);
  }

  function darken(hex, factor) {
    const rgb = parseHex(hex);
    if (!rgb) return '#112b3c';
    return '#' + rgb.map(v => Math.max(0, Math.min(255, Math.round(v * factor))).toString(16).padStart(2, '0')).join('');
  }

  function accessibleThemeColor(hex, minRatio = 4.5) {
    let color = parseHex(hex) ? hex : '#112b3c';
    let ratio = contrastRatio(color, WHITE);
    let factor = 0.9;
    while (ratio < minRatio && factor >= 0.2) {
      color = darken(hex, factor);
      ratio = contrastRatio(color, WHITE);
      factor -= 0.1;
    }
    if (ratio < minRatio) {
      color = '#112b3c';
      ratio = contrastRatio(color, WHITE);
    }
    return { color, ratio };
  }

  function ensureSkipLink() {
    const main = document.querySelector('main');
    if (!main || document.querySelector('.skip-link')) return;
    if (!main.id) main.id = 'main-content';
    if (!main.hasAttribute('tabindex')) main.setAttribute('tabindex', '-1');
    const link = document.createElement('a');
    link.className = 'skip-link';
    link.href = `#${main.id}`;
    link.textContent = 'Skip to main content';
    document.body.insertBefore(link, document.body.firstChild);
  }

  function enhanceMenuKeyboard() {
    const header = document.querySelector('.site-header');
    const toggle = header?.querySelector('.menu-toggle');
    if (!header || !toggle || header.dataset.keyboardMenuReady === 'true') return;
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || !header.classList.contains('menu-open')) return;
      header.classList.remove('menu-open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = 'Menu';
      toggle.focus();
    });
    header.dataset.keyboardMenuReady = 'true';
  }

  function enhanceTeamThemeContrast(root = document) {
    root.querySelectorAll?.('.team-theme').forEach(theme => {
      if (theme.dataset.contrastChecked === 'true') return;
      const raw = getComputedStyle(theme).getPropertyValue('--team-bg').trim();
      const accessible = accessibleThemeColor(raw);
      theme.style.setProperty('--team-bg', accessible.color);
      theme.dataset.contrastRatio = accessible.ratio.toFixed(2);
      theme.dataset.contrastChecked = 'true';
    });
  }

  function enhanceLiveTeamCount() {
    const cards = document.querySelector('#cards');
    const query = document.querySelector('#q');
    const filters = document.querySelector('#filters');
    if (!cards || !query || !filters || document.querySelector('#team-filter-status')) return;
    const status = document.createElement('div');
    status.id = 'team-filter-status';
    status.className = 'filter-live-status';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    status.setAttribute('aria-atomic', 'true');
    cards.before(status);
    const update = () => {
      const count = cards.querySelectorAll('.team-card').length;
      status.textContent = `${count} team${count === 1 ? '' : 's'} shown.`;
    };
    new MutationObserver(update).observe(cards, { childList: true });
    update();
  }

  async function enhanceMapTextAlternative() {
    const mapElement = document.querySelector('#geo-map, #map');
    if (!mapElement || document.querySelector('.map-text-alternative')) return;
    const D = window.SportsPassportData;
    if (!D?.load) return;
    let events, venues;
    try {
      [events, venues] = await Promise.all([D.load('events'), D.load('venues')]);
    } catch (_) {
      return;
    }
    const mapped = venues
      .filter(v => Number.isFinite(v.latitude) && Number.isFinite(v.longitude))
      .sort((a, b) => `${a.city} ${a.display_name}`.localeCompare(`${b.city} ${b.display_name}`));
    const details = document.createElement('details');
    details.className = 'map-text-alternative';
    const summary = document.createElement('summary');
    summary.textContent = `Text alternative: ${mapped.length} mapped venues`;
    const list = document.createElement('ul');
    mapped.forEach(venue => {
      const visits = D.venueEvents(events, venue.key).length;
      const li = document.createElement('li');
      const link = document.createElement('a');
      link.href = `/venues/${encodeURIComponent(venue.slug)}/`;
      link.textContent = venue.display_name;
      li.append(link, document.createTextNode(` — ${venue.city}; ${visits} archive visit${visits === 1 ? '' : 's'}`));
      list.appendChild(li);
    });
    details.append(summary, list);
    const container = mapElement.closest('.geo-map-card, .atlas-shell') || mapElement.parentElement;
    container?.appendChild(details);
  }

  function runEnhancements() {
    ensureSkipLink();
    enhanceMenuKeyboard();
    enhanceTeamThemeContrast();
    enhanceLiveTeamCount();
    enhanceMapTextAlternative();
  }

  const observer = new MutationObserver(() => runEnhancements());
  function boot() {
    runEnhancements();
    observer.observe(document.body, { childList: true, subtree: true });
  }

  window.SportsPassportAccessibility = { contrastRatio, accessibleThemeColor, runEnhancements };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
