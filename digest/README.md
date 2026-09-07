# Daily digest

A scheduled Routine that assembles a three-part digest every morning and files
it to Google Drive. Unrelated to the Chinese101 app itself — this directory is
just where the configuration lives so it is version-controlled and editable.

## How it runs

A Claude Routine (scheduled trigger) fires **daily at `0 0 * * *` UTC**, which
is 08:00 Asia/Taipei. Taiwan observes no DST, so this stays correct year-round
with no seasonal adjustment.

Each firing resumes a bound session, runs the searches, emails the digest, then
writes `archive/<date>.md`, appends to `ledger.md`, and pushes to this branch.

## Delivery

The digest is **emailed to sonya.fan@gmail.com as formatted HTML** each morning
by Routine `trig_01MSJN1vFHCLhPKNo1V1btEo`, with a markdown copy archived to
`archive/<date>.md` on this branch.

### Why the Routine binds to a session

Per-Routine connector grants are unavailable for this organization, so a
Routine that starts a *fresh* session each fire gets web search and git and
nothing else — no Gmail, no Drive. The working Routine therefore **fires into
an existing session** (`persist_session: true`), which resumes that
conversation with its connectors, Gmail included, still attached.

The cost of that design is a dependency on the bound session surviving. If it
is archived or reclaimed, the digest stops. Two mitigations:

- `trig_01JKnYU9dZM9qtivxGFwvWgJ` is kept on **standby, disabled**, prefixed
  `[STANDBY]`. It uses the fresh-session design: no Gmail, but it writes the
  digest to this repo and its completion-notification email carries the closing
  summary. Re-enable it if the bound Routine goes quiet.
- Rebinding is cheap: create a new Routine from any session that holds Gmail,
  reusing the prompt stored on the current one.

### Google Drive

Not used. The connector's token expired during setup, and it is unavailable to
fired sessions for the same reason Gmail is. Email plus the repo archive covers
the need; a Drive copy would add a third place to look.

## Editing the digest

The digest runs **four sections**: interactive BYOD learning tools, funded
study-abroad programs, summer camps and activities near UT Austin, and the
book of the day.

`spec.md` is the source of truth for content. It is **copied into the Routine
prompt**, so editing the file alone changes nothing — after editing, ask Claude
to update the Routine's prompt to match. The duplication is intentional: a
firing then never depends on this branch being present or current.

The email's visual design is pinned by reference to `archive/2026-09-07.md`,
the hand-built sample. Restyling means updating the Routine prompt's step 3.

## Source-pool sizes

Worth knowing when tuning the rotation, since the six sources are wildly
uneven:

| Source | Approx. pool |
|---|---|
| Le Monde 100 Books of the Century | exactly 100, fixed since 1999 |
| NYT 100 Best Books of the 21st Century | exactly 100, fixed since 2024 |
| GatesNotes | ~200+, grows a few per year |
| Nature & Science annual picks | ~200+, grows ~20/year |
| Princeton / Harvard reading lists | fuzzy — no single canonical list |
| Best of the Booker | **6** |

"Best of the Booker" was a one-off 2008 public vote won by Salman Rushdie's
*Midnight's Children*, with five other finalists — six books total. That slot is
therefore broadened to Booker winners generally, with those six taken first.

At one book per day the combined pool runs roughly two years before the finite
lists are exhausted.
