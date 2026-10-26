"""記住最近處理過的訊息編號,用來擋掉重複送來的同一則訊息。"""

from collections import OrderedDict


class RecentIds:
    """有序集合:超過 max_size 時,只保留最近加入的 keep 筆,不會整個清空。"""

    def __init__(self, max_size: int = 5000, keep: int = 1000):
        self._ids: OrderedDict[int, None] = OrderedDict()
        self._max_size = max_size
        self._keep = keep

    def add(self, item: int) -> None:
        self._ids[item] = None
        if len(self._ids) > self._max_size:
            while len(self._ids) > self._keep:
                self._ids.popitem(last=False)  # 丟掉最舊的

    def __contains__(self, item: int) -> bool:
        return item in self._ids

    def __len__(self) -> int:
        return len(self._ids)
