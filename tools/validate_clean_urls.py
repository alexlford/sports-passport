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
    guard=text.find('if (isCleanPublicRoute(url))')
    file_parse=text.find("const file = (url.pathname.split('/').pop()")
    if guard < 0 or file_parse < 0 or guard > file_parse:
        errors.append('already-clean route guard must run before legacy filename parsing')
    for route in ('/about/','/years/','/events/','/teams/','/venues/','/geography/','/journeys/','/chapters/','/favorites/','/analytics/','/hall-of-fame/'):
        if route not in text:
            errors.append(f'clean route prefix missing: {route}')
    for retired in ("'/artifacts/'", 'artifacts.html', 'ensureArtifactsNav', 'data-artifacts-nav'):
        if retired in text:
            errors.append(f'artifact route/navigation must stay outside the public clean URL runtime: {retired}')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print('OK: clean public routes preserve trailing-slash section URLs and descriptive query strings without publishing the retained Artifacts feature.')
