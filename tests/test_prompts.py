from app.prompts import build_messages, extract_image_urls
from app.schemas import QuestionType, SearchRequest


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


def test_build_messages_keeps_plain_text_user_content_without_images() -> None:
    payload = SearchRequest(title="题目", options="A. 选项A\nB. 选项B", type=QuestionType.single)

    messages = build_messages(payload)

    assert isinstance(messages[1]["content"], str)
    assert "题目图片" not in messages[1]["content"]


def test_build_messages_attaches_image_url_blocks() -> None:
    payload = SearchRequest(
        title="题目 https://example.com/table.png求答案",
        options="A. 选项A\nB. https://example.com/choice.jpg",
        type=QuestionType.single,
    )

    messages = build_messages(payload)
    user_content = messages[1]["content"]

    assert isinstance(user_content, list)
    assert user_content[0]["type"] == "text"
    assert "已附加 2 张图片" in user_content[0]["text"]
    assert user_content[1:] == [
        {"type": "image_url", "image_url": {"url": "https://example.com/table.png"}},
        {"type": "image_url", "image_url": {"url": "https://example.com/choice.jpg"}},
    ]
