from enum import StrEnum
from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AIProvider(StrEnum):
    openai_compatible = "openai-compatible"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    ai_provider: AIProvider = Field(
        default=AIProvider.openai_compatible,
        validation_alias="AI_PROVIDER",
    )
    ai_api_key: SecretStr | None = Field(default=None, validation_alias="AI_API_KEY")
    ai_base_url: str | None = Field(default=None, validation_alias="AI_BASE_URL")
    ai_text_model: str | None = Field(default=None, validation_alias="AI_TEXT_MODEL")
    ai_vision_model: str | None = Field(default=None, validation_alias="AI_VISION_MODEL")
    ai_timeout: float = Field(default=30.0, validation_alias="AI_TIMEOUT")
    ai_temperature: float = Field(default=0.3, validation_alias="AI_TEMPERATURE")
    chaoxing_cookie: SecretStr | None = Field(default=None, validation_alias="CHAOXING_COOKIE")

    host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("SERVER_HOST", "HOST"))
    port: int = Field(default=5000, validation_alias=AliasChoices("SERVER_PORT", "PORT"))

    @field_validator(
        "ai_base_url",
        "ai_text_model",
        "ai_vision_model",
        "chaoxing_cookie",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def ai_api_key_value(self) -> str | None:
        if self.ai_api_key is None:
            return None
        return self.ai_api_key.get_secret_value()

    @property
    def chaoxing_cookie_value(self) -> str | None:
        if self.chaoxing_cookie is None:
            return None
        return self.chaoxing_cookie.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()
