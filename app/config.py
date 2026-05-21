from enum import StrEnum
from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class JsonMode(StrEnum):
    auto = "auto"
    on = "on"
    off = "off"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    llm_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_API_KEY", "OPENAI_API_KEY"),
    )
    llm_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_BASE_URL", "OPENAI_BASE_URL"),
    )
    llm_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_MODEL", "OPENAI_MODEL"),
    )
    llm_timeout: float = Field(
        default=30.0,
        validation_alias=AliasChoices("LLM_TIMEOUT", "OPENAI_TIMEOUT"),
    )
    llm_temperature: float = Field(default=0.3, validation_alias="LLM_TEMPERATURE")
    llm_json_mode: JsonMode = Field(default=JsonMode.auto, validation_alias="LLM_JSON_MODE")

    host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("SERVER_HOST", "HOST"))
    port: int = Field(default=5000, validation_alias=AliasChoices("SERVER_PORT", "PORT"))

    @field_validator("llm_base_url", "llm_model", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def llm_api_key_value(self) -> str | None:
        if self.llm_api_key is None:
            return None
        return self.llm_api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()
