# Sports Passport Design System Baseline

Status: **baseline documentation only**  
Purpose: preserve the publication identity while the site is consolidated through small, independently reversible PRs.

This document records the production design language that already exists. It is not a redesign specification. Later PRs may refine navigation, hierarchy, and component reuse, but should do so deliberately against this baseline.

## 1. Design principles

1. **Publication before database.** Sports Passport should feel like a personal annual media guide and almanac, not an analytics dashboard with sports data.
2. **The archive is the source of truth.** Years, teams, venues, geography, journeys, rankings, and analytics are different editorial views of one underlying record.
3. **Warm archival character.** Cream paper, navy ink, restrained red/gold accents, serif display typography, and subtle rules establish the publication voice.
4. **Editorial hierarchy over feature density.** The visitor should always know what the page is primarily about, even when many valid metadata signals are available.
5. **Curated and factual layers stay distinct.** Archive facts, confidence labels, and reconstructed records should not be confused with personal rankings or editorial commentary.
6. **Annual editions are a signature format.** Each year should read as a season/media-guide edition, with the current year visibly live and historical years stable.
7. **Mobile remains readable and navigable.** Dense publication layouts should reflow rather than simply shrink.

## 2. Canonical style sources

The current foundation is primarily defined by:

- `assets/site.css` — shared palette, typography, shell, navigation, cards, panels, stats, filters, focus states, and responsive behavior.
- `assets/home.css` — launch/homepage composition and current-season treatment.
- page-specific stylesheets and inline page styles — annual editions, rankings, profiles, geography, journeys, analytics, and other editorial views.

The consolidation goal is not to eliminate page-specific art direction. It is to move repeated global patterns into shared components while preserving intentional publication-specific treatments.

## 3. Core palette

Canonical shared tokens from `assets/site.css`:

| Role | Token | Value |
| --- | --- | --- |
| Paper | `--paper` | `#f4ecdc` |
| Warm white | `--white` | `#fffdf8` |
| Primary ink | `--ink` | `#112b3c` |
| Muted text | `--muted` | `#736d64` |
| Rule / border | `--line` | `rgba(17,43,60,.16)` |
| Editorial red | `--red` | `#b7443a` |
| Blue | `--blue` | `#315f84` |
| Gold | `--gold` | `#c49b48` |
| Green | `--green` | `#426d5d` |

The cream/navy foundation is part of the Sports Passport identity and should remain distinct from the warmer minimalist Adventure site and the dark technical Life Map.

Accent colors should communicate meaningful editorial categories or status. Avoid adding colors solely to make a component look different.

## 4. Typography

Canonical stacks:

- Display serif: Georgia / Times New Roman fallback.
- Interface/body sans: Inter / system sans-serif fallback.

Hierarchy rules:

- Large serif headlines carry the media-guide/publication identity.
- Sans-serif copy, controls, metadata, and navigation provide clarity and contrast.
- Uppercase kickers are compact editorial labels, usually red.
- Body copy should maintain comfortable reading sizes and line height.
- Metadata can be quieter, but important confidence/status information must remain readable.

Do not replace the serif/sans contrast with a single generic UI typeface.

## 5. Layout and spacing

- Canonical shell width is approximately `1240px`.
- Warm paper is the page field; warm-white panels/cards sit above it.
- Sections are separated primarily by whitespace and hierarchy rather than heavy chrome.
- Cards use moderate radii, thin navy-tinted borders, and restrained shadows.
- Hero treatments may be more expressive than ordinary content panels.
- Dense multi-column layouts should collapse predictably on tablet and mobile.

Avoid solving hierarchy problems by wrapping every section in another bordered card.

## 6. Core components

### Publication masthead and navigation

The long-term target is one recognizable Sports Passport masthead/global navigation system across all pages.

Current page-specific navigation variants are valid historical implementations but should not multiply further.

Rules for future consolidation:

- global navigation identifies the publication,
- contextual navigation explains the local section,
- the two levels should not compete visually,
- mobile navigation must remain easy to scan and touch,
- existing public URLs and deep-link behavior must remain stable.

### Hero

Typical hierarchy:

- kicker / status,
- oversized serif title,
- short editorial deck,
- supporting lifetime or season statistics.

The hero should establish the page's editorial purpose before filters or detailed metadata appear.

### Stats

- Strong serif value.
- Quiet uppercase sans label.
- Warm-white/light panel.
- Used as summary evidence, not as the dominant visual identity.

### Cards and portals

- Clear title and purpose.
- Muted explanatory copy.
- Strong but restrained terminal link/action.
- Hover may lift slightly.
- Avoid making every secondary destination visually equivalent to a primary destination.

### Rankings

Top Tens and curated rankings are editorial content, not computed analytics.

- Rank should be immediately readable.
- Podium emphasis is appropriate.
- The #1 item may receive stronger treatment.
- Experience rankings and venue rankings should remain conceptually distinct.
- Links to exact events/years/venues support the archive but should not overpower the ranked item.

### Annual editions and event cards

Annual editions are one of the site's signature formats.

Priority order for event information:

1. date and event/matchup,
2. result / teams / venue,
3. sport and season context,
4. confidence / favorite / ranking annotations.

If multiple annotations are present, they should not all receive equal badge prominence.

### Badges and confidence labels

Badges should be reserved for states that benefit from rapid scanning.

Suggested semantic priority:

- **Primary state:** current/in progress, result/status where relevant.
- **Archive confidence:** verified/notional or equivalent provenance.
- **Editorial annotation:** favorite team, Top 10, signature moment.

Confidence/provenance is factual metadata. Personal rankings are editorial metadata. Their visual treatment should remain distinguishable.

## 7. Information architecture baseline

Sports Passport contains many legitimate views of the same archive. The design audit identified the need for clearer primary-versus-secondary hierarchy, but no routes should be removed casually.

A useful conceptual model for future navigation work is:

- **Years** — chronological annual editions.
- **Teams** — recurring team histories and dossiers.
- **Places** — geography, venues, cities, and maps.
- **Stories** — journeys, chapters, family/team threads, and curated narrative views.

Secondary/editorial destinations include Top Tens, Hall of Fame, lifetime analytics, and methodology/about content.

This is a hierarchy model, not an instruction to remove existing destinations.

## 8. Responsive and accessibility baseline

- Preserve visible keyboard focus states.
- Existing shared controls commonly target at least 44px height; retain that standard.
- Do not use color alone to communicate team/sport/status meaning.
- Long team, venue, and event names must wrap safely.
- Rankings and event cards must remain readable without horizontal page scrolling.
- Horizontally scrollable year/filter navigation must provide an obvious, usable mobile experience.
- Interactive charts or maps should retain text alternatives/context and useful touch targets.

## 9. Change protocol

For design-system consolidation:

1. Start from green `main`.
2. One concern per PR.
3. Prefer 1–5 handwritten files changed where practical.
4. Do not mix event/archive data edits into visual-system PRs.
5. Preserve clean URLs, legacy implementation targets, and deep links.
6. Check the changed page and at least one neighboring page that should remain unchanged.
7. Run all repository validation before merge.
8. Merge and verify deployment before stacking another visual PR in the same area.
9. Prefer additive shared components first; perform larger CSS refactors only after visible behavior is proven.

## 10. Known consolidation targets

The August 2026 site audit identified these follow-on areas. They are intentionally **not** changed by this baseline PR:

- introduce a canonical global masthead/navigation pattern,
- retain contextual secondary navigation without page-to-page drift,
- simplify homepage hierarchy so primary and secondary destinations are clearer,
- reduce badge competition on annual/event pages,
- preserve the annual media-guide identity while consolidating repeated CSS,
- strengthen the thin shared Alex Ford identity layer across sub-sites,
- keep Sports Passport visually distinct rather than flattening it into the Adventure or Life Map themes.

This document is the reference point for those later PRs.
