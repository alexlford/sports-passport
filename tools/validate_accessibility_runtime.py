#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors=[]

runtime=(ROOT/'assets'/'accessibility.js').read_text(encoding='utf-8') if (ROOT/'assets'/'accessibility.js').is_file() else ''
css=(ROOT/'assets'/'accessibility.css').read_text(encoding='utf-8') if (ROOT/'assets'/'accessibility.css').is_file() else ''
shared=(ROOT/'assets'/'sports-passport-data.js').read_text(encoding='utf-8') if (ROOT/'assets'/'sports-passport-data.js').is_file() else ''

for token,label in (
    ('Skip to main content','skip link'),
    ("event.key !== 'Escape'",'Escape-close keyboard handling'),
    ("toggle.focus()",'menu focus return'),
    ("aria-live', 'polite'",'live result status'),
    ('map-text-alternative','text alternative for maps'),
    ('accessibleThemeColor','dynamic team theme contrast guard'),
    ('data-contrast-ratio','runtime contrast annotation'),
):
    if token not in runtime:
        errors.append(f'accessibility runtime missing {label}: {token}')

for token,label in (
    ('prefers-reduced-motion: reduce','reduced-motion media query'),
    ('.skip-link','skip-link styling'),
    ('.map-text-alternative','map text-alternative styling'),
):
    if token not in css:
        errors.append(f'accessibility CSS missing {label}: {token}')

for token,label in (
    ("ensureStyle('/assets/accessibility.css'",'shared accessibility stylesheet injection'),
    ("script.src = '/assets/accessibility.js'",'shared accessibility runtime injection'),
):
    if token not in shared:
        errors.append(f'shared runtime missing {label}: {token}')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print('OK: keyboard, live-region, reduced-motion, map-alternative, and dynamic-theme accessibility safeguards are wired globally.')
