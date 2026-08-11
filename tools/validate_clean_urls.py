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
        "link.href = '/artifacts/';",
        "link.dataset.artifactsNav = 'true';",
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
    for route in ('/about/','/artifacts/','/years/','/events/','/teams/','/venues/','/geography/','/journeys/','/chapters/','/favorites/','/analytics/','/hall-of-fame/'):
        if route not in text:
            errors.append(f'clean route prefix missing: {route}')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print('OK: clean public routes preserve trailing-slash section URLs, descriptive query strings, and Artifacts navigation.')
