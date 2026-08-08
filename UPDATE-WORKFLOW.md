# Sports Passport update workflow

GitHub is the canonical home of the Sports Passport site.

## Central data

- `data/events.json` is the event-manifest file. It lists the event chunk files that make up the archive.
- `data/events-*.json` contain the attended events.
- `data/venues.json` contains one record per physical stadium or arena.
- `data/journeys.json` defines cross-year story threads.
- `data/phases.json` defines life-stage chapter boundaries.
- `data/corrections.json` contains audited overrides for source records that were later found to be incorrect.
- `data/config.json` contains archive metadata and current-year settings.

## Adding a game at an existing venue

1. Add one event object to the appropriate event chunk.
2. Give the event a new unique `evt-####` ID.
3. Use the existing physical `venue_key` from `data/venues.json`.
4. Run `python tools/validate_data.py`.
5. Commit the change.

No HTML needs to be regenerated. Annual editions, lifetime analytics, team profiles, venue profiles, journeys, life chapters, geography, map counts, and Hall of Fame records recalculate from the shared data when the site loads.

## Starting a new year

For 2026 and later, either append to the current newest event chunk or create a new file such as `events-2026-2029.json` and add that filename to the `chunks` array in `data/events.json`.

The year automatically appears in `annuals.html` and is available at `year.html?y=YYYY`. The configured `current_year` in `data/config.json` appears even before the first event is recorded.

## Visiting a brand-new physical venue

1. Add the event to an event chunk.
2. Add one physical venue record to `data/venues.json`.
3. Use an exact stadium/arena latitude and longitude when verified.
4. Point the event's `venue_key` to the new venue record.
5. Run the validator and commit.

The new venue then appears automatically in the directory, venue profile system, geography summaries, and venue map. If coordinates are temporarily unavailable, the profile still works and the map reports the venue as awaiting coordinates rather than guessing.

## Historical names

`venue_recorded` preserves the name stored with the original event. `venue_key` identifies the physical building. This prevents naming-rights changes from inflating the physical-venue count.

## Audited corrections

If a source record is later found to be wrong, prefer a targeted entry in `data/corrections.json` when preserving the original transcription is useful. The browser data layer applies these corrections before any statistics are calculated.

## Publishing

The production site is designed for GitHub Pages from the repository `main` branch and repository root. A validation workflow checks the archive on pushes and pull requests.
