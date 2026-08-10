# Sports Passport

A personal, data-driven archive of live sports attendance for Alex Ford.

## Current archive

- 266 event records
- 57 physical venues
- Annual editions from 1993 through the current 2026 season
- Team, venue, geography, journey, analytics, favorites, and Hall of Fame views
- Three curated Top 10 rankings: sports experiences, favorite venues, and best venues visited

## Historical confidence

The early archive is intentionally transparent about evidentiary confidence. Pre-2006 events are labeled either `verified` or `notional` in the source data. Verified early events have surviving evidence or direct confirmation; notional records are plausible reconstructions used to preserve the shape of the early sports timeline without claiming exact attendance certainty.

Examples of verified pre-2006 attendance include Camden Yards games supported by old ticket stubs and Indiana at Southern Illinois on December 1, 2001. The July 16, 1999 Twins–Cubs Wrigley Field record is notional.

## Updating the archive

See [`UPDATE-WORKFLOW.md`](UPDATE-WORKFLOW.md) for the event, venue, team identity, confidence, and validation rules.

Run the archive validator before merging data changes:

```bash
python tools/validate_data.py
```

The public site is hosted with GitHub Pages at `sports.alexlford.com`.
