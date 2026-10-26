"""累計合格次數。每次從紀錄現算,不另外存計數器。"""

from collections.abc import Iterable
from datetime import date

from fire_inspector.models import Record


def _passing_days(records: Iterable[Record], user_id: int) -> set[date]:
    return {
        r.taken_at.date()
        for r in records
        if r.user_id == user_id and r.overall == "合格"
    }


def count_passing_days(
    records: Iterable[Record], user_id: int, semester_start: date
) -> int:
    """這位社員從學期開始日起,有幾個不同的日子至少合格過一次。"""
    return sum(1 for day in _passing_days(records, user_id) if day >= semester_start)


def already_counted_on(records: Iterable[Record], user_id: int, day: date) -> bool:
    """這位社員在 day 這天是否已經有合格紀錄(同一天只計一次)。"""
    return day in _passing_days(records, user_id)
