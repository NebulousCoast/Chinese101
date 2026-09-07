# Daily Digest — content specification

This is the source of truth for what the daily digest contains. It is duplicated
verbatim into the Routine prompt so that a firing never depends on repo state.
**If you edit this file, you must also update the Routine** (see README.md).

## Recipient profile

| Field | Value |
|---|---|
| Recipient | sonya.fan@gmail.com (HTML email; markdown archived in-repo) |
| Delivery time | 08:00 Asia/Taipei (UTC+8, no DST) = `0 0 * * *` UTC |
| Student location | Taiwan-based |
| EdTech lens | Parent / homeschool |
| Local area | Greater Austin, Texas (section 3) |

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

- Applicant is **based in Taiwan** — only list programs that accept
  international or Taiwan-resident applicants. Programs restricted to US
  citizens/permanent residents (e.g. most federally funded ones) are out
  unless they run a separate international track.
- **Academically challenging** — research, selective seminar, or olympiad
  calibre. Not tourism, not general "summer camp".
- **Generous stipend or full funding** — the program pays the student, or
  covers tuition + room + board. A partial-discount scholarship is not enough;
  if funding is need-based only, label it as such.

For each program give: name, host institution, eligibility, funding detail,
**application deadline**, and the official URL. Deadlines matter more than
descriptions — lead with them, and mark anything closing within 30 days.

## Section 3 — Summer camps and activities near UT Austin

Surface **2–3 items**: summer camps, academies, research programs,
competitions, and term-time enrichment for a high schooler in the greater
Austin, Texas area.

UT Austin's own offerings are the anchor:

- Women in STEM high school camps and academies
- UTeach Outreach camps
- STEM Starts — Summer Engineering Experience (SEE), Summer STEM Learning
  Academy (SLA), Consider Every Option (CEO) day camps
- Cockrell School — My Introduction to Engineering (MITE)
- College of Natural Sciences STEM camp listings

Strong non-UT options in the Austin area belong here too.

**This section deliberately does NOT inherit Section 2's funding bar.** Most of
these charge money, and that is fine — the point is proximity and fit, not
funding. Instead:

- **Always state the cost.** At setup, Women in STEM virtual academies and
  1-day camps ran $200 and 2-day camps $350. Reverify every time; never quote
  a stale figure.
- Say whether it is **in-person or virtual** — several UT programs are
  virtual, which changes the value of "near Austin" entirely.
- Give **grade eligibility** (many are rising 10th–12th, MITE is current
  juniors).
- **Flag anything free or scholarship-supported.** Those are the most valuable
  finds in this section.

Registration and deadlines follow Section 2's verification discipline:
"confirm on official site" when unverified. Summer 2027 registration was
expected to open in January 2027, so outside that window most items are
**"mark the date"** rather than "apply now" — say which, rather than implying
a live application. Rotate the featured camps; do not repeat the same one
daily.

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
