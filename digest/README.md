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

## 2026-10-03 — Section 5 added (competitions for the 11-year-old)

The family confirmed a **second child, aged 11**, and asked for "any kind of
contest or competitions that a 11-year-old could apply for". Changes made:

- `spec.md` gained a `Section 5` with four filters (age/grade, reachable from
  Taiwan, entry route for a homeschooler, cost and deadline) and its standing
  findings. The profile table now lists both children.
- The Routine prompt (`trig_01MSJN1vFHCLhPKNo1V1btEo`) was updated in place via
  `update_trigger` — not recreated, so run history is preserved. It now says FIVE
  sections, carries the two-child profile, and seeds Section 5 with the verified
  findings below so no firing re-derives them.
- The email footer rule gained "· contests for the 11-year-old".
- Section 3 now notes which child each camp fits; BrainPOP moved from "below
  level" to "possibly relevant for the younger child".
- First delivery went out the same day as a **supplement email**, archived at
  `archive/2026-10-03-supplement-competitions.md`, rather than waiting for the
  next 08:00 Taipei firing.

**The one finding worth protecting:** Caribou Contests ceased operations on 11
August 2025 after its founder's death, and is still recommended across
unmaintained blogs and school lists. The Routine prompt now forbids recommending
it.

## 2026-10-12 — Sections 6 and 7 added (collaboration, challenges)

The family asked for "more international collaboration opportunities" and "some
challenges". Both were posed back as questions ("what can be on the list?"), so
candidates were researched first and then put to them via AskUserQuestion.

**Their choices:** all three readings of "challenges" (team challenge with judges,
a recurring problem to attempt, an honest obstacles audit); and alternating days
rather than two daily sections or folding into existing ones.

**Changes made:**
- `spec.md` gained Section 6 (international collaboration, EVEN dates) and Section
  7 (challenges, ODD dates), each with filters, a verified pool, and leads.
- The Routine prompt (`trig_01MSJN1vFHCLhPKNo1V1btEo`) was updated in place —
  not recreated, so run history survives. It now says SIX sections on any given
  day (1–5 daily, plus 6 or 7 by date parity) and carries three numbered standing
  rules.
- **Standing Rule 3 is the alternation mitigation and is mandatory:** any dated
  item from section 6 or 7 still appears in the daily deadline lead on EVERY day,
  regardless of parity. The risk of a deadline landing on an off day was flagged
  to the family, who chose alternation anyway; this removes the failure mode
  rather than just accepting it. It is the mechanism that lost the September
  physics-olympiad window.
- Standing Rule 1 was widened: the residence filter applies to PLATFORMS too, not
  only programmes (the Khanmigo lapse).
- A new profile line: **neither child's gender has ever been stated — never
  assume it.** Technovation has a gender-based eligibility condition, so the
  condition is stated and the family decides.
- Footer rule extended with "collaboration (even days) · challenges (odd days)".
- First delivery went out same-day as a supplement, archived at
  `archive/2026-10-12-supplement-sections-6-and-7.md`.

**The framing worth keeping**, which emerged from building Part C: everything
blocked is blocked by an institution; everything open can be started this
afternoon.
