# Flowchart

**Best for:** decision logic, algorithms, user-facing branching flows ("Should I…?"), onboarding routing, support-triage trees.

## Layout conventions
- Shape carries type, not color:
  - **Oval** (`rx=20`) — start / end
  - **Rectangle** (`rx=6`) — step / action
  - **Diamond** — decision (≤3 exits)
  - **Small filled ink dot** (`r=4`) — merge point where branches rejoin
- Flow runs top→down. From a diamond, conventional exits: Yes to the right, No below — but label every outgoing arrow regardless.
- Use coral on the happy path *or* on the single most consequential decision — never on every decision.
- If two arrows must cross, use a small arc jump on one so the crossing is readable.

## Iterate-until-converged (loop with a stop)

When the logic repeats until a test passes (training loops, EM, Newton steps, retry logic) the shape is a Flowchart whose last decision sends one exit back to the first loop node and the other to a **Stop pill** (`rx=20`). Keep the spine vertical down the left of the sheet, route the `否` back-edge as a single `r=8` elbow in the margin that re-enters the first loop node from its left edge, and put the update it performs (`θ_old ← θ_new`) in a note beside the diamond rather than on the stroke. Teaching it? Pair it with a worked example: use [Explainer sheet](type-explainer-sheet.md).

## Anti-patterns
- Using fill color to signal node type (shape does that).
- Decision diamond with 4+ exits — refactor into nested diamonds.
- Unlabeled decision branches.

## Examples
- `assets/example-flowchart.html` — minimal light
- `assets/example-flowchart-dark.html` — minimal dark
- `assets/example-flowchart-full.html` — full editorial
