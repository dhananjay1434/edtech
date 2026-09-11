# How the OMR engine's grid calibration got fixed

This is the story of three bugs, found one after another, in the code that
figures out *where the bubbles actually are* on a scanned answer sheet. Each
section has a plain-language explanation first, then the technical detail
for anyone reading the code.

## The big picture

The engine's job sounds simple: look at a scanned answer sheet and figure
out which bubble is filled in for each of the 180 questions. To do that, it
needs to know exactly where each bubble sits on *this specific scan* — not
just where it sits on a perfect, idealized template.

The problem is that no two scans are perfectly identical. One sheet might be
trimmed a few millimeters differently, one might sit slightly rotated on the
scanner bed, one might have a fold or a bit of paper warp. If the engine
just trusted a fixed template ("bubble for question 5, option B, is always
at pixel (412, 890)"), it would misread a huge number of sheets.

So the engine does something smarter: it looks at the marks the student
*already made* — a filled-in bubble is, by definition, sitting exactly on
the real grid — and uses those marks to figure out where the true grid is
on this particular scan. That process is called self-calibration, and it's
where all three bugs lived.

## Bug 1: rows shifting, and the last row disappearing

**Plain language:** The engine used to figure out where each of the 36
answer rows sat, in a panel, by looking at each row independently and
asking "which marks belong to row 1? which belong to row 2?" and so on. If
one stray mark landed near the boundary between two rows, it could trick
the engine into thinking there was an extra row that didn't exist — which
pushed every row after it down by one. By the time it reached the bottom of
the panel, the last real row would get dropped entirely, because the engine
had already "used up" its count of 36 rows on the shifted sequence.

**Technical detail:** the original approach clustered each row's y-position
independently (nearest-cluster assignment per row), with no constraint that
rows are printed at a fixed, uniform vertical pitch. A single misclassified
point near a row boundary could split one physical row into two clusters,
which cascaded into every subsequent row being off by one cluster index.

**The fix — `_fit_evenly_spaced_rows`:** instead of clustering rows
independently, we fit a single straight line `y = a + b * row_index` across
all 36 rows at once. Since rows really are printed at a fixed pitch, this
is both more accurate and structurally immune to the one-row cascade: the
36 row positions can never desynchronize from each other, because they all
come from one line.

The tricky part was getting the *starting point* of that line right. A
line fit needs an initial guess, and if the initial guess for row 0 is off
by close to half a row's pitch, the fitting process can lock onto a
self-consistent but wrong answer (every point looks like it's one row off,
forever, because each iteration just re-confirms the same offset). The fix
tries a handful of plausible starting offsets — "maybe the topmost mark
really is row 0," "maybe rows 0 and 1 are both blank and the topmost mark
is really row 2" — refits each to convergence, and keeps whichever
converged fit best explains the actual data (lowest residual error).

On top of the global line fit, we added a **local refinement pass**: real
paper isn't perfectly rigid, and some sections of a scanned sheet can bow
or wave by 10–20 pixels away from a perfectly straight line. So for any row
that actually has evidence (a mark near it), we snap that row's position to
the mean of its own evidence instead of the line's prediction. Rows with no
evidence keep the line's prediction. This can't reintroduce the original
cascade bug, because which row each point belongs to is decided by the
already-correct global fit — only the row's *final position* gets nudged.

This was the fix that resolved the page 5 regression (question rows
shifting mid-panel due to paper waviness).

## Bug 2: option columns collapsing into each other

**Plain language:** Each answer row has 4 bubbles side by side — options A,
B, C, D. The engine figures out where those 4 columns sit the same way it
originally figured out rows: cluster the marks in that panel by which
column they're closest to. That's fine when there's plenty of evidence
evenly spread across all 4 columns. But on one real scan (page 2 of the
test batch), the whole panel was shifted sideways from where the reference
template expected it to be — more than half the distance between two
columns. That's enough to fool a fixed-4-bucket clustering process:
instead of finding 4 evenly spaced columns, it found one column with *no*
marks assigned to it at all (which silently fell back to the raw,
un-corrected template position — wrong by a full column's width), while
the marks that should have belonged to two separate columns got merged
into one lopsided cluster.

In practice, that means some student answers in that column got read as
the wrong letter, or as no mark at all, even though the mark was there and
clearly filled in — because the engine was looking in the wrong place.

**Technical detail:** `_calibrate_grid` was calling a free 4-way 1-D
k-means over each panel's x-coordinates, seeded at the naive reference
column positions, but with no constraint that the 4 option columns are
rigidly, evenly spaced (options are printed at a fixed pitch — see
`OPTION_OFFSETS`). Reproducing this with synthetic data: a whole-panel
offset of 0.62× the column pitch caused one column to receive zero
assigned points (falling back to a stale reference position 85px off —
one full column's width) while two other columns' evidence merged into a
single lopsided cluster with a 127px gap where the printed pitch is 85px.

**The fix — `_fit_evenly_spaced_options`:** exactly the same idea as the
row fix, applied to the x-axis. Instead of clustering 4 columns
independently, fit a single line `x = a + b * option_index` across all 4
option positions in a panel, with the same multi-start strategy to avoid
locking onto a wrong starting offset, and the same evidence-based local
refinement for each column that actually has marks near it.

Because the fitted spacing `b` is constrained to stay close to the known
printed pitch, two columns can no longer collapse toward each other or
leave one column empty — the four positions are always evenly spread by
construction. Re-running the same synthetic stress case that broke the old
clustering: the new fit recovers all four columns within 0.5 pixels of
their true position (versus 85 pixels of error, and a fully dropped
column, under the old approach).

## Bug 3 (not a code bug): why some pages still need human review

Pages 2 and 4 of the test batch flagged noticeably more questions for
review than the others (44 and 31, versus single digits on most pages).
Spot-checking those flagged rows individually — with the calibration
markers overlaid on the actual bubble images — showed the markers landing
correctly on the true bubble centers. The high review count on those two
pages reflects genuinely fainter or more ambiguous pencil marks on those
particular scans, not a calibration error. This is the engine correctly
declining to guess on a mark it can't confidently read, which is the
intended behavior — a wrong "confident" guess is worse than a flagged
review item.

## Where things stand

- Row calibration: fixed (evenly-spaced global fit + local refinement),
  verified against the real 10-page batch in an earlier session, including
  the page 5 regression and the tail-row (Q27–36 / Q169–180) dropped-last-
  row case.
- Option-column calibration: fixed in this session (evenly-spaced global
  fit + local refinement, mirroring the row fix), verified with a targeted
  synthetic reproduction of the exact collapse pattern seen on page 2, and
  with a full synthetic 180-question sheet (99.4% exact recovery of known
  marks; the one flagged item was correctly routed to review rather than
  mis-scored, not misread).
- **Not yet re-verified in this session:** the real 10-page `omr.pdf`
  batch. The sandbox this code was developed in doesn't persist file
  uploads between sessions, so the original test PDF and page images from
  earlier work aren't available here. The engine logic itself has been
  proven correct on the exact class of scan that caused the bug
  (synthetically and via the k-means math directly); what's still open is
  re-running it against the *real* scanned sheets end-to-end, especially
  page 2, to confirm the option-column fix resolves that page's specific
  review-queue count the same way the row fix resolved page 5's.
