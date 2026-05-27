import re
from dataclasses import dataclass
from typing import Literal

IMAGE_URL_PATTERN = re.compile(
    r"https?://[^\s<>'\"\)\]\}\u4e00-\u9fff]+?\."
    r"(?:png|jpe?g|webp|gif|bmp)"
    r"(?:[?#][^\s<>'\"\)\]\}\u4e00-\u9fff]*)?",
    re.IGNORECASE,
)
TRAILING_URL_PUNCTUATION = ".,;:!?)>]}，。；：！？）】》"


@dataclass(frozen=True)
class QuestionImageMatch:
    raw_url: str
    normalized_url: str
    start: int
    end: int
    trailing_text: str = ""


@dataclass(frozen=True)
class QuestionImagePart:
    kind: Literal["text", "image"]
    text: str = ""
    url: str = ""


def find_image_matches(text: str) -> list[QuestionImageMatch]:
    matches: list[QuestionImageMatch] = []

    for match in IMAGE_URL_PATTERN.finditer(text):
        raw_url = match.group(0)
        normalized_url = raw_url.rstrip(TRAILING_URL_PUNCTUATION)
        if not normalized_url:
            continue
        matches.append(
            QuestionImageMatch(
                raw_url=raw_url,
                normalized_url=normalized_url,
                start=match.start(),
                end=match.end(),
                trailing_text=raw_url[len(normalized_url) :]
                if raw_url.startswith(normalized_url)
                else "",
            )
        )

    return matches


def extract_image_urls(*texts: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for text in texts:
        for match in find_image_matches(text):
            if match.normalized_url in seen:
                continue
            seen.add(match.normalized_url)
            urls.append(match.normalized_url)

    return urls


def split_image_parts(text: str) -> list[QuestionImagePart]:
    parts: list[QuestionImagePart] = []
    last_index = 0

    for match in find_image_matches(text):
        if match.start > last_index:
            parts.append(QuestionImagePart(kind="text", text=text[last_index : match.start]))

        parts.append(QuestionImagePart(kind="image", url=match.normalized_url))
        if match.trailing_text:
            parts.append(QuestionImagePart(kind="text", text=match.trailing_text))
        last_index = match.end

    if last_index < len(text):
        parts.append(QuestionImagePart(kind="text", text=text[last_index:]))

    return parts or [QuestionImagePart(kind="text", text=text)]
