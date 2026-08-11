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
        'new URL(rawHref, document.baseURI || location.href)',
        'const deep = deepCleanRoute(url);',
        'if (deep) return deep;',
        "years: ['year', value]",
        "events: ['event', value]",
        "teams: ['team', value]",
        "venues: ['venue', value]",
        "journeys: ['journey', value]",
        "chapters: ['chapter', value]",
        "if (isCleanPublicRoute(url)) return `${url.pathname}${url.search}${url.hash}`;",
        "if (url.pathname === '/' || file === 'index.html') path = '/';",
        '/years/?year=',
        '/events/?event=',
        '/teams/?team=',
        '/venues/?venue=',
        '/journeys/?journey=',
        '/chapters/?chapter=',
    )
    for token in required:
        if token not in text:
            errors.append(f'clean URL runtime missing regression token: {token}')
    if "if (file === '' || file === 'index.html') path = '/';" in text:
        errors.append('trailing-slash regression: empty filename must not be treated as archive home')
    deep=text.find('const deep = deepCleanRoute(url);')
    guard=text.find('if (isCleanPublicRoute(url))')
    file_parse=text.find("const file = (url.pathname.split('/').pop()")
    if min(deep,guard,file_parse) < 0 or not (deep < guard < file_parse):
        errors.append('deep clean routes must normalize before already-clean route guard and legacy filename parsing')
    for route in ('/about/','/years/','/events/','/teams/','/venues/','/geography/','/journeys/','/chapters/','/favorites/','/analytics/','/hall-of-fame/'):
        if route not in text:
            errors.append(f'clean route prefix missing: {route}')
    for retired in ("'/artifacts/'", 'artifacts.html', 'ensureArtifactsNav', 'data-artifacts-nav'):
        if retired in text:
            errors.append(f'artifact route/navigation must stay outside the public clean URL runtime: {retired}')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print('OK: clean public routes preserve section URLs, normalize deep routes to GitHub-Pages-safe query routes, and resolve relative links against document.baseURI.')
