from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionType(StrEnum):
    single = "single"
    multiple = "multiple"
    judgement = "judgement"
    completion = "completion"
    unknown = "unknown"


TYPE_LABELS: dict[QuestionType, str] = {
    QuestionType.single: "单选题",
    QuestionType.multiple: "多选题",
    QuestionType.judgement: "判断题",
    QuestionType.completion: "填空题",
    QuestionType.unknown: "未知类型",
}

QUESTION_TYPE_ALIASES: dict[str, QuestionType] = {
    "single": QuestionType.single,
    "singlechoice": QuestionType.single,
    "single_choice": QuestionType.single,
    "单选": QuestionType.single,
    "单选题": QuestionType.single,
    "multiple": QuestionType.multiple,
    "multiplechoice": QuestionType.multiple,
    "multiple_choice": QuestionType.multiple,
    "多选": QuestionType.multiple,
    "多选题": QuestionType.multiple,
    "judgement": QuestionType.judgement,
    "judgment": QuestionType.judgement,
    "judge": QuestionType.judgement,
    "truefalse": QuestionType.judgement,
    "true_false": QuestionType.judgement,
    "判断": QuestionType.judgement,
    "判断题": QuestionType.judgement,
    "completion": QuestionType.completion,
    "completionquestion": QuestionType.completion,
    "completion_question": QuestionType.completion,
    "blank": QuestionType.completion,
    "fillblank": QuestionType.completion,
    "fill_blank": QuestionType.completion,
    "填空": QuestionType.completion,
    "填空题": QuestionType.completion,
    "unknown": QuestionType.unknown,
    "未知": QuestionType.unknown,
    "未知类型": QuestionType.unknown,
}


class SearchRequest(BaseModel):
    title: str = Field(min_length=1)
    options: str = ""
    type: QuestionType = QuestionType.unknown

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("题目为空")
        return value

    @field_validator("options", mode="before")
    @classmethod
    def normalize_options(cls, value: Any) -> str:
        if value is None:
            return ""
        text = str(value)
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, value: Any) -> QuestionType:
        if value is None:
            return QuestionType.unknown
        if isinstance(value, QuestionType):
            return value

        text = str(value).strip()
        if not text:
            return QuestionType.unknown
        return QUESTION_TYPE_ALIASES.get(
            text.lower(), QUESTION_TYPE_ALIASES.get(text, QuestionType.unknown)
        )

    @property
    def type_label(self) -> str:
        return TYPE_LABELS[self.type]


class HealthResponse(BaseModel):
    code: int = 1
    msg: str


class ErrorResponse(BaseModel):
    code: int = 0
    msg: str


class ModelAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answer: str = Field(min_length=1)
    analysis: str = Field(min_length=1)


class SearchResponse(BaseModel):
    code: int = 1
    question: str
    answer: str
    analysis: str
