from fire_inspector.recent_ids import RecentIds


def test_remembers_ids_it_was_given():
    seen = RecentIds()
    assert 1 not in seen
    seen.add(1)
    assert 1 in seen


def test_adding_the_same_id_twice_does_not_grow_it():
    seen = RecentIds()
    seen.add(1)
    seen.add(1)
    assert len(seen) == 1


def test_nothing_is_forgotten_until_the_limit_is_exceeded():
    seen = RecentIds(max_size=5000, keep=1000)
    for message_id in range(5000):
        seen.add(message_id)
    assert len(seen) == 5000
    assert 0 in seen


def test_over_the_limit_it_keeps_only_the_most_recent_1000_in_order():
    seen = RecentIds(max_size=5000, keep=1000)
    for message_id in range(5001):
        seen.add(message_id)
    assert len(seen) == 1000
    assert 5000 in seen and 4001 in seen  # 最新的 1000 筆:4001 到 5000
    assert 4000 not in seen and 0 not in seen  # 較舊的被丟掉


def test_it_does_not_clear_everything_like_before():
    seen = RecentIds(max_size=5, keep=2)
    for message_id in range(6):
        seen.add(message_id)
    assert 5 in seen and 4 in seen  # 最近的還在,不會被整個清空
