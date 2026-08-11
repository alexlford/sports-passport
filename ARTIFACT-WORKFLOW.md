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

Do not create an artifact record simply because an event would benefit from one. Candidate moments and research leads live separately so they cannot be mistaken for known physical objects.

## 1A. Track a research lead

Use `data/artifact-priorities.json` when physical evidence would materially strengthen the biography but no known object has yet been identified. A research lead can point to one exact event, several candidate events, or a broader set of notional early-archive records.

Each research lead should include:

- a stable `artifact-priority-####` ID
- the life-chapter `phase_key`
- a category such as `verified_early_archive` or `family_history`
- a public-facing summary explaining why evidence would matter
- `event_ids` defining the exact or candidate archive records in scope
- a status that makes uncertainty explicit
- supported `candidate_types` worth looking for
- a `research_note` stating what still needs to be established

A research lead is not evidence. It must never change attendance confidence, create a museum case, or imply ownership of an object. If the exact event is unresolved, preserve every plausible candidate until the date can be confirmed rather than guessing.

## 2. Digitize the source

For an existing physical artifact:

1. Scan or photograph it square to the camera with even light.
2. Crop to the object without cutting off ticket edges, dates, seat information, logos, or handwritten context that contributes provenance.
3. Keep a high-resolution archival original outside the website repository if desired.
4. Create a web-ready JPEG, PNG, or WebP copy sized for fast page loading.
5. Add the web copy under `assets/artifacts/` with a descriptive stable filename, for example `1993-camden-yards-ticket-stub.webp`.
6. Set the artifact record's `media` field to that path and change `digitization_status` to `digitized`.

The website will automatically surface the new visual on the Artifact Museum and on connected Event Passport, annual, venue, life-chapter, and recurring-journey views.

## 3. Promote a research lead into the catalog

When a real source is found:

1. Match it to an exact event before creating an artifact record.
2. If a lead contains multiple candidate events, resolve the event first and update the research record so the uncertainty is removed deliberately.
3. Create the real artifact entry in `data/artifacts.json`.
4. Add media only if an actual scan or photograph exists.
5. Remove or retire the corresponding research lead once the new catalog entry makes it redundant.
6. Only update a pre-2006 attendance confidence label if the new evidence genuinely supports that change.

This separation keeps the research queue useful without allowing future possibilities to masquerade as provenance.

## 4. Validate provenance

Before merging, confirm:

- the artifact is attached to the correct exact event
- the public title and summary do not overstate what the object proves
- the media file is the actual artifact named in the catalog
- known early-archive confidence labels remain unchanged unless new evidence truly changes the underlying attendance claim
- no Personal Canon candidate or biography research lead is promoted into the catalog without a real identified source
- unresolved multi-event research leads still preserve every plausible event rather than selecting one by assumption

Run the repository validation suite or rely on the pull-request CI checks. `tools/validate_artifacts.py` verifies artifact IDs, research-priority IDs, event references, supported object/status values, media-file consistency, life-chapter alignment, and the known evidence fact locks.

## 5. Priority order

When choosing what to digitize or research next, use this order:

1. already-cataloged evidence with `image_pending`
2. physical evidence that can strengthen a Verified early-archive record
3. known artifacts tied to a Top 10 Sports Experience
4. family-history artifacts that add provenance or personal narrative
5. unresolved biography research leads where one exact event still needs confirmation
6. other tickets, credentials, programs, photos, seat views, and keepsakes that add something the event data alone cannot show

The guiding rule is simple: **provenance over decoration**.
