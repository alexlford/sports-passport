# Sports Passport update workflow

The site is data-driven. The authoritative event archive is split into year-range chunks listed by `data/events.json`; dynamic pages load the manifest and merge the chunks in the browser.

## Add or correct an event

1. Edit the appropriate event chunk listed in `data/events.json`.
2. Keep the event `id` unique and stable.
3. Preserve the source-supplied team labels in `teams`.
4. Preserve the source-supplied venue wording in `venue_recorded`.
5. Set `venue_key` to the physical venue identity used by the venue registry.
6. Update `data/events.json` and `data/config.json` event counts if the archive size changes.
7. Run `python tools/validate_data.py` before merge.

## Attendance confidence for early reconstructed years

The pre-2006 archive contains a mixture of documented attendance and reconstructed/notional records. Every event before 2006 must declare one of these values:

- `attendance_status: "verified"` when attendance is supported by surviving evidence or direct confirmation. Include a short `verification` field describing that evidence.
- `attendance_status: "notional"` when the event is a plausible reconstruction used to represent the early sports timeline but exact attendance is not independently verified.

Do not upgrade a notional record to verified without evidence or direct user confirmation. The current verified pre-2006 records include the Camden Yards games supported by old ticket stubs and Indiana at Southern Illinois on December 1, 2001. The July 16, 1999 Twins–Cubs Wrigley Field record is explicitly notional.

Aggregate archive views may include both verified/documented and notional records, but they must call those counts **archive records/visits/appearances** and explain the confidence policy. Objective Hall of Fame records and team win/loss records exclude notional reconstructions.

## Venue-name fact lock

`venue_recorded` is a source fact. Keep the exact venue name supplied by the attendance source, even when a different naming-rights name was historically in use on the event date.

`venue_key` identifies the physical building and may therefore differ from `venue_recorded`. Use aliases in the venue registry to connect alternate names to one physical venue.

Do not silently reconstruct historical naming-rights names. Use `data/venue-corrections.json` only for an audited factual correction, not for historical-name substitution.

## Team-name fact lock

Event `teams` arrays are source facts. Do not rewrite an event's team labels merely to standardize naming.

Use `data/team-aliases.json` to map source labels to a canonical identity for team profiles and aggregate analytics. Appropriate uses include relocations, rebrands, abbreviations, and generic labels. Keep mappings one step deep: an alias target may not itself be another alias source.

This means a canonical team profile can aggregate historical identities while annual event cards continue to display the exact source wording.

## Add a new physical venue

Add the venue to `data/venue-additions.json` with:

- `key`
- `slug`
- `display_name`
- `city`
- registered `latitude` and `longitude`
- `aliases`
- `first_year`
- `last_year`

Then update `venue_count` in `data/config.json`. The loader combines `data/venues.json` and `data/venue-additions.json` automatically. Do not describe coordinates as independently verified unless there is evidence supporting that claim; the public map calls them registered venue points.

## Team colors

Every exact source team label used by an event must have a two-color palette in `data/team-colors.json`. Each color must be a six-digit hex value.

Canonical team identities must also be able to resolve a palette, either directly or through one of their source aliases.

## Curated Top 10 rankings

`data/curated-rankings.json` contains three intentionally editorial lists:

- `sports_experiences`
- `favorite_venues`
- `best_venues`

Each list must contain exactly ten entries ordered with ranks 1 through 10. These lists are user-curated, not algorithmic. Revisit them as new seasons and venues are added, rather than deriving them automatically from attendance counts.

Every `sports_experiences` entry must include the exact archive `event_id`. This keeps the editorial ranking connected to the factual event record and lets the site link each ranked experience back to its annual edition.

The favorite-venue list intentionally permits editorial groupings that are broader than a single physical `venue_key`, such as `Busch Stadium` across stadium generations and `SIU — Arena & Football Stadium` as a personal-place grouping.

## Dynamic views

`data/config.json` contains a `dynamic_views` registry. Keep it complete when a new data-driven page is added. The validator checks both that the known dynamic pages are listed and that every listed path exists.

## Validation

Run:

```bash
python tools/validate_data.py
```

The validator checks event IDs, venue keys, archive counts, team palettes and aliases, early-record attendance confidence, exact Top 10 event links, dynamic-view coverage, journey/phase uniqueness, source favorites, and correction references.
