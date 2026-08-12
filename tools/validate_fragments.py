#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.hrefs.append(attrs['href'])


def parse(path):
    parser = PageParser()
    parser.feed(path.read_text(encoding='utf-8'))
    return parser


html_files = sorted(ROOT.rglob('*.html'))
parsed = {path: parse(path) for path in html_files}

for source, page in parsed.items():
    for href in page.hrefs:
        if href.startswith(('http://', 'https://', 'mailto:', 'tel:', 'javascript:')):
            continue
        parts = urlsplit(href)
        if not parts.fragment:
            continue

        # Query-only links keep the current page; static cross-page links resolve from
        # the source directory. Clean public routes are client-side wrappers and may
        # contain dynamic content, so only validate targets we can prove statically.
        if not parts.path:
            target = source
        elif parts.path.endswith('.html'):
            target = (source.parent / parts.path).resolve()
        else:
            continue

        if target not in parsed:
            if target.is_file():
                parsed[target] = parse(target)
            else:
                errors.append(f'{source.relative_to(ROOT)}: fragment link target file does not exist: {href}')
                continue

        if parts.fragment not in parsed[target].ids:
            errors.append(
                f'{source.relative_to(ROOT)}: fragment #{parts.fragment} not found in '
                f'{target.relative_to(ROOT)} (from {href})'
            )

if errors:
    print('\n'.join('ERROR: ' + error for error in errors))
    sys.exit(1)

fragment_links = sum(
    1 for page in parsed.values() for href in page.hrefs
    if urlsplit(href).fragment and not href.startswith(('http://', 'https://'))
)
print(f'OK: static fragment targets validated across {len(html_files)} HTML files ({fragment_links} fragment links).')
