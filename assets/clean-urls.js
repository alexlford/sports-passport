(() => {
  const ORIGIN = 'https://sports.alexlford.com';
  const CLEAN_ROUTE_PREFIXES = [
    '/about/','/years/','/events/','/teams/','/venues/','/geography/',
    '/journeys/','/chapters/','/favorites/','/analytics/','/hall-of-fame/','/search/'
  ];
  const GENERATED_META = window.SPORTS_ROUTE_SOURCE ? {
    title: document.title,
    description: document.head.querySelector('meta[name="description"]')?.getAttribute('content') || '',
    canonical: document.head.querySelector('link[rel="canonical"]')?.href || '',
  } : null;

  function encode(value) {
    return encodeURIComponent(String(value || '').trim());
  }

  function withHash(path, hash) {
    return `${path}${hash || ''}`;
  }

  function isCleanPublicRoute(url) {
    return CLEAN_ROUTE_PREFIXES.some(prefix => url.pathname === prefix || url.pathname.startsWith(prefix));
  }

  function deepCleanRoute(url) {
    const parts = url.pathname.split('/').filter(Boolean).map(decodeURIComponent);
    if (parts.length !== 2) return null;
    const [section, value] = parts;
    if (!value || !['years','events','teams','venues','journeys','chapters'].includes(section)) return null;
    return `/${section}/${encode(value)}/${url.hash || ''}`;
  }

  function queryCleanRoute(url) {
    const path = url.pathname.endsWith('/') ? url.pathname : `${url.pathname}/`;
    const route = {
      '/years/': ['year','y'],
      '/events/': ['event','id'],
      '/teams/': ['team','t'],
      '/venues/': ['venue','v'],
      '/journeys/': ['journey','j'],
      '/chapters/': ['chapter','p'],
    }[path];
    if (!route) return null;
    const value = route.map(key => url.searchParams.get(key)).find(Boolean);
    return value ? `${path}${encode(value)}/${url.hash || ''}` : null;
  }

  function cleanPathForLegacy(rawHref) {
    if (!rawHref || rawHref.startsWith('#') || rawHref.startsWith('mailto:') || rawHref.startsWith('tel:') || rawHref.startsWith('javascript:')) return null;
    let url;
    try { url = new URL(rawHref, document.baseURI || location.href); } catch (_) { return null; }
    if (url.origin !== location.origin) return null;

    const deep = deepCleanRoute(url);
    if (deep) return deep;
    const queryRoute = queryCleanRoute(url);
    if (queryRoute) return queryRoute;
    if (isCleanPublicRoute(url)) return `${url.pathname}${url.search}${url.hash}`;

    const file = (url.pathname.split('/').pop() || '').toLowerCase();
    const p = url.searchParams;
    let path = null;

    if (url.pathname === '/' || file === 'index.html') path = '/';
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
    else if (file === 'search.html') path = '/search/';

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

  const cleanRouteKey = path => {
    const pathname = path || '/';
    if (pathname === '/') return 'home';
    if (pathname.startsWith('/years/') || pathname.startsWith('/events/')) return 'years';
    if (pathname.startsWith('/geography/') || pathname.startsWith('/venues/')) return 'geography';
    if (pathname.startsWith('/teams/')) return 'teams';
    if (pathname.startsWith('/journeys/') || pathname.startsWith('/chapters/')) return 'journeys';
    if (pathname.startsWith('/favorites/')) return 'favorites';
    if (pathname.startsWith('/analytics/')) return 'analytics';
    if (pathname.startsWith('/hall-of-fame/')) return 'hof';
    if (pathname.startsWith('/about/')) return 'about';
    if (pathname.startsWith('/search/')) return 'search';
    return '';
  };

  function currentPublicRelativeUrl() {
    if (window.SPORTS_ROUTE_PUBLIC_URL) return window.SPORTS_ROUTE_PUBLIC_URL;
    const cleaned = cleanPathForLegacy(location.href);
    if (cleaned) return cleaned;
    if (location.pathname === '/index.html') return '/';
    return `${location.pathname}${location.search}${location.hash || ''}`;
  }

  function upsertMeta(attribute, key, content) {
    if (!content) return;
    let meta = document.head.querySelector(`meta[${attribute}="${key}"]`);
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute(attribute, key);
      document.head.appendChild(meta);
    }
    meta.setAttribute('content', content);
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
    upsertMeta('property','og:url',clean);
  }

  function restoreGeneratedMetadata() {
    if (!GENERATED_META) return;
    if (GENERATED_META.title) {
      document.title = GENERATED_META.title;
      upsertMeta('property','og:title',GENERATED_META.title);
      upsertMeta('name','twitter:title',GENERATED_META.title);
    }
    if (GENERATED_META.description) {
      upsertMeta('name','description',GENERATED_META.description);
      upsertMeta('property','og:description',GENERATED_META.description);
      upsertMeta('name','twitter:description',GENERATED_META.description);
    }
    setCanonicalToCurrentCleanUrl();
  }

  function polishPublicChrome() {
    const header = document.querySelector('.site-header');
    if (header) {
      const brand = header.querySelector('.brand a');
      if (brand) brand.setAttribute('href','/');
      const active = cleanRouteKey(new URL(currentPublicRelativeUrl(), ORIGIN).pathname);
      const primaryNavPaths = new Set(['/years/','/teams/','/geography/','/journeys/','/favorites/']);
      header.querySelectorAll('.global-nav a:not(.external)').forEach(anchor => {
        const clean = cleanPathForLegacy(anchor.getAttribute('href')) || anchor.getAttribute('href');
        if (!primaryNavPaths.has(clean)) {
          anchor.remove();
          return;
        }
        const key = cleanRouteKey(new URL(clean, ORIGIN).pathname);
        anchor.classList.toggle('active', !!active && key === active);
        if (active && key === active) anchor.setAttribute('aria-current','page');
        else anchor.removeAttribute('aria-current');
        if (clean === '/geography/') anchor.textContent = 'Places';
        if (clean === '/journeys/') anchor.textContent = 'Life Chapters';
        if (clean === '/favorites/') anchor.textContent = 'Personal Canon';
      });
      const search = header.querySelector('.global-search-link');
      if (search) {
        search.setAttribute('href','/search/');
        search.classList.toggle('active', active === 'search');
        if (active === 'search') search.setAttribute('aria-current','page');
        else search.removeAttribute('aria-current');
      }
    }

    const footer = document.querySelector('.site-footer');
    if (footer && !footer.querySelector('[data-about-archive]')) {
      const about = document.createElement('a');
      about.href = '/about/';
      about.dataset.aboutArchive = 'true';
      about.textContent = 'About the archive';
      const external = footer.querySelector('a[href*="alexlford.com"]');
      if (external) footer.insertBefore(about, external);
      else footer.appendChild(about);
    }
  }

  function boot() {
    rewriteLinks(document);
    setCanonicalToCurrentCleanUrl();
    polishPublicChrome();
    if (GENERATED_META) setTimeout(restoreGeneratedMetadata, 0);
    const observer = new MutationObserver(mutations => {
      let chromeChanged = false;
      for (const mutation of mutations) {
        if (mutation.type === 'attributes' && mutation.target instanceof HTMLAnchorElement) rewriteAnchor(mutation.target);
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            rewriteLinks(node);
            if (node.matches?.('.site-header,.site-footer') || node.querySelector?.('.site-header,.site-footer')) chromeChanged = true;
          }
        });
      }
      if (chromeChanged) polishPublicChrome();
    });
    observer.observe(document.documentElement, {subtree:true, childList:true, attributes:true, attributeFilter:['href']});
  }

  window.SportsPassportCleanUrls = { cleanPathForLegacy, rewriteLinks, currentPublicRelativeUrl, isCleanPublicRoute, cleanRouteKey, polishPublicChrome, deepCleanRoute, queryCleanRoute };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})();
