(() => {
  const ORIGIN = 'https://sports.alexlford.com';
  const CLEAN_ROUTE_PREFIXES = [
    '/about/','/artifacts/','/years/','/events/','/teams/','/venues/','/geography/',
    '/journeys/','/chapters/','/favorites/','/analytics/','/hall-of-fame/'
  ];

  function encode(value) {
    return encodeURIComponent(String(value || '').trim());
  }

  function withHash(path, hash) {
    return `${path}${hash || ''}`;
  }

  function isCleanPublicRoute(url) {
    return CLEAN_ROUTE_PREFIXES.some(prefix => url.pathname === prefix || url.pathname.startsWith(prefix));
  }

  function cleanPathForLegacy(rawHref) {
    if (!rawHref || rawHref.startsWith('#') || rawHref.startsWith('mailto:') || rawHref.startsWith('tel:') || rawHref.startsWith('javascript:')) return null;
    let url;
    try { url = new URL(rawHref, location.href); } catch (_) { return null; }
    if (url.origin !== location.origin) return null;

    // Clean section routes are already canonical. Preserve their path and descriptive query keys
    // rather than allowing the trailing slash to be mistaken for the archive home page.
    if (isCleanPublicRoute(url)) return `${url.pathname}${url.search}${url.hash}`;

    const file = (url.pathname.split('/').pop() || '').toLowerCase();
    const p = url.searchParams;
    let path = null;

    if (url.pathname === '/' || file === 'index.html') path = '/';
    else if (file === 'about.html') path = '/about/';
    else if (file === 'artifacts.html') path = '/artifacts/';
    else if (file === 'annuals.html') path = '/years/';
    else if (file === 'year.html' && p.get('y')) path = `/years/?year=${encode(p.get('y'))}`;
    else if (file === 'event.html' && p.get('id')) path = `/events/?event=${encode(p.get('id'))}`;
    else if (file === 'teams.html') path = '/teams/';
    else if (file === 'team-profile.html' && p.get('t')) path = `/teams/?team=${encode(p.get('t'))}`;
    else if (file === 'venues.html') path = '/venues/';
    else if (file === 'venue-profile.html' && p.get('v')) path = `/venues/?venue=${encode(p.get('v'))}`;
    else if (file === 'geography.html') path = '/geography/';
    else if (file === 'venue-map.html') path = '/geography/map/';
    else if (file === 'journeys.html') path = '/journeys/';
    else if (file === 'journey-profile.html' && p.get('j')) path = `/journeys/?journey=${encode(p.get('j'))}`;
    else if (file === 'phase.html' && p.get('p')) path = `/chapters/?chapter=${encode(p.get('p'))}`;
    else if (file === 'favorites.html') path = '/favorites/';
    else if (file === 'lifetime-analytics.html') path = '/analytics/';
    else if (file === 'hall-of-fame.html') path = '/hall-of-fame/';

    return path ? withHash(path, url.hash) : null;
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

  function ensureArtifactsNav() {
    const nav = document.querySelector('#global-nav,.global-nav');
    if (!nav) return;
    let link = nav.querySelector('a[data-artifacts-nav]');
    if (!link) {
      link = document.createElement('a');
      link.href = '/artifacts/';
      link.textContent = 'Artifacts';
      link.dataset.artifactsNav = 'true';
      const external = nav.querySelector('a.external');
      nav.insertBefore(link, external || null);
    }
    const active = location.pathname.startsWith('/artifacts');
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current','page');
    else link.removeAttribute('aria-current');
  }

  function currentPublicRelativeUrl() {
    if (window.SPORTS_ROUTE_PUBLIC_URL) return window.SPORTS_ROUTE_PUBLIC_URL;
    if (location.pathname === '/index.html') return '/';
    return `${location.pathname}${location.search}`;
  }

  function setCanonicalToCurrentCleanUrl() {
    const clean = `${ORIGIN}${currentPublicRelativeUrl()}`;
    let canonical = document.head.querySelector('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.rel = 'canonical';
      document.head.appendChild(canonical);
    }
    canonical.href = clean;
    let og = document.head.querySelector('meta[property="og:url"]');
    if (!og) {
      og = document.createElement('meta');
      og.setAttribute('property','og:url');
      document.head.appendChild(og);
    }
    og.setAttribute('content', clean);
  }

  function boot() {
    rewriteLinks(document);
    ensureArtifactsNav();
    if (location.pathname === '/' || window.SPORTS_CLEAN_ROUTE) setCanonicalToCurrentCleanUrl();
    const observer = new MutationObserver(mutations => {
      let navMayNeedRefresh = false;
      for (const mutation of mutations) {
        if (mutation.type === 'attributes' && mutation.target instanceof HTMLAnchorElement) rewriteAnchor(mutation.target);
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            rewriteLinks(node);
            if (node.matches?.('.global-nav,#global-nav') || node.querySelector?.('.global-nav,#global-nav')) navMayNeedRefresh = true;
          }
        });
      }
      if (navMayNeedRefresh) ensureArtifactsNav();
    });
    observer.observe(document.documentElement, {subtree:true, childList:true, attributes:true, attributeFilter:['href']});
  }

  window.SportsPassportCleanUrls = { cleanPathForLegacy, rewriteLinks, currentPublicRelativeUrl, isCleanPublicRoute };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})();
