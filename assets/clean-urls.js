(() => {
  const ORIGIN = 'https://sports.alexlford.com';

  function encode(value) {
    return encodeURIComponent(String(value || '').trim());
  }

  function cleanPathForLegacy(rawHref) {
    if (!rawHref || rawHref.startsWith('#') || rawHref.startsWith('mailto:') || rawHref.startsWith('tel:') || rawHref.startsWith('javascript:')) return null;
    let url;
    try { url = new URL(rawHref, location.href); } catch (_) { return null; }
    if (url.origin !== location.origin) return null;

    const file = (url.pathname.split('/').pop() || '').toLowerCase();
    const p = url.searchParams;
    let path = null;

    if (file === '' || file === 'index.html') path = '/';
    else if (file === 'about.html') path = '/about/';
    else if (file === 'annuals.html') path = '/years/';
    else if (file === 'year.html' && p.get('y')) path = `/years/${encode(p.get('y'))}/`;
    else if (file === 'event.html' && p.get('id')) path = `/events/${encode(p.get('id'))}/`;
    else if (file === 'teams.html') path = '/teams/';
    else if (file === 'team-profile.html' && p.get('t')) path = `/teams/${encode(p.get('t'))}/`;
    else if (file === 'venues.html') path = '/venues/';
    else if (file === 'venue-profile.html' && p.get('v')) path = `/venues/${encode(p.get('v'))}/`;
    else if (file === 'geography.html') path = '/geography/';
    else if (file === 'venue-map.html') path = '/geography/map/';
    else if (file === 'journeys.html') path = '/journeys/';
    else if (file === 'journey-profile.html' && p.get('j')) path = `/journeys/${encode(p.get('j'))}/`;
    else if (file === 'phase.html' && p.get('p')) path = `/chapters/${encode(p.get('p'))}/`;
    else if (file === 'favorites.html') path = '/favorites/';
    else if (file === 'lifetime-analytics.html') path = '/analytics/';
    else if (file === 'hall-of-fame.html') path = '/hall-of-fame/';

    return path ? `${path}${url.hash || ''}` : null;
  }

  function rewriteAnchor(anchor) {
    if (!(anchor instanceof HTMLAnchorElement)) return;
    const raw = anchor.getAttribute('href');
    const clean = cleanPathForLegacy(raw);
    if (clean && raw !== clean) anchor.setAttribute('href', clean);
  }

  function rewriteLinks(root = document) {
    if (root instanceof HTMLAnchorElement) rewriteAnchor(root);
    root.querySelectorAll?.('a[href]').forEach(rewriteAnchor);
  }

  function setCanonicalToCurrentCleanPath() {
    const pathname = location.pathname === '/index.html' ? '/' : location.pathname;
    const clean = `${ORIGIN}${pathname}`;
    let canonical = document.head.querySelector('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.rel = 'canonical';
      document.head.appendChild(canonical);
    }
    canonical.href = clean;
    const og = document.head.querySelector('meta[property="og:url"]');
    if (og) og.setAttribute('content', clean);
  }

  function boot() {
    rewriteLinks(document);
    if (location.pathname === '/' || window.SPORTS_CLEAN_ROUTE) setCanonicalToCurrentCleanPath();
    const observer = new MutationObserver(mutations => {
      for (const mutation of mutations) {
        if (mutation.type === 'attributes' && mutation.target instanceof HTMLAnchorElement) rewriteAnchor(mutation.target);
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) rewriteLinks(node);
        });
      }
    });
    observer.observe(document.documentElement, {subtree:true, childList:true, attributes:true, attributeFilter:['href']});
  }

  window.SportsPassportCleanUrls = { cleanPathForLegacy, rewriteLinks };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})();
