#!/usr/bin/env python3
"""Mark reconstructed/notional Event Passports noindex,follow in generated HTML."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
META = '<meta name="robots" content="noindex,follow">'


def main():
    events = json.loads((DATA / 'resolved-events.json').read_text(encoding='utf-8'))
    notional = [event for event in events if event.get('attendance_status') == 'notional' and event.get('id')]
    touched = 0
    for event in notional:
        path = ROOT / 'events' / str(event['id']) / 'index.html'
        if not path.is_file():
            raise SystemExit(f'missing generated Event Passport {path.relative_to(ROOT)}')
        text = path.read_text(encoding='utf-8')
        text = re.sub(r'<meta\s+name=["\']robots["\'][^>]*>', '', text, flags=re.I)
        text = text.replace('</head>', META + '\n</head>', 1)
        path.write_text(text, encoding='utf-8')
        touched += 1
    print(f'Marked {touched} reconstructed Event Passports noindex,follow.')


if __name__ == '__main__':
    main()
