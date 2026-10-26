"""挑出要審查的圖片附件,並確認下載的檔案真的是圖片。"""

import io

from PIL import Image, UnidentifiedImageError

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 50_000_000

_EXTENSIONS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def select_attachment(attachments):
    """回傳 (第一張合格的圖片, 被忽略的其他圖片張數);沒有可處理的圖片就回傳 None。"""
    eligible = [
        a
        for a in attachments
        if (a.content_type or "").split(";")[0].strip().lower() in ALLOWED_CONTENT_TYPES
        and a.size <= MAX_IMAGE_BYTES
    ]
    if not eligible:
        return None
    return eligible[0], len(eligible) - 1


def verify_image(data: bytes) -> str:
    """確認檔案內容真的是 jpg / png / webp,回傳真正的副檔名。不是就丟出 ValueError。"""
    try:
        with Image.open(io.BytesIO(data)) as image:
            image_format = image.format
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("圖片尺寸過大")
            image.load()  # 完整解碼一次,截斷或損毀的檔案會在這裡失敗
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as error:
        raise ValueError(f"不是有效的圖片:{error}") from error
    if image_format not in _EXTENSIONS:
        raise ValueError(f"不接受的圖片格式:{image_format}")
    return _EXTENSIONS[image_format]
