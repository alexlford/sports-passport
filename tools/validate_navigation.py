#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]
clean=(ROOT/'assets'/'clean-urls.js').read_text(encoding='utf-8')
chrome=(ROOT/'assets'/'chrome.css').read_text(encoding='utf-8')
route=(ROOT/'assets'/'route-bootstrap.js').read_text(encoding='utf-8')
not_found=(ROOT/'404.html').read_text(encoding='utf-8')

required_clean=(
    'const cleanRouteKey = path =>',
    "if (window.SPORTS_ROUTE_PUBLIC_URL) return window.SPORTS_ROUTE_PUBLIC_URL;",
    "const cleaned = cleanPathForLegacy(location.href);",
    "new URL(rawHref, document.baseURI || location.href)",
    "if (pathname.startsWith('/years/') || pathname.startsWith('/events/')) return 'years';",
    "if (pathname.startsWith('/geography/') || pathname.startsWith('/venues/')) return 'geography';",
    "if (pathname.startsWith('/teams/')) return 'teams';",
    "if (pathname.startsWith('/journeys/') || pathname.startsWith('/chapters/')) return 'journeys';",
    "if (pathname.startsWith('/favorites/')) return 'favorites';",
    "if (pathname.startsWith('/analytics/')) return 'analytics';",
    "if (pathname.startsWith('/hall-of-fame/')) return 'hof';",
    "if (clean === '/journeys/') anchor.textContent = 'Life Chapters';",
    "if (clean === '/favorites/') anchor.textContent = 'Personal Canon';",
    "if (brand) brand.setAttribute('href','/');",
    "about.href = '/about/';",
    'setCanonicalToCurrentCleanUrl();',
    'polishPublicChrome();',
)
for token in required_clean:
    if token not in clean:
        errors.append(f'clean navigation runtime missing: {token}')

if "if (location.pathname === '/' || window.SPORTS_CLEAN_ROUTE) setCanonicalToCurrentCleanUrl();" in clean:
    errors.append('canonical cleanup must apply to legacy entry URLs too')
if "currentPublicRelativeUrl() {\n    if (window.SPORTS_ROUTE_PUBLIC_URL) return window.SPORTS_ROUTE_PUBLIC_URL;\n    if (location.pathname === '/index.html')" in clean:
    errors.append('legacy direct URLs are not being canonicalized to clean public routes')

required_route=(
    "publicQuery.get('y')",
    "publicQuery.get('id')",
    "publicQuery.get('t')",
    "publicQuery.get('v')",
    "publicQuery.get('j')",
    "publicQuery.get('p')",
    "else template = 'annuals.html';",
    "${location.hash || ''}",
)
for token in required_route:
    if token not in route:
        errors.append(f'route bootstrap missing recovery behavior: {token}')

required_404=(
    'src="/assets/route-bootstrap.js"',
    'href="/assets/site.css"',
    'href="/favicon.svg"',
    'src="/assets/clean-urls.js"',
    'href="/years/"',
    'href="/teams/"',
    'href="/venues/"',
)
for token in required_404:
    if token not in not_found:
        errors.append(f'404 recovery page missing root-safe route/asset reference: {token}')
for bad in ('src="assets/route-bootstrap.js"','href="assets/site.css"','src="assets/clean-urls.js"'):
    if bad in not_found:
        errors.append(f'404 recovery page must not use nested-path-relative asset reference: {bad}')

if '@media(max-width:1040px)' not in chrome:
    errors.append('shared navigation should collapse before desktop links become cramped')
if '@media(max-width:900px)' in chrome:
    errors.append('old cramped navigation breakpoint still present')
if '.site-footer span{margin-right:auto}' not in chrome:
    errors.append('footer link grouping polish missing')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print('OK: clean navigation, deep-route recovery, root-safe 404 assets, canonical URLs, footer links, and responsive chrome are validated consistently.')
