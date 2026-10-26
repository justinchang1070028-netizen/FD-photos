import io
from types import SimpleNamespace

import pytest
from PIL import Image

from fire_inspector.attachments import select_attachment, verify_image


def attachment(content_type="image/jpeg", size=1000, filename="a.jpg"):
    return SimpleNamespace(content_type=content_type, size=size, filename=filename)


def image_bytes(fmt):
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, fmt)
    return buffer.getvalue()


# --- select_attachment ---


def test_no_attachments_means_nothing_to_do():
    assert select_attachment([]) is None


@pytest.mark.parametrize("content_type", ["text/plain", "video/mp4", "application/pdf", None])
def test_non_image_attachments_are_ignored(content_type):
    assert select_attachment([attachment(content_type=content_type)]) is None


@pytest.mark.parametrize("content_type", ["image/jpeg", "image/png", "image/webp"])
def test_accepted_image_types(content_type):
    chosen, extra = select_attachment([attachment(content_type=content_type)])
    assert extra == 0


def test_gif_is_not_accepted():
    assert select_attachment([attachment(content_type="image/gif")]) is None


def test_only_the_first_image_is_chosen_and_the_rest_are_counted():
    first, second, third = attachment(filename="1.jpg"), attachment(filename="2.jpg"), attachment(filename="3.jpg")
    chosen, extra = select_attachment([first, second, third])
    assert chosen is first
    assert extra == 2


def test_a_video_before_the_photo_is_skipped():
    video, photo = attachment(content_type="video/mp4"), attachment()
    chosen, extra = select_attachment([video, photo])
    assert chosen is photo and extra == 0


def test_images_over_10mb_are_ignored():
    assert select_attachment([attachment(size=10 * 1024 * 1024 + 1)]) is None
    assert select_attachment([attachment(size=10 * 1024 * 1024)]) is not None


# --- verify_image ---


@pytest.mark.parametrize(
    ("fmt", "extension"), [("JPEG", ".jpg"), ("PNG", ".png"), ("WEBP", ".webp")]
)
def test_real_images_give_their_true_extension(fmt, extension):
    assert verify_image(image_bytes(fmt)) == extension


def test_a_text_file_renamed_to_jpg_is_rejected():
    with pytest.raises(ValueError):
        verify_image("這不是圖片".encode("utf-8"))


def test_a_gif_disguised_as_a_photo_is_rejected():
    with pytest.raises(ValueError):
        verify_image(image_bytes("GIF"))


def test_a_truncated_image_is_rejected():
    with pytest.raises(ValueError):
        verify_image(image_bytes("PNG")[:20])
