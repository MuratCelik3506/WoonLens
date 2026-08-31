from pytest import MonkeyPatch

from woonlens.bootstrap.settings import Settings, get_settings


def test_settings_have_safe_production_defaults(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("WOONLENS_ENVIRONMENT", raising=False)
    monkeypatch.delenv("WOONLENS_LOG_LEVEL", raising=False)
    settings = Settings()

    assert settings.environment == "production"
    assert settings.log_level == "INFO"
    assert settings.bag_max_related_buildings == 10
    assert settings.ep_online_api_key is None


def test_settings_use_woonlens_environment_prefix(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("WOONLENS_ENVIRONMENT", "test")

    assert Settings().environment == "test"


def test_ep_online_key_is_secret(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("WOONLENS_EP_ONLINE_API_KEY", "private-test-value")

    settings = Settings()

    assert settings.ep_online_api_key is not None
    assert settings.ep_online_api_key.get_secret_value() == "private-test-value"
    assert "private-test-value" not in repr(settings)


def test_process_settings_are_cached(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("WOONLENS_ENVIRONMENT", "test")
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
