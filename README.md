# Sports Passport

A personal, data-driven archive of live sporting events attended from 1993 to the present.

## Live architecture

The site is static HTML/CSS/JavaScript designed for GitHub Pages. The central source of truth is `data/events.json`; venue metadata lives in `data/venues.json`. Annual editions, lifetime analytics, team profiles, venue profiles, journey pages, life chapters, and Hall of Fame records derive from those shared data files.

## Updating the archive

1. Add the attended event to `data/events.json`.
2. If it is a brand-new physical venue, add it to `data/venues.json` with exact coordinates.
3. Run `python tools/validate_data.py`.
4. Commit the changes. GitHub Pages publishes the updated static site.

See `UPDATE-WORKFLOW.md` for the full maintenance contract.

## Entry points

- `index.html` — archive home
- `annuals.html` — annual editions
- `lifetime-analytics.html` — lifetime analytics
- `teams.html` — team explorer
- `venues.html` — venue museum
- `venue-map.html` — interactive venue atlas
- `journeys.html` — cross-year life threads
- `hall-of-fame.html` — record book and personal ballot

## Hosting

Intended for GitHub Pages from the `main` branch, repository root.
