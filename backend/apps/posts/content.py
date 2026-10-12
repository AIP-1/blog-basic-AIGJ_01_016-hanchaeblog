"""기록 본문 정제 (API 명세서 4.3, 7.2 '본문 HTML 허용 태그').

에디터가 보낸 HTML 에서 허용한 태그 · 속성만 남긴다. 스크립트 · 이벤트 속성 · 위험한 주소는 모두 지운다.
사진은 우리 서버에 올린 것(/media/...)만 남긴다. 다른 사이트 사진을 걸면 방문자 정보가 새기 때문이다.
"""

import html
import re
from urllib.parse import urlparse

import nh3
from django.conf import settings

ALLOWED_TAGS = {
    "p", "br", "div", "span", "h2", "h3",
    "strong", "b", "em", "i", "u", "s",
    "ul", "ol", "li", "blockquote", "pre", "code", "hr",
    "a", "img",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href"},
    "img": {"src", "alt"},
    "p": {"style"}, "span": {"style"}, "div": {"style"}, "h2": {"style"}, "h3": {"style"}, "li": {"style"},
}
# 글자색 · 정렬만 남긴다
ALLOWED_STYLES = {"color", "background-color", "text-align"}
EXCERPT_LENGTH = 150


def _media_path(url):
    """우리 서버에 올린 파일이면 MEDIA_URL 뒤의 경로(images/2026/10/a.png), 아니면 None."""
    path = urlparse(url).path
    prefix = "/" + settings.MEDIA_URL.lstrip("/")
    return path[len(prefix):] if path.startswith(prefix) else None


def _filter_attribute(tag, attr, value):
    if tag == "img" and attr == "src" and _media_path(value) is None:
        return None
    return value


def sanitize(content):
    cleaned = nh3.clean(
        content or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        attribute_filter=_filter_attribute,
        filter_style_properties=ALLOWED_STYLES,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer nofollow",
    )
    # src 를 잃은 사진은 빈 껍데기라 지운다
    return re.sub(r"<img(?![^>]*\ssrc=)[^>]*>", "", cleaned)


def to_text(content):
    """서식을 뺀 글자 (검색 · 요약용)."""
    text = re.sub(r"<(br|/p|/h2|/h3|/li|/blockquote|/pre|/div)\b[^>]*>", " ", content, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def excerpt(text):
    return text[:EXCERPT_LENGTH]


def image_paths(content):
    """본문에 들어 있는 우리 서버 사진의 경로들 (나온 순서대로)."""
    paths = []
    for src in re.findall(r"<img[^>]*\ssrc=\"([^\"]+)\"", content):
        path = _media_path(html.unescape(src))
        if path and path not in paths:
            paths.append(path)
    return paths
