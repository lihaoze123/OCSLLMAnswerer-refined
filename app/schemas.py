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
