# Math notation in SVG

Routed from the Explainer sheet and any diagram that prints a formula. Use it when a node, panel, or axis needs `θ_old`, `r_nk`, `σ²`, `ℓ(θ)`, or a similar symbol.

SVG has no math layout engine and `<foreignObject>` breaks PNG and Figma export, so notation is built from plain `<text>` and `<tspan>`. Keep it **small, regular, and verifiable**: if a formula needs a fraction bar, a summation with limits above and below, or a matrix, it does not belong on a diagram. Show the idea in words and put the full equation in the prose around the figure.

---

## 1. Where formulas live

| Slot | Face | Size |
|---|---|---|
| Formula inside a node | Geist Mono 500 | 14 (presentation), 12 (standard) |
| Formula in a chart panel | Geist Mono 500 | 12 |
| Parameter readout under a chart | Geist Mono 400 | 11 |
| Inline symbol in a Han sentence | the sentence's sans stack | same size as the sentence |

Mono is correct here: a formula is technical content, and fixed advance keeps `=` signs and bars aligned across lines. Sizes sit inside the named **formula line** exception in [output-spec.md](output-spec.md); sub- and superscripts fall in the dense-annotation range (7 to 11).

Greek and a few symbols (`θ π μ σ ℓ Σ ← → ≈ ²`) may be missing from the mono face. Keep the skin's stack `'Geist Mono', ui-monospace, monospace`: the generic `monospace` resolves to a system face with Greek coverage, and the skin linter rejects named fallbacks outside the approved families.

---

## 2. Subscripts and superscripts

Use a shrunken `<tspan>` with a relative `dy`, and undo the shift on the next run. **Do not use `baseline-shift`**: renderers disagree on it, and the export helpers drop it.

```svg
<!-- r_nk = P(z_n = k | x_n, θ_old) at size 14 -->
<text font-family="{mono}" font-size="14" font-weight="500" fill="{ink}">
  <tspan>r</tspan><tspan font-size="10" dy="3">nk</tspan>
  <tspan dy="-3"> = P(z</tspan><tspan font-size="10" dy="3">n</tspan>
  <tspan dy="-3"> = k | x</tspan><tspan font-size="10" dy="3">n</tspan>
  <tspan dy="-3">, θ</tspan><tspan font-size="10" dy="-5">old</tspan>
  <tspan dy="5">)</tspan>
</text>
```

| Mode | `dy` to enter | Size |
|---|---|---|
| Subscript | `+3` at base 14, `+3` at base 12 | `round(base × 0.75)`, never below 7 |
| Superscript | `-5` | same |
| Return to baseline | the **negative** of the last shift | base |

Track the running offset rather than hand-counting. The reference builder keeps a helper (`math_()` in `scripts/build-explainer-sheet-example.py`) that takes `(text, mode)` pairs and emits the `dy` values.

Rules:

1. **No whitespace between tspans in the markup** that would add a visible gap; put intended spaces inside the text, as in `<tspan dy="-3"> = k</tspan>`.
2. Keep sub/superscript text to **three characters or fewer**: `nk`, `old`, `new`, `(0)`. Longer indices are words, so move them out of the formula.
3. A superscript on a symbol that already carries a subscript (`σ_k²`) uses the Unicode glyph (`²`) rather than a second shift.
4. Prefer Unicode for symbols that exist: `θ π μ σ ℓ Σ ← → ≈ ≤ ≥ ∈ ∑` and the superscript digits `⁰¹²³`. A glyph survives export, copy-paste, and screen readers; a shifted tspan survives only as a sequence of characters.

---

## 3. Notation conventions for diagrams

- **Name the symbols the reader needs, nothing else.** On the sheet, `θ = {π, μ, σ²}` is enough; do not define every symbol the equation uses.
- **A formula always has a plain sentence beside it** (see [type-explainer-sheet.md § 3.1](type-explainer-sheet.md)). The formula is for the expert, the sentence for everyone.
- **Keep one symbol system.** If the left pane writes `θ_old`, the footer and the caption write `θ_old` too, not `θ^(t)` in one place and `θ_old` in another.
- **Use `←` for assignment and `=` for equality.** `θ_old ← θ_new` is an update, `r_nk = P(…)` is a definition.
- **Numbers printed with symbols use the true minus `−` (U+2212)**, not a hyphen, and fixed decimals: `μ = (−0.96, 1.10)`.
- **Never let a formula carry the focal accent by itself.** Accent belongs to the node or heading around it.

---

## 4. Micro-charts used in worked examples

These are drawn as plain SVG paths, no chart library. Each fits inside an Explainer-sheet panel (about 280 × 100 px).

### 4.1 Density curve (`<path>` of 101 samples)

Sample the function every 0.08 across the x-range and join with `L`. Clamp at the top gridline so a tall peak cannot escape the panel. Draw order: whole (`ink` 2.4), part A (`muted` 1.4), part B (`muted` 1.4 dashed `5,4`), then data ticks.

### 4.2 Data rug (ticks)

One short vertical line per observation just below the baseline (8px, `ink` 1.2). It shows where data sit without a scatter, and the same ticks appear on both panels of a before/after pair so the data visibly stay put while the curves move.

### 4.3 Proportion strip

A white rectangle (`ink` 1 stroke) with a `muted` fill of width `W × value`. One strip per item in a row; value printed below in mono 11. The split is the point, so the unfilled portion is the complement, never a different colour.

### 4.4 Sparkline

One polyline in `ink` 2.4 over a baseline and a y-axis stub. Map the value range to the panel height with the **first value at the bottom and the last at the top** unless the series is not monotonic, in which case use min/max. Print only: axis name, final value, and iteration count.

### 4.5 Axes and gridlines

Baseline in `muted` 1; one dotted reference line in `rule-solid` `1,3`; end ticks and a centre tick only. No box around a plot. A box turns a panel into a card.

---

## 5. Checklist

- [ ] Every subscript/superscript uses `dy` and the offset is undone afterwards?
- [ ] Index text ≤ 3 characters; longer meaning moved into words?
- [ ] Greek and symbols render with the fallback stack; checked in the PNG, not only the HTML?
- [ ] True minus `−` and fixed decimals on every printed number?
- [ ] One symbol system across the whole sheet?
- [ ] No `foreignObject`, no `baseline-shift`, no external math font?
