# Daily digest

A scheduled Routine that assembles a three-part digest every morning and files
it to Google Drive. Unrelated to the Chinese101 app itself — this directory is
just where the configuration lives so it is version-controlled and editable.

## How it runs

A Claude Routine (scheduled trigger) fires **daily at `0 0 * * *` UTC**, which
is 08:00 Asia/Taipei. Taiwan observes no DST, so this stays correct year-round
with no seasonal adjustment.

Each firing starts a **fresh session** with the Google Drive connector attached.
It runs the searches, writes the digest, saves it to Drive, and updates the
ledger.

## Delivery

Currently **Google Drive only**. Email was the original request, but the Gmail
connector is installed on the account without being enabled in the session that
created the Routine, and a Routine can only carry connectors its creating
session already holds.

To switch on email delivery:

1. Enable the Gmail connector in the Claude Code session/chat settings.
2. In a session that has Gmail live, update the Routine to add a final step
   sending the digest body to sonya.fan@gmail.com, and re-create it with
   `connectors: ["Google Drive", "Gmail"]`.

Until then the digest lands in Drive as `Daily Digest YYYY-MM-DD`.

## The ledger

`Daily Digest Book Ledger` is a Google Drive document holding one line per book
already covered (`YYYY-MM-DD — Title — Author — source`). It exists to stop the
rotation repeating itself. The first firing creates it if absent.

The ledger lives in Drive rather than in this repo deliberately: a daily commit
purely to record a book title would bury the app's real history in noise.

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
