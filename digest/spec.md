# Daily Digest — content specification

This is the source of truth for what the daily digest contains. It is duplicated
verbatim into the Routine prompt so that a firing never depends on repo state.
**If you edit this file, you must also update the Routine** (see README.md).

## Recipient profile

| Field | Value |
|---|---|
| Recipient | sonya.fan@gmail.com (HTML email; markdown archived in-repo) |
| Delivery time | 08:00 Asia/Taipei (UTC+8, no DST) = `0 0 * * *` UTC |
| Student location | Taiwan-based, Taiwanese passport |
| EdTech lens | Parent / homeschool |
| Austin link | Summers only — mother is a UT Austin visiting scholar teaching a summer course. Non-residents, no family in Austin. |

## Section 1 — Interactive BYOD learning tools

Surface **2–3 items**, newest first. In scope:

- Learning apps, educational games, and classroom-practice patterns designed
  for BYOD (bring-your-own-device) settings, where interactivity is the point.
- Bias hard toward things a **family can adopt directly**: name the cost, the
  platform, and whether a child can use it independently or needs an adult.
- Prefer items from the last 30 days. If nothing is genuinely new, say so
  plainly and surface the best evergreen option instead of padding.

Out of scope: district procurement news, enterprise pricing, LMS admin
features, funding rounds with no product change.

## Section 2 — Study-abroad opportunities (high school)

Surface **2–3 programs**. Hard filters:

- Applicant holds a **Taiwanese passport** — only list programs that accept
  international applicants. Programs restricted to US citizens/permanent
  residents (e.g. most federally funded ones) are out unless they run a
  separate international track. RSI and SSP both do.
- **Academically challenging** — research, selective seminar, or olympiad
  calibre. Not tourism, not general "summer camp".
- **Generous stipend or full funding** — the program pays the student, or
  covers tuition + room + board. A partial-discount scholarship is not enough;
  if funding is need-based only, label it as such.

For each program give: name, host institution, eligibility, funding detail,
**application deadline**, and the official URL. Deadlines matter more than
descriptions — lead with them, and mark anything closing within 30 days.

## Section 3 — Summer camps and activities near UT Austin

Surface **2–3 items**. **Summer only** — the family is in Austin solely while
the mother teaches, so term-time Austin activities are useless to them.
**Prefer in-person**: being physically on campus is the whole point, which
makes a virtual-only program worth less here than it would be otherwise. Say
which it is either way — several UT programs (SEE, the Summer STEM Learning
Academy) are virtual.

Sources: the [UT Youth Protection Program camps
directory](https://youthprotectionprogram.utexas.edu/camps/) is the most
complete index of UT camps. Also Women in STEM high school camps, UTeach
Outreach, STEM Starts (SEE, SLA, CEO day camps, UT PREP), Cockrell School
MITE, School of Design and Creative Technologies Summer Institutes, and
College of Natural Sciences listings. Strong non-UT Austin-area options count
too.

### Three filters specific to this section

**Not Texas-residency-restricted.** They are non-residents. Exclude
resident-only programs; note out-of-state pricing where it applies.

**Visa-compatible.** Taiwan is a Visa Waiver Program country, so the family
likely travels on ESTA or a B-2 visitor visa. B-2/ESTA permits short,
part-time, **non-credit recreational** study — ordinary summer camps are fine
— but **not** full-time or for-credit study. Flag any for-credit or full-time
pre-college program as "check visa status before applying" rather than
presenting it as available. Exception worth raising: if the mother holds J-1
visiting scholar status and the student is her J-2 dependent, study
restrictions are much looser, which would widen the options considerably.

**Cost always stated.** This section does **not** inherit Section 2's funding
bar — most of these charge, and that is fine. State the price every time (at
setup: UT PREP around $2,700 with scholarships; Women in STEM virtual
academies and 1-day camps $200, 2-day camps $350 — reverify, never quote
stale figures), give grade eligibility, and flag anything free or
scholarship-supported as the most valuable find.

### The affiliation lead

Whether UT programs discount or prioritise dependents of faculty, staff, or
visiting scholars was **not confirmed during setup** — searches turned up
nothing, so it must not be asserted. But the mother's own department is a
direct route both to that question and to informal lab or research shadowing
that is never advertised. Raise it as a lead when a program looks like a fit.

### Timing

Deadlines follow Section 2's verification discipline. Summer 2027
registration was expected to open January 2027, so outside that window most
items are **"mark the date"**, not "apply now" — say which. Rotate the
featured camps.

## Section 4 — Book of the day

Pick **one** book and write a big-concepts summary (roughly 300–500 words):
the central argument, 3–5 key ideas, and why it still matters. Not a plot
recap — concepts.

### Source rotation

Rotate by day so the sources stay balanced. Compute
`index = (days since 1970-01-01 UTC) mod 6`:

| index | Source |
|---|---|
| 0 | GatesNotes book recommendations |
| 1 | NYT — The 100 Best Books of the 21st Century |
| 2 | Le Monde's 100 Books of the Century (1999 Fnac/Le Monde poll, 100 titles) |
| 3 | Princeton / Harvard required reading and professor-recommended lists |
| 4 | Nature & Science editors' annual science-book picks |
| 5 | Booker Prize winners — take the six "Best of the Booker" (2008) finalists first, then other winners |

### De-duplication

Before choosing, read `ledger.md` and **never repeat a title already listed**.
After writing the digest, append the new title to it. If the day's source is
exhausted, move to the next index and note the shift.

## Format

Markdown, written to `archive/<YYYY-MM-DD>.md`, and HTML for the email.
`# Daily Digest — <YYYY-MM-DD>`, then one `##` per section (four of them). Every
factual claim carries a source link. Where a search turned up nothing solid,
write "nothing new found today" — do not invent programs, deadlines, or
prices. Fabricated application deadlines are the worst possible failure here.
