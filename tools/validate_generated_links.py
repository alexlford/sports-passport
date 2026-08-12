#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

# Legacy templates remain the implementation targets behind the clean public URL layer.
# A typo in a JavaScript template string can therefore create a broken link that an
# ordinary DOM/static-href validator never sees.
EXPECTED_QUERY_KEY = {
    'year.html': 'y',
    'event.html': 'id',
    'team-profile.html': 't',
    'venue-profile.html': 'v',
    'journey-profile.html': 'j',
    'phase.html': 'p',
}

pattern = re.compile(r'(?P<path>(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.html)(?:\?(?P<query>[^\s"\'`<>]*))?')
source_files = sorted(list(ROOT.glob('*.html')) + list((ROOT / 'assets').glob('*.js')))
seen = []

for source in source_files:
    text = source.read_text(encoding='utf-8')
    for match in pattern.finditer(text):
        rel = match.group('path')
        query = match.group('query') or ''

        # Skip fully qualified external URLs whose path merely ends in .html.
        prefix = text[max(0, match.start() - 12):match.start()]
        if '://' in prefix:
            continue

        # Links emitted by shared scripts resolve in the document's URL context, not
        # relative to /assets/. Top-level HTML templates resolve relative to themselves.
        base = ROOT if source.parent == ROOT / 'assets' else source.parent
        target = (base / rel).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            errors.append(f'{source.relative_to(ROOT)}: generated link escapes repository: {rel}')
            continue

        if not target.is_file():
            errors.append(f'{source.relative_to(ROOT)}: generated local target does not exist: {rel}')
            continue

        name = target.name
        expected = EXPECTED_QUERY_KEY.get(name)
        if expected and query:
            first = query.split('&', 1)[0]
            key = first.split('=', 1)[0]
            if key and key != expected:
                errors.append(
                    f'{source.relative_to(ROOT)}: generated {name} link uses query key {key!r}; '
                    f'expected {expected!r}: {match.group(0)}'
                )

        seen.append((source.relative_to(ROOT), match.group(0)))

if errors:
    print('\n'.join('ERROR: ' + error for error in errors))
    sys.exit(1)

print(f'OK: {len(seen)} generated/local .html link references validated across {len(source_files)} HTML/JS source files.')
