"""이미지 올리기 (통합 명세 4.6, ERD REQ-004).

- jpg · png · gif · webp, 10MB 이하. 확장자가 아니라 파일 내용으로 판단해 이미지로 위장한 파일을 거절한다.
- 휴대폰 사진은 찍힌 방향대로 바로 세우고, 위치 정보 같은 메타데이터는 다시 저장하면서 지운다.
- GIF 는 움직임을 지키려고 원본을 그대로 저장한다.
- 목록용 작은 이미지(가로 480px, WebP)를 함께 만든다.
"""

import io
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image as PILImage
from PIL import ImageOps, UnidentifiedImageError

from .content import media_url

from apps.common.errors import APIError

from .models import Image

FORMATS = {"JPEG": ("image/jpeg", "jpg"), "PNG": ("image/png", "png"), "GIF": ("image/gif", "gif"), "WEBP": ("image/webp", "webp")}
THUMB_WIDTH = 480
# 4천만 화소(약 8000x5000)를 넘는 사진은 받지 않는다. 풀면 수백 MB 가 되어 서버 메모리가 모자란다
MAX_PIXELS = 40_000_000
PILImage.MAX_IMAGE_PIXELS = MAX_PIXELS


def _open(data):
    try:
        probe = PILImage.open(io.BytesIO(data))
        probe.verify()  # 깨졌거나 위장한 파일을 걸러 낸다
        img = PILImage.open(io.BytesIO(data))
    except (PILImage.DecompressionBombError, PILImage.DecompressionBombWarning):
        raise APIError(413, "FILE_TOO_LARGE", "사진이 너무 커요. 가로 · 세로를 줄여서 올려 주세요.")
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise APIError(415, "UNSUPPORTED_FILE", "jpg · png · gif · webp 이미지만 올릴 수 있어요.")
    if img.width * img.height > MAX_PIXELS:
        raise APIError(413, "FILE_TOO_LARGE", "사진이 너무 커요. 가로 · 세로를 줄여서 올려 주세요.")
    return img


def save_upload(uploaded_file, uploader):
    if uploaded_file is None:
        raise APIError(400, "VALIDATION_ERROR", "올릴 이미지를 골라 주세요.", fields={"file": "이미지를 골라 주세요."})
    if uploaded_file.size > settings.MAX_IMAGE_BYTES:
        raise APIError(413, "FILE_TOO_LARGE", "이미지는 10MB 이하만 올릴 수 있어요.")

    data = uploaded_file.read()
    img = _open(data)
    if img.format not in FORMATS:
        raise APIError(415, "UNSUPPORTED_FILE", "jpg · png · gif · webp 이미지만 올릴 수 있어요.")
    content_type, ext = FORMATS[img.format]
    name = uuid.uuid4().hex

    if img.format == "GIF":
        original_bytes = data
        width, height = img.size
    else:
        upright = ImageOps.exif_transpose(img)
        buffer = io.BytesIO()
        save_kwargs = {"quality": 90} if img.format in ("JPEG", "WEBP") else {}
        if img.format == "JPEG" and upright.mode not in ("RGB", "L"):
            upright = upright.convert("RGB")
        upright.save(buffer, format=img.format, **save_kwargs)
        original_bytes = buffer.getvalue()
        width, height = upright.size
        img = upright

    # WebP 는 RGB · RGBA 만 저장할 수 있다 (16비트 · 흑백 1비트 PNG 등은 바꿔서)
    has_alpha = img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)
    thumb = img.convert("RGBA" if has_alpha else "RGB")
    if thumb.width > THUMB_WIDTH:
        thumb.thumbnail((THUMB_WIDTH, THUMB_WIDTH * 20))
    thumb_buffer = io.BytesIO()
    thumb.save(thumb_buffer, format="WEBP", quality=82)

    image = Image(
        uploader=uploader,
        content_type=content_type,
        width=width,
        height=height,
        size_bytes=len(original_bytes),
    )
    image.file.save(f"{name}.{ext}", ContentFile(original_bytes), save=False)
    image.thumb_file.save(f"{name}.webp", ContentFile(thumb_buffer.getvalue()), save=False)
    image.save()
    return image


def image_payload(image, request):
    return {
        "id": image.pk,
        # 본문에 그대로 들어가므로 호스트 없이 /media/... 로 준다 (도메인 · https 가 바뀌어도 깨지지 않게)
        "url": media_url(image.file.name),
        "thumb_url": media_url(image.thumb_file.name),
        "width": image.width,
        "height": image.height,
    }


def get_own_image(image_id, user):
    """회원 자신이 올린 이미지만 쓸 수 있다. 없거나 남의 것이면 칸 오류."""
    image = Image.objects.filter(pk=image_id, uploader=user).first()
    if image is None:
        raise APIError(400, "VALIDATION_ERROR", "이미지를 찾을 수 없어요.", fields={"profile_image_id": "먼저 이미지를 올려 주세요."})
    return image
