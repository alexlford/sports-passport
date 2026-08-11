#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

PUBLIC_TEMPLATES = (
    'index.html',
    'about.html',
    'annuals.html',
    'year.html',
    'event.html',
    'favorites.html',
    'geography.html',
    'venue-map.html',
    'venues.html',
    'venue-profile.html',
    'teams.html',
    'team-profile.html',
    'journeys.html',
    'journey-profile.html',
    'phase.html',
    'lifetime-analytics.html',
    'hall-of-fame.html',
)

texts = {}
for name in PUBLIC_TEMPLATES:
    path = ROOT / name
    if not path.is_file():
        errors.append(f'missing public template: {name}')
        continue
    texts[name] = path.read_text(encoding='utf-8')

# Artifacts are deliberately retained internally but should not leak back into public presentation.
for name, text in texts.items():
    if 'artifact' in text.lower():
        errors.append(f'{name} contains public-facing artifact copy or integration')

# The narrative architecture is five life chapters, not generic eras/stages.
journeys = texts.get('journeys.html', '')
for required in ('The five chapters.', 'Stories that cross chapters.'):
    if required not in journeys:
        errors.append(f'journeys.html missing chapter-language lock: {required}')
for stale in ('The five eras.', 'Stories that cross eras.', 'defined that stage'):
    if stale in journeys:
        errors.append(f'journeys.html contains retired chapter terminology: {stale}')

# Personal archive pages should use the same first-person editorial voice.
team_profile = texts.get('team-profile.html', '')
if 'Where I saw them' not in team_profile:
    errors.append('team-profile.html must use first-person venue history wording')
if 'Where you saw them' in team_profile:
    errors.append('team-profile.html still uses second-person venue history wording')

venue_profile = texts.get('venue-profile.html', '')
if 'What I saw here' not in venue_profile:
    errors.append('venue-profile.html must use first-person sport-mix wording')
for stale in ('What you saw here', 'recalculates automatically from the central archive data'):
    if stale in venue_profile:
        errors.append(f'venue-profile.html contains implementation/second-person wording: {stale}')

hall = texts.get('hall-of-fame.html', '')
if 'My personal canon' not in hall:
    errors.append('hall-of-fame.html must use first-person Personal Canon wording')
for stale in ("Alex's personal canon", "alongside Alex's curated"):
    if stale in hall:
        errors.append(f'hall-of-fame.html contains inconsistent third-person wording: {stale}')

geography = texts.get('geography.html', '')
if '<div class="kicker">Venue directory</div>' not in geography:
    errors.append('geography.html must frame venue profiles as the venue directory')
for stale in ('artifact cases', '<div class="kicker">Museum</div>'):
    if stale in geography:
        errors.append(f'geography.html contains retired museum wording: {stale}')

# Life chapters should be navigable into the rest of the archive rather than ending in static analytics.
phase = texts.get('phase.html', '')
for required in (
    'D.load("venues")',
    '/years/?year=',
    '/teams/?team=',
    '/venues/?venue=',
    'grid3',
    'Team names open their full archive profiles.',
    'Venue names open their profiles.',
):
    if required not in phase:
        errors.append(f'phase.html missing chapter cross-linking token: {required}')

if errors:
    print('\n'.join('ERROR: ' + e for e in errors))
    sys.exit(1)

print(
    f'OK: {len(texts)} public templates keep Artifacts unpublished, use consistent life-chapter terminology, '
    'maintain first-person archive voice, and preserve navigable chapter analytics.'
)
