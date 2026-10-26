"""一次投稿的紀錄,對應 Excel 的一列。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Record:
    taken_at: datetime  # 台北時區的當地時間(不帶時區資訊)
    uploader: str
    user_id: int
    clothing: str
    shoes: str
    hair: str
    other: str  # 首飾/口罩/眼鏡 合併的一格
    overall: str  # 合格 / 不合格 / 無法判定 / 無效照片
    cumulative: int  # 寫入當下的累計合格次數(快照)
    photo_path: str  # 相對於 DATA_DIR
