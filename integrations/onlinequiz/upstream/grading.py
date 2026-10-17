"""Score calculation.

- No selection: always 0.
- Single choice: full points if correct, otherwise 0.
- Multiple choice: ratio = max(0, (n - 2k) / n), k = |S △ C|.
"""


def symmetric_difference_size(selected: set[str], correct: set[str]) -> int:
    return len(selected ^ correct)


def grade_ratio(n: int, k: int) -> float:
    if n <= 0:
        return 0.0
    return max(0.0, (n - 2 * k) / n)


def grade_answer(
    *,
    n_options: int,
    correct_letters: set[str],
    selected_letters: set[str],
    points: float,
    is_multiple: bool | None = None,
) -> tuple[float, bool]:
    """
    Returns (score, is_full_score).

    ``is_multiple`` defaults to ``len(correct_letters) > 1`` when not given.
    """
    if not selected_letters:
        return 0.0, False
    if is_multiple is None:
        is_multiple = len(correct_letters) > 1
    if not is_multiple:
        is_full = selected_letters == correct_letters
        return (points if is_full else 0.0), is_full
    k = symmetric_difference_size(selected_letters, correct_letters)
    ratio = grade_ratio(n_options, k)
    score = ratio * points
    is_full = k == 0 and selected_letters == correct_letters
    return score, is_full
