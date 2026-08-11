#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]

readability=(ROOT/'assets'/'readability.css').read_text(encoding='utf-8')
home=(ROOT/'assets'/'home.css').read_text(encoding='utf-8')

for token in (
    'Shared visual hierarchy',
    'grid-template-columns:repeat(auto-fit,minmax(138px,1fr))',
    'min-height:94px',
    '.section{margin:50px 0!important}',
    'a.card:hover,a.card:focus-visible',
    '@media(max-width:760px)',
    '.stats{grid-template-columns:repeat(2,minmax(0,1fr))!important',
    '.scoreboard{padding:14px 12px!important',
):
    if token not in readability:
        errors.append(f'readability hierarchy token missing: {token}')

for token in (
    '.home-hero{',
    'padding:clamp(36px,5.8vw,68px)',
    '.home-stat{display:flex;min-height:92px',
    '.explore-section:last-of-type .portal-grid{grid-template-columns:repeat(4,minmax(0,1fr))}',
    '.portal{display:flex;min-height:174px',
    '.chapter:hover,.chapter:focus-visible',
    '@media(max-width:1100px)',
    '@media(max-width:700px)',
):
    if token not in home:
        errors.append(f'homepage hierarchy token missing: {token}')

# Keep mobile card density deliberate: two-up stats, one-up content cards.
if '.portal-grid,.chapters,.explore-section:last-of-type .portal-grid{grid-template-columns:1fr}' not in home:
    errors.append('homepage mobile content grids must collapse to one column')
if '.home-stats{grid-template-columns:1fr 1fr' not in home:
    errors.append('homepage mobile stats must remain compact two-up')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print('OK: shared hero, stats, section, card, homepage, and mobile density polish remains intact.')
