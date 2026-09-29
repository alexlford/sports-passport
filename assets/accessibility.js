(() => {
  const WHITE = '#ffffff';
  const mapFilterState = new WeakMap();

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

  function archiveLoadFailure(reason) {
    const message = String(reason?.message || reason || '');
    return /Could not load|Failed to fetch|NetworkError|Load failed/i.test(message);
  }

  function showDataLoadError(reason) {
    if (document.querySelector('.data-load-error')) return;
    const main = document.querySelector('main');
    if (!main) return;
    const panel = document.createElement('section');
    panel.className = 'data-load-error';
    panel.setAttribute('role', 'alert');
    panel.setAttribute('aria-live', 'assertive');
    panel.innerHTML = '<div class="data-load-error__kicker">Archive unavailable</div><h1>That page’s data did not load.</h1><p>The navigation still works. Try the request again, or return to the Sports Passport home page.</p><div class="data-load-error__actions"><button type="button" class="data-load-retry">Try again</button><a href="/">Go to Sports Passport home</a></div>';
    panel.querySelector('.data-load-retry')?.addEventListener('click', () => location.reload());
    const header = main.querySelector(':scope > .site-header, :scope > header');
    if (header) header.insertAdjacentElement('afterend', panel);
    else main.prepend(panel);
    panel.querySelector('h1')?.setAttribute('tabindex', '-1');
    panel.querySelector('h1')?.focus();
    panel.dataset.reason = String(reason?.message || reason || 'archive-data-load-failure').slice(0, 160);
  }

  function updateMapFilter(mapElement) {
    const rankedOnly = mapElement.dataset.venueFilter === 'ranked';
    const markers = [...mapElement.querySelectorAll('.leaflet-marker-icon')];
    let visible = 0;
    markers.forEach(marker => {
      const ranked = Boolean(marker.querySelector('.venue-marker.ranked'));
      const shouldHide = rankedOnly && !ranked;
      if (marker.hidden !== shouldHide) marker.hidden = shouldHide;
      if (!shouldHide) visible += 1;
    });

    const shell = mapElement.closest('.geo-map-card, .atlas-shell');
    const controls = shell?.querySelector('.map-filter-controls');
    controls?.querySelectorAll('button[data-map-filter]').forEach(button => {
      const active = button.dataset.mapFilter === (rankedOnly ? 'ranked' : 'all');
      const pressed = String(active);
      if (button.getAttribute('aria-pressed') !== pressed) button.setAttribute('aria-pressed', pressed);
      if (button.classList.contains('active') !== active) button.classList.toggle('active', active);
    });

    const status = controls?.querySelector('.map-filter-status');
    const statusText = `${visible} of ${markers.length} venues shown`;
    if (status && markers.length && status.textContent !== statusText) status.textContent = statusText;
    mapFilterState.set(mapElement, { markerCount: markers.length, filter: rankedOnly ? 'ranked' : 'all' });
  }

  function enhanceMapFilters() {
    document.querySelectorAll('#geo-map, #map').forEach(mapElement => {
      const shell = mapElement.closest('.geo-map-card, .atlas-shell');
      const toolbar = shell?.querySelector('.geo-map-toolbar, .atlas-toolbar');
      if (!shell || !toolbar) return;

      let controls = toolbar.querySelector('.map-filter-controls');
      let created = false;
      if (!controls) {
        created = true;
        controls = document.createElement('div');
        controls.className = 'map-filter-controls';
        controls.setAttribute('role', 'group');
        controls.setAttribute('aria-label', 'Venue map filter');
        controls.innerHTML = '<button type="button" data-map-filter="all" aria-pressed="true">All venues</button><button type="button" data-map-filter="ranked" aria-pressed="false">Top 10 only</button><span class="map-filter-status" role="status" aria-live="polite"></span>';
        const reset = toolbar.querySelector('#reset-map');
        if (reset) toolbar.insertBefore(controls, reset);
        else toolbar.appendChild(controls);
        controls.querySelectorAll('button[data-map-filter]').forEach(button => button.addEventListener('click', () => {
          mapElement.dataset.venueFilter = button.dataset.mapFilter;
          updateMapFilter(mapElement);
        }));
      }

      if (!mapElement.dataset.venueFilter) mapElement.dataset.venueFilter = 'all';
      const state = mapFilterState.get(mapElement);
      const markerCount = mapElement.querySelectorAll('.leaflet-marker-icon').length;
      const filter = mapElement.dataset.venueFilter;
      if (created || !state || state.markerCount !== markerCount || state.filter !== filter) {
        updateMapFilter(mapElement);
      }
    });
  }

  async function enhanceMapTextAlternative() {
    const mapElement = document.querySelector('#geo-map, #map');
    if (!mapElement || document.querySelector('.map-text-alternative') || mapElement.dataset.textAlternativeLoading === 'true') return;
    const D = window.SportsPassportData;
    if (!D?.load) return;
    mapElement.dataset.textAlternativeLoading = 'true';
    let events, venues;
    try {
      [events, venues] = await Promise.all([D.load('events'), D.load('venues')]);
    } catch (_) {
      delete mapElement.dataset.textAlternativeLoading;
      return;
    }
    if (document.querySelector('.map-text-alternative')) {
      delete mapElement.dataset.textAlternativeLoading;
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
    delete mapElement.dataset.textAlternativeLoading;
  }

  function runEnhancements() {
    ensureSkipLink();
    enhanceMenuKeyboard();
    enhanceTeamThemeContrast();
    enhanceLiveTeamCount();
    enhanceMapFilters();
    enhanceMapTextAlternative();
  }

  window.addEventListener('unhandledrejection', event => {
    if (!archiveLoadFailure(event.reason)) return;
    showDataLoadError(event.reason);
    event.preventDefault();
  });
  window.addEventListener('error', event => {
    if (!archiveLoadFailure(event.error || event.message)) return;
    showDataLoadError(event.error || event.message);
  });

  const observer = new MutationObserver(() => runEnhancements());
  function boot() {
    runEnhancements();
    observer.observe(document.body, { childList: true, subtree: true });
  }

  window.SportsPassportAccessibility = { contrastRatio, accessibleThemeColor, runEnhancements, showDataLoadError, updateMapFilter };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
