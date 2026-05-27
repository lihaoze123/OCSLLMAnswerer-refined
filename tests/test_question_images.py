from app.question_images import extract_image_urls, find_image_matches, split_image_parts


def test_extract_image_urls_stops_before_adjacent_chinese_text() -> None:
    title = (
        "如下几个表所示"
        "https://p.ananas.chaoxing.com/star3/origin/fb6c52ba3edd701e5e832cbf0daf359d.png"
        "求既学过“1001”号课"
    )

    assert extract_image_urls(title) == [
        "https://p.ananas.chaoxing.com/star3/origin/fb6c52ba3edd701e5e832cbf0daf359d.png"
    ]


def test_extract_image_urls_deduplicates_and_ignores_non_image_urls() -> None:
    image_url = "https://example.com/question.PNG"

    assert extract_image_urls(
        f"题目图片 {image_url}。",
        f"A. 再次出现 {image_url}\nB. 文档 https://example.com/page",
    ) == [image_url]


def test_find_image_matches_returns_spans_and_normalized_urls() -> None:
    text = "前 https://example.com/a.png 后"

    matches = find_image_matches(text)

    assert len(matches) == 1
    assert matches[0].normalized_url == "https://example.com/a.png"
    assert text[matches[0].start : matches[0].end] == "https://example.com/a.png"


def test_split_image_parts_preserves_order() -> None:
    parts = split_image_parts("前 https://example.com/a.png 后")

    assert [part.kind for part in parts] == ["text", "image", "text"]
    assert parts[0].text == "前 "
    assert parts[1].url == "https://example.com/a.png"
    assert parts[2].text == " 后"
