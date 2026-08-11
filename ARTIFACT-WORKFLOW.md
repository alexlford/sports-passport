# Sports Passport Artifact Workflow

The artifact layer is deliberately evidence-first. A museum card should only claim an object exists after that object has been identified and added to `data/artifacts.json`. A visual should only appear after a real scan or photograph has been committed.

## 1. Catalog the object

Add one record to `data/artifacts.json` with:

- `id`: next stable `artifact-####` identifier
- `event_id`: exact Sports Passport event ID
- `type`: `ticket_stub`, `credential`, `program`, `seat_view`, `keepsake`, or `photo`
- `title`: concise public-facing object title
- `summary`: what the object is and which event it documents
- `provenance`: why it belongs in the archive and what it establishes
- `digitization_status`: `image_pending` until a real media file is present; `digitized` after one is added
- `media`: `null` until digitized

Do not create an artifact record simply because an event would benefit from one. The public Personal Canon coverage queue is intentionally separate from the catalog so candidate moments cannot be mistaken for known physical objects.

## 2. Digitize the source

For an existing physical artifact:

1. Scan or photograph it square to the camera with even light.
2. Crop to the object without cutting off ticket edges, dates, seat information, logos, or handwritten context that contributes provenance.
3. Keep a high-resolution archival original outside the website repository if desired.
4. Create a web-ready JPEG, PNG, or WebP copy sized for fast page loading.
5. Add the web copy under `assets/artifacts/` with a descriptive stable filename, for example `1993-camden-yards-ticket-stub.webp`.
6. Set the artifact record's `media` field to that path and change `digitization_status` to `digitized`.

The website will automatically surface the new visual on the Artifact Museum and on connected Event Passport, annual, venue, life-chapter, and recurring-journey views.

## 3. Validate provenance

Before merging, confirm:

- the artifact is attached to the correct exact event
- the public title and summary do not overstate what the object proves
- the media file is the actual artifact named in the catalog
- known early-archive confidence labels remain unchanged unless new evidence truly changes the underlying attendance claim
- no Personal Canon candidate is promoted into the catalog without a real identified source

Run the repository validation suite or rely on the pull-request CI checks. `tools/validate_artifacts.py` verifies IDs, event references, supported object/status values, media-file consistency, and the known Camden Yards ticket-stub fact locks.

## 4. Priority order

When choosing what to digitize next, use this order:

1. already-cataloged evidence with `image_pending`
2. physical evidence that can strengthen a Verified early-archive record
3. known artifacts tied to a Top 10 Sports Experience
4. family-history artifacts that add provenance or personal narrative
5. other tickets, credentials, programs, photos, seat views, and keepsakes that add something the event data alone cannot show

The guiding rule is simple: **provenance over decoration**.
