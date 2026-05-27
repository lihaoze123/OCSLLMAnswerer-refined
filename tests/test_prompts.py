from app.prompts import build_prompt
from app.schemas import QuestionType, SearchRequest


def test_build_prompt_omits_image_instruction_without_images() -> None:
    payload = SearchRequest(title="题目", options="A. 选项A\nB. 选项B", type=QuestionType.single)

    prompt = build_prompt(payload)

    assert "题目图片" not in prompt
    assert "题目: 题目" in prompt


def test_build_prompt_includes_image_instruction_with_image_count() -> None:
    payload = SearchRequest(
        title="题目 https://example.com/table.png求答案",
        options="A. 选项A\nB. https://example.com/choice.jpg",
        type=QuestionType.single,
    )

    prompt = build_prompt(payload, image_count=2)

    assert "已附加 2 张图片" in prompt
    assert "https://example.com/table.png求答案" in prompt
    assert "https://example.com/choice.jpg" in prompt
