# Daily digest

A scheduled Routine that assembles a three-part digest every morning and files
it to Google Drive. Unrelated to the Chinese101 app itself — this directory is
just where the configuration lives so it is version-controlled and editable.

## How it runs

A Claude Routine (scheduled trigger) fires **daily at `0 0 * * *` UTC**, which
is 08:00 Asia/Taipei. Taiwan observes no DST, so this stays correct year-round
with no seasonal adjustment.

Each firing starts a **fresh session**, runs the searches, writes the digest to
`archive/<date>.md`, appends to `ledger.md`, and pushes to this branch.

Routine id: `trig_01JKnYU9dZM9qtivxGFwvWgJ`.

**Fired sessions get no connectors.** Attaching connectors to a Routine is not
available for this organization, so a firing has web search and git and nothing
else. The digest therefore lives in this repo, which always works.

## Delivery

Two channels, neither of which is the Gmail send originally asked for:

1. **The repo** — full digest at `archive/<date>.md`, pushed to this branch.
   Authoritative and complete.
2. **Routine completion email** — the Routine has push and email notifications
   on, so the ~200-400 word closing summary reaches the account's inbox each
   morning. A summary, not the whole digest, but it does arrive by email.

Real Gmail delivery needs the Gmail connector enabled in the session that
creates the Routine. As of setup it is installed on the account but not enabled
in-session, and per-Routine connector grants are unavailable for this org
anyway. The likely workaround is to create the Routine from the claude.ai
Routines UI in a context where Gmail is live.

## The ledger

`ledger.md` holds one line per book already covered
(`YYYY-MM-DD — Title — Author — source`), to stop the rotation repeating
itself. Kept in-repo because fired sessions have no other durable store.

## Editing the digest

`spec.md` is the source of truth for content. It is **copied into the Routine
prompt**, so editing the file alone changes nothing — after editing, ask Claude
to update the Routine's prompt to match. The duplication is intentional: it
means a firing never depends on this branch being present or current.

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
