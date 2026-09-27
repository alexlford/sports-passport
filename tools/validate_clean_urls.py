#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'assets'/'clean-urls.js'
errors=[]

if not path.is_file():
    errors.append('missing assets/clean-urls.js')
else:
    text=path.read_text(encoding='utf-8')
    required=(
        'CLEAN_ROUTE_PREFIXES',
        'isCleanPublicRoute',
        'function deepCleanRoute(url)',
        'function queryCleanRoute(url)',
        'new URL(rawHref, document.baseURI || location.href)',
        'const deep = deepCleanRoute(url);',
        'if (deep) return deep;',
        'const queryRoute = queryCleanRoute(url);',
        'if (queryRoute) return queryRoute;',
        "'/years/': ['year','y']",
        "'/events/': ['event','id']",
        "'/teams/': ['team','t']",
        "'/venues/': ['venue','v']",
        "'/journeys/': ['journey','j']",
        "'/chapters/': ['chapter','p']",
        "if (isCleanPublicRoute(url)) return `${url.pathname}${url.search}${url.hash}`;",
        "if (url.pathname === '/' || file === 'index.html') path = '/';",
        '/years/${encode(p.get(\'y\'))}/',
        '/events/${encode(p.get(\'id\'))}/',
        '/teams/${encode(p.get(\'t\'))}/',
        '/venues/${encode(p.get(\'v\'))}/',
        '/journeys/${encode(p.get(\'j\'))}/',
        '/chapters/${encode(p.get(\'p\'))}/',
    )
    for token in required:
        if token not in text:
            errors.append(f'clean URL runtime missing regression token: {token}')
    if "if (file === '' || file === 'index.html') path = '/';" in text:
        errors.append('trailing-slash regression: empty filename must not be treated as archive home')
    deep=text.find('const deep = deepCleanRoute(url);')
    query=text.find('const queryRoute = queryCleanRoute(url);')
    guard=text.find('if (isCleanPublicRoute(url))')
    file_parse=text.find("const file = (url.pathname.split('/').pop()")
    if min(deep,query,guard,file_parse) < 0 or not (deep < query < guard < file_parse):
        errors.append('deep and legacy-query routes must normalize before already-clean guard and legacy filename parsing')
    for route in ('/about/','/years/','/events/','/teams/','/venues/','/geography/','/journeys/','/chapters/','/favorites/','/analytics/','/hall-of-fame/'):
        if route not in text:
            errors.append(f'clean route prefix missing: {route}')
    for retired in ("'/artifacts/'", 'artifacts.html', 'ensureArtifactsNav', 'data-artifacts-nav'):
        if retired in text:
            errors.append(f'artifact route/navigation must stay outside the public clean URL runtime: {retired}')
    for legacy_query in ('/years/?year=','/events/?event=','/teams/?team=','/venues/?venue=','/journeys/?journey=','/chapters/?chapter='):
        if legacy_query in text:
            errors.append(f'new links must not emit legacy query routes: {legacy_query}')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print('OK: clean links resolve to first-class deep static pages while old query URLs remain compatibility inputs.')
