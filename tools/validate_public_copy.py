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

# The full Artifacts workbench remains an internal collection/research surface. Public pages may
# selectively render provenance-linked evidence, but they must not advertise or link to the workbench.
for name, text in texts.items():
    for forbidden in (
        'href="artifacts.html"',
        "href='artifacts.html'",
        'href="/artifacts/"',
        "href='/artifacts/'",
        "D.load('artifact-priorities')",
        'D.load("artifact-priorities")',
    ):
        if forbidden in text:
            errors.append(f'{name} exposes the internal Artifacts workbench: {forbidden}')

home = texts.get('index.html', '')
for forbidden in ('<h3>Artifacts</h3>', 'Sports Passport · Artifacts', 'Open Artifacts'):
    if forbidden in home:
        errors.append(f'index.html advertises the internal Artifacts workbench: {forbidden}')

# Selective public evidence is intentionally limited to contextual archive pages. Other directory/
# analytics pages should stay text/data-first unless a future tranche explicitly adds a media context.
SELECTIVE_EVIDENCE_TEMPLATES = {
    'event.html', 'favorites.html', 'venue-profile.html', 'team-profile.html', 'phase.html'
}
for name, text in texts.items():
    if name not in SELECTIVE_EVIDENCE_TEMPLATES and ('D.load(\'artifacts\')' in text or 'D.load("artifacts")' in text):
        errors.append(f'{name} loads artifacts outside an approved selective evidence context')

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

# Record Book is the objective layer. Personal Canon rankings live only on favorites.html,
# while Lifetime Analytics owns trends and longitudinal interpretation.
hall = texts.get('hall-of-fame.html', '')
for required in ('Record Book', 'objective', 'Lifetime Analytics', 'Personal Canon'):
    if required not in hall:
        errors.append(f'hall-of-fame.html missing Record Book scope language: {required}')
for stale in ('My personal canon', 'Top 10 Sports Experiences.', 'rankings.sports_experiences', 'id="canon"'):
    if stale in hall:
        errors.append(f'hall-of-fame.html still duplicates Personal Canon content: {stale}')
if '<a href="hall-of-fame.html">Record Book</a>' not in home:
    errors.append('index.html must label the objective archive surface Record Book')

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
    f'OK: {len(texts)} public templates keep the Artifacts workbench unpublished while allowing selective provenance-linked evidence, '
    'separate objective Record Book records from Analytics and Personal Canon, use consistent life-chapter terminology, maintain first-person archive voice, and preserve navigable chapter analytics.'
)
