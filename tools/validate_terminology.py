#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

errors = []
for rel in [
    'index.html', 'favorites.html', 'hall-of-fame.html', 'journeys.html',
    'assets/archive-desks.js', 'assets/seo.js', 'tests/browser/smoke.spec.js'
]:
    text = (ROOT / rel).read_text(encoding='utf-8')
    if 'Hall of Fame' in text:
        errors.append(f'{rel}: legacy public label "Hall of Fame" remains; use "Record Book"')

label_checks = [
    ('favorites.html', r'href=["\']favorites\.html["\'][^>]*>Top Tens</a>', 'Personal Canon'),
    ('journeys.html', r'<title>Journeys \| Sports Passport</title>', 'Life Chapters'),
    ('journeys.html', r'Sports Passport · Journeys', 'Sports Passport · Life Chapters'),
]
for rel, pattern, replacement in label_checks:
    text = (ROOT / rel).read_text(encoding='utf-8')
    if re.search(pattern, text):
        errors.append(f'{rel}: legacy label matched {pattern!r}; use {replacement!r}')

if errors:
    raise SystemExit('\n'.join(errors))
print('Public terminology is consistent.')
