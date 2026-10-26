from datetime import date, datetime

from fire_inspector.counting import already_counted_on, count_passing_days
from fire_inspector.models import Record

SEMESTER_START = date(2026, 9, 1)


def record(taken_at, overall="合格", user_id=1, uploader="小明"):
    return Record(
        taken_at=taken_at,
        uploader=uploader,
        user_id=user_id,
        clothing="✅",
        shoes="✅",
        hair="✅",
        other="✅",
        overall=overall,
        cumulative=0,
        photo_path="photos/x.jpg",
    )


def test_counts_each_passing_day_once():
    records = [
        record(datetime(2026, 10, 1, 18, 0)),
        record(datetime(2026, 10, 2, 18, 0)),
        record(datetime(2026, 10, 5, 18, 0)),
    ]
    assert count_passing_days(records, 1, SEMESTER_START) == 3


def test_two_passes_on_the_same_day_count_once():
    records = [
        record(datetime(2026, 10, 1, 18, 0)),
        record(datetime(2026, 10, 1, 21, 30)),
    ]
    assert count_passing_days(records, 1, SEMESTER_START) == 1


def test_only_qualified_records_count():
    records = [
        record(datetime(2026, 10, 1, 18, 0), overall="不合格"),
        record(datetime(2026, 10, 2, 18, 0), overall="無效照片"),
        record(datetime(2026, 10, 3, 18, 0), overall="無法判定"),
        record(datetime(2026, 10, 4, 18, 0), overall="合格"),
    ]
    assert count_passing_days(records, 1, SEMESTER_START) == 1


def test_failing_then_passing_on_the_same_day_counts_once():
    records = [
        record(datetime(2026, 10, 1, 18, 0), overall="不合格"),
        record(datetime(2026, 10, 1, 18, 5), overall="合格"),
    ]
    assert count_passing_days(records, 1, SEMESTER_START) == 1


def test_each_user_is_counted_separately():
    records = [
        record(datetime(2026, 10, 1, 18, 0), user_id=1),
        record(datetime(2026, 10, 2, 18, 0), user_id=1),
        record(datetime(2026, 10, 1, 18, 0), user_id=2),
    ]
    assert count_passing_days(records, 1, SEMESTER_START) == 2
    assert count_passing_days(records, 2, SEMESTER_START) == 1
    assert count_passing_days(records, 3, SEMESTER_START) == 0


def test_changing_nickname_does_not_split_the_count():
    records = [
        record(datetime(2026, 10, 1, 18, 0), uploader="小明"),
        record(datetime(2026, 10, 2, 18, 0), uploader="小明🔥火舞"),
    ]
    assert count_passing_days(records, 1, SEMESTER_START) == 2


def test_records_before_semester_start_are_not_counted():
    records = [
        record(datetime(2026, 8, 31, 23, 59)),
        record(datetime(2026, 9, 1, 0, 0)),
    ]
    assert count_passing_days(records, 1, SEMESTER_START) == 1


def test_already_counted_on_is_true_after_a_pass_that_day():
    records = [record(datetime(2026, 10, 1, 18, 0))]
    assert already_counted_on(records, 1, date(2026, 10, 1)) is True


def test_already_counted_on_is_false_for_other_day_user_or_result():
    records = [
        record(datetime(2026, 10, 1, 18, 0), user_id=1),
        record(datetime(2026, 10, 2, 18, 0), user_id=1, overall="不合格"),
    ]
    assert already_counted_on(records, 1, date(2026, 10, 2)) is False
    assert already_counted_on(records, 1, date(2026, 10, 3)) is False
    assert already_counted_on(records, 2, date(2026, 10, 1)) is False
