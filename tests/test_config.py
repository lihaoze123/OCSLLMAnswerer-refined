from pydantic import SecretStr

from app.config import AIProvider, Settings


def test_settings_reads_new_ai_config_values() -> None:
    settings = Settings(
        ai_provider=AIProvider.openai_compatible,
        ai_api_key=SecretStr("test-key"),
        ai_base_url="https://example.invalid/v1",
        ai_text_model="gpt-4o-mini",
        ai_vision_model="gpt-4o",
    )

    assert settings.ai_api_key_value == "test-key"
    assert settings.ai_base_url == "https://example.invalid/v1"
    assert settings.ai_text_model == "gpt-4o-mini"
    assert settings.ai_vision_model == "gpt-4o"


def test_settings_normalizes_blank_optional_values_to_none() -> None:
    settings = Settings(ai_text_model="", ai_vision_model="", ai_base_url="")

    assert settings.ai_text_model is None
    assert settings.ai_vision_model is None
    assert settings.ai_base_url is None
