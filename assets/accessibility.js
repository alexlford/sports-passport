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

  async function enhanceArchiveFreshness() {
    const footer = document.querySelector('.site-footer');
    if (!footer || footer.dataset.archiveFreshnessReady === 'true' || footer.dataset.archiveFreshnessLoading === 'true') return;
    const D = window.SportsPassportData;
    if (!D?.load) return;
    footer.dataset.archiveFreshnessLoading = 'true';
    try {
      const [events, config, manifestResponse] = await Promise.all([
        D.load('events'),
        D.load('config'),
        fetch('/data/cache-manifest.json', { cache: 'no-cache' })
      ]);
      const manifest = manifestResponse.ok ? await manifestResponse.json() : null;
      const dates = events.map(event => event.date).filter(date => /^\d{4}-\d{2}-\d{2}$/.test(date)).sort();
      const latest = dates.at(-1);
      if (!latest) return;
      const formatted = new Intl.DateTimeFormat('en-US', {
        month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC'
      }).format(new Date(`${latest}T00:00:00Z`));
      const revision = String(manifest?.version || '').slice(0, 8);
      const freshness = document.createElement('span');
      freshness.className = 'archive-freshness';
      freshness.textContent = `Archive through ${formatted} · ${config.version}${revision ? ` · rev ${revision}` : ''}`;
      freshness.title = revision ? `Data revision ${manifest.version}` : 'Sports Passport archive version';
      const firstLink = footer.querySelector('a');
      if (firstLink) footer.insertBefore(freshness, firstLink);
      else footer.appendChild(freshness);
      footer.dataset.archiveFreshnessReady = 'true';
    } catch (_) {
      // Freshness metadata is supplementary; leave the footer usable if it cannot load.
    } finally {
      delete footer.dataset.archiveFreshnessLoading;
    }
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

  function replaceTextNodes(root, replacements) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(node => {
      let value = node.nodeValue;
      replacements.forEach(([pattern, replacement]) => { value = value.replace(pattern, replacement); });
      if (value !== node.nodeValue) node.nodeValue = value;
    });
  }

  function removeInternalArchiveMetadata() {
    const routeSource = String(window.SPORTS_ROUTE_SOURCE || '');
    const path = location.pathname.toLowerCase();
    const isEventPassport = routeSource === 'event.html' || /(^|\/)event\.html$/.test(path) || /^\/events\/[^/]+\/?$/.test(path);
    const isYear = routeSource === 'year.html' || /^\/years\/\d+\/?$/.test(path);
    const isAbout = routeSource === 'about.html' || /^\/about\/?$/.test(path);
    const isSearch = routeSource === 'search.html' || /^\/search\/?$/.test(path);
    const isAnalytics = routeSource === 'lifetime-analytics.html' || /^\/analytics\/?$/.test(path);

    if (isEventPassport) {
      const internalLabels = new Set(['Archive confidence', 'Evidence class', 'Evidence provenance', 'Event ID']);
      document.querySelectorAll('.record-row').forEach(row => {
        const label = row.querySelector(':scope > span')?.textContent?.trim();
        if (internalLabels.has(label)) row.remove();
      });
      document.querySelectorAll('.status-row .status-chip:not(.top10)').forEach(chip => chip.remove());
      document.querySelectorAll('.status-row').forEach(row => {
        if (!row.querySelector('.status-chip')) row.remove();
      });
    }

    // Confidence and provenance are internal archive bookkeeping. Keep the data,
    // but remove those classifications from every visitor-facing archive surface.
    document.querySelectorAll('.confidence-note, .year-card .confidence').forEach(element => element.remove());
    document.querySelectorAll('.method-note').forEach(note => {
      if (/confidence|\bverified\b|\bnotional\b|confirmed\s*\/\s*documented/i.test(note.textContent || '')) note.remove();
    });
    document.querySelectorAll('.event-card .badge, .event-confidence').forEach(chip => {
      if (/^(Verified|Notional|Documented)$/i.test(chip.textContent?.trim() || '')) chip.remove();
    });

    document.querySelectorAll('.stat').forEach(stat => {
      const label = stat.querySelector('span');
      const text = label?.textContent?.trim();
      if (text === 'Confirmed / documented') stat.remove();
      else if (text === 'Confirmed record') label.textContent = 'Record';
    });

    if (isYear) {
      const deck = document.querySelector('.hero .deck');
      if (deck && /This reconstructed early edition contains/i.test(deck.textContent || '')) {
        deck.textContent = deck.textContent.replace(/\s*This reconstructed early edition contains.*$/i, '');
      }
      document.querySelectorAll('.section .head p').forEach(paragraph => {
        if (/Early records are labeled Verified or Notional/i.test(paragraph.textContent || '')) {
          paragraph.textContent = 'Recent games appear first. Team and venue names connect directly into the broader archive.';
        }
      });
    }

    if (isAbout) {
      document.querySelectorAll('.confidence-band').forEach(band => band.closest('.section')?.remove());
      const description = document.querySelector('meta[name="description"]');
      if (description && /archive confidence/i.test(description.content || '')) {
        description.content = 'How Alex Ford’s Sports Passport is organized: annual editions, life chapters, favorite teams, venue rankings, and editorial methodology.';
      }
    }

    if (isSearch) {
      const explainer = document.querySelector('.search-heading > p');
      if (explainer && /event ID|confidence rules/i.test(explainer.textContent || '')) {
        explainer.textContent = 'Try a team, stadium, city, year, or sport. Filters narrow the same archive without exposing internal bookkeeping.';
      }
    }

    if (isAnalytics) {
      const deck = document.querySelector('.hero .deck');
      if (deck && /early-record confidence remains explicit/i.test(deck.textContent || '')) {
        deck.textContent = deck.textContent.replace(/,?\s*while early-record confidence remains explicit\.?/i, '.');
      }
      document.querySelectorAll('.density-note').forEach(note => {
        if (/notional/i.test(note.textContent || '')) note.textContent = 'Tap a team to open its dossier.';
      });
      replaceTextNodes(document.querySelector('#app'), [
        [/\bFirst confirmed event\b/g, 'First event'],
        [/\bLatest confirmed event\b/g, 'Latest event'],
        [/\bNo confirmed events\b/gi, 'No events'],
        [/\bconfirmed\/documented records\b/gi, 'archive records'],
        [/\bconfirmed\/documented archive\b/gi, 'archive'],
        [/\bconfirmed venue visits\b/gi, 'venue visits'],
        [/\bconfirmed venues\b/gi, 'venues'],
        [/\bconfirmed scores\b/gi, 'recorded scores'],
        [/\bconfirmed records\b/gi, 'archive records'],
        [/\bconfirmed events\b/gi, 'events'],
        [/\bconfirmed event\b/gi, 'event'],
        [/\bdocumented timeline\b/gi, 'timeline']
      ]);
    }
  }

  function runEnhancements() {
    ensureSkipLink();
    enhanceMenuKeyboard();
    enhanceTeamThemeContrast();
    enhanceLiveTeamCount();
    enhanceArchiveFreshness();
    enhanceMapFilters();
    enhanceMapTextAlternative();
    removeInternalArchiveMetadata();
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
