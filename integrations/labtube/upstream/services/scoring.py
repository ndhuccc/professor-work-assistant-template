"""Pure scoring and review-selection helpers (no database access)."""
import math
import random

MAX_PER_QUESTION = 2
QUESTIONS = 3
MAX_TOTAL = MAX_PER_QUESTION * QUESTIONS     # 6


def quiz_rate(scores):
    """Sum of up to three 0–2 question scores divided by 6; missing questions count as 0."""
    return round(sum(scores) / MAX_TOTAL, 4)


def final_score(rubric, rate, coefficient=0.5):
    """final = rubric × ((1 − c) + c × rate).  With c = 0.5 this is the SOP's  rubric × (0.5 + 0.5 × rate)."""
    if rubric is None or rate is None:
        return None
    c = max(0.0, min(1.0, coefficient))
    return round(rubric * ((1 - c) + c * rate), 2)


def is_boundary(rate, low=0.4, high=0.6):
    return rate is not None and low <= rate <= high


def sample_ids(ids, session_id, fraction=0.10, minimum=1):
    """Reproducible random sample (seeded by the session id) of at least ``minimum`` ids."""
    ids = sorted(ids)
    if not ids:
        return set()
    k = max(minimum, math.ceil(len(ids) * fraction))
    return set(random.Random(session_id).sample(ids, min(k, len(ids))))


def classify_attempts(attempts, session_id):
    """Assign each attempt to its first applicable review bucket.

    attempts: list of dicts {id, rate, flagged, needs_review, boundary}. Buckets in priority order:
    flagged → needs_review → boundary → sample → ok. Returns {attempt_id: bucket}.
    """
    sampled = sample_ids([a['id'] for a in attempts], session_id)
    result = {}
    for a in attempts:
        if a['flagged']:
            result[a['id']] = 'flagged'
        elif a['needs_review']:
            result[a['id']] = 'needs_review'
        elif a['boundary']:
            result[a['id']] = 'boundary'
        elif a['id'] in sampled:
            result[a['id']] = 'sample'
        else:
            result[a['id']] = 'ok'
    return result


def group_average(pairs):
    """[(key, score)] -> {key: (count, average)}.

    Questions differ per student, so averaging by question *number* means nothing; group by question *type*
    (explain / change / reason) or by score value instead.
    """
    acc = {}
    for key, score in pairs:
        acc.setdefault(key, []).append(score)
    return {k: (len(v), sum(v) / len(v)) for k, v in acc.items()}


def score_counts(scores):
    """Counts of 0 / 1 / 2 among the given question scores."""
    return [sum(1 for s in scores if s == v) for v in range(MAX_PER_QUESTION + 1)]


def review_changes(pairs):
    """[(ai_score, final_score)] -> how often the reviewer disagreed with the AI (pairs without an AI score are skipped)."""
    pairs = [(a, f) for a, f in pairs if a is not None]
    n = len(pairs)
    up = sum(1 for a, f in pairs if f > a)
    down = sum(1 for a, f in pairs if f < a)
    return {'compared': n, 'changed': up + down, 'up': up, 'down': down,
            'change_rate': (up + down) / n if n else None,
            'mean_shift': (sum(f - a for a, f in pairs) / n if n else None)}


def time_usage(used_and_allowed):
    """[(used_seconds, allowed_seconds)] -> median/mean/max used and how many used (nearly) all of their time."""
    rows = [(u, a) for u, a in used_and_allowed if u is not None and a]
    if not rows:
        return {'n': 0, 'median': None, 'mean': None, 'max': None, 'full_n': 0}
    used = sorted(u for u, _ in rows)
    mid = len(used) // 2
    median = used[mid] if len(used) % 2 else (used[mid - 1] + used[mid]) / 2
    return {'n': len(rows), 'median': median, 'mean': sum(used) / len(used), 'max': used[-1],
            'full_n': sum(1 for u, a in rows if u >= 0.9 * a)}


def rate_distribution(rates, buckets=5):
    """Counts of rates in equal-width buckets over [0, 1]."""
    counts = [0] * buckets
    for r in rates:
        i = min(buckets - 1, int(r * buckets))
        counts[i] += 1
    return counts
