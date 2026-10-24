"""calibration.py: expected minutes and tokens per storypoint from done-task history."""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS / "lib"))
import calibration  # noqa: E402


def row(points, minutes, tokens, **extra):
    return {"points": points, "actual_minutes": minutes, "actual_tokens": tokens, **extra}


def test_refit_and_mdape():
    # _solve: an exact 2x2 system is solved, a singular one returns None.
    assert calibration._solve([[2.0, 1.0], [1.0, 3.0]], [5.0, 10.0]) == pytest.approx([1.0, 3.0])
    assert calibration._solve([[1.0, 2.0], [2.0, 4.0]], [3.0, 6.0]) is None

    # refit recovers an exact line over points for either target.
    rows = [row(p, 4 + 10 * p, 1000 + 500000 * p) for p in (1, 2, 3, 5, 8)]
    assert calibration.refit(rows, "actual_minutes") == pytest.approx((4.0, 10.0))
    assert calibration.refit(rows, "actual_tokens") == pytest.approx((1000.0, 500000.0))

    # One distinct points value (or no rows) is a singular system.
    assert calibration.refit([row(3, 30, 2000000)] * 4, "actual_minutes") is None
    assert calibration.refit([], "actual_minutes") is None

    # MdAPE of known (predicted, actual) pairs: errors 0.5, 0.0, 0.25 -> median 0.25.
    assert calibration.mdape([(15, 10), (20, 20), (30, 40)]) == pytest.approx(0.25)
    # Zero actuals are skipped, and nothing usable gives None.
    assert calibration.mdape([(15, 10), (5, 0), (20, 20)]) == pytest.approx(0.25)
    assert calibration.mdape([(5, 0)]) is None
    assert calibration.mdape([]) is None


def test_expected_uses_bucket_median():
    rows = [row(3, 30, 2000000), row(3, 50, 1000000), row(3, 40, 3000000), row(5, 90, 9000000)]
    assert calibration.expected(3, rows) == (40, 2000000)
    # An even bucket takes the mean of the middle two, as ints.
    rows.append(row(3, 60, 4000000))
    assert calibration.expected(3, rows) == (45, 2500000)
    m, t = calibration.expected(3, rows)
    assert isinstance(m, int) and isinstance(t, int)


def test_expected_falls_back_to_refit():
    # Line minutes = 2 + 10.4 * points, tokens = 100 + 700000.4 * points; bucket 13 is empty.
    rows = [row(p, 2 + 10.4 * p, 100 + 700000.4 * p) for p in (1, 2, 3, 5, 8)]
    rows = [row(r["points"], round(r["actual_minutes"]), round(r["actual_tokens"])) for r in rows]
    a_m, b_m = calibration.refit(rows, "actual_minutes")
    a_t, b_t = calibration.refit(rows, "actual_tokens")
    assert calibration.expected(13, rows) == (round(a_m + b_m * 13), round(a_t + b_t * 13))
    # Two rows in the bucket is still below MIN_BUCKET, so the refit line applies.
    assert calibration.MIN_BUCKET == 3 and calibration.MIN_REFIT == 5
    rows += [row(13, 500, 1)]
    assert calibration.expected(13, rows)[0] == round(
        sum(calibration.refit(rows, "actual_minutes")[i] * (1, 13)[i] for i in range(2))
    )

    # The refit value is clamped to at least 1.
    falling = [row(p, max(1, 200 - 30 * p), max(1, 2000 - 300 * p)) for p in (1, 2, 3, 5, 8)]
    assert calibration.expected(13, falling) == (1, 1)


def test_expected_falls_back_to_seed():
    assert calibration.POINTS == (1, 2, 3, 5, 8, 13)
    assert calibration.SEED == {
        1: (11, 750000),
        2: (23, 1500000),
        3: (34, 2250000),
        5: (57, 3750000),
        8: (91, 6000000),
        13: (147, 9750000),
    }
    assert calibration.expected(5, []) == (57, 3750000)
    four = [row(1, 10, 1), row(2, 20, 2), row(3, 30, 3), row(8, 80, 8)]
    for p in calibration.POINTS:
        assert calibration.expected(p, four) == calibration.SEED[p]
    # Five usable rows on one points value make a singular refit: other buckets take the seed.
    same = [row(3, 30, 3)] * 5
    assert calibration.expected(3, same) == (30, 3)
    assert calibration.expected(8, same) == calibration.SEED[8]
    with pytest.raises(ValueError):
        calibration.expected(4, [])


def test_bucket_table_sources():
    rows = [row(1, 10, 100000)] * 3 + [row(2, 21, 210000), row(5, 52, 520000)]
    junk = [
        {"points": 3, "actual_minutes": 30},  # missing tokens
        {"actual_minutes": 30, "actual_tokens": 3},  # missing points
        row(3, "30", 300000),  # non-integer minutes
        row(3, 30.0, 300000),  # float minutes
        row(3, 30, None),
        row("3", 30, 300000),
        row(3, True, 300000),
        row(4, 40, 400000),  # points not on the scale
        row(3, -5, 300000),  # negative actual
    ]
    table = calibration.bucket_table(rows + junk)
    assert sorted(table) == list(calibration.POINTS)
    for p in calibration.POINTS:
        assert set(table[p]) == {"minutes", "tokens", "n", "source"}
    assert table[1] == {"minutes": 10, "tokens": 100000, "n": 3, "source": "history"}
    a_m, b_m = calibration.refit(rows, "actual_minutes")
    a_t, b_t = calibration.refit(rows, "actual_tokens")
    for p in (2, 3, 5, 8, 13):
        assert table[p]["source"] == "refit"
        assert table[p]["minutes"] == max(1, round(a_m + b_m * p))
        assert table[p]["tokens"] == max(1, round(a_t + b_t * p))
    assert [table[p]["n"] for p in calibration.POINTS] == [3, 1, 0, 1, 0, 0]

    # Below MIN_REFIT usable rows (junk does not count) every bucket is seed or history.
    seeded = calibration.bucket_table(rows[:4] + junk)
    assert seeded[1] == {"minutes": 10, "tokens": 100000, "n": 3, "source": "history"}
    assert seeded[2] == {"minutes": 23, "tokens": 1500000, "n": 1, "source": "seed"}
    assert seeded[13] == {"minutes": 147, "tokens": 9750000, "n": 0, "source": "seed"}

    # Optional fields are carried without affecting the table.
    extra = [row(1, 10, 100000, expected_minutes=11, expected_tokens=750000, points_actual=2)]
    assert calibration.bucket_table(extra * 3)[1]["source"] == "history"
