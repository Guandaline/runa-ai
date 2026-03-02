# tests/unit/nala/athomic/config/test_config_loading.py

import pytest

from nala.athomic.config import AppSettings, get_settings


@pytest.mark.integration
def test_load_from_toml_with_nested_cache_config(tmp_path, monkeypatch):
    """
    Tests loading a TOML file with the new structure of
    named connections and nested Pydantic models.
    """
    settings_file = tmp_path / "settings.toml"
    settings_content = """
    [default]
    app_name = "TestApp Lazy"
    log_level = "DEBUG"

    [default.database.documents]
      default_connection_name = "test_db"
      [default.database.documents.connections.test_db]
        enabled = true
        backend = "mongo"
        [default.database.documents.connections.test_db.provider]
          backend = "mongo"
          url = "mongo://lazy:pass@host_lazy:5432/db_lazy" # pragma: allowlist secret
          pool_size = 8

    [default.database.kvstore]
      default_connection_name = "cache_db"
      [default.database.kvstore.connections.cache_db]
        enabled = true
        backend = "redis"
        [default.database.kvstore.connections.cache_db.provider]
          backend = "redis"
          uri = "redis://localhost_lazy_toml:6399/2"

    [default.performance.cache]
      enabled = true
      default_ttl_seconds = 1800
      kv_store_connection_name = "cache_db"
    """
    settings_file.write_text(settings_content, encoding="utf-8")

    get_settings.cache_clear()

    monkeypatch.setenv("NALA_SETTINGS_FILES", str(settings_file))
    monkeypatch.setenv("NALA_DOTENV_PATH", str(tmp_path / "non_existent.env"))
    monkeypatch.setenv("ENV_FOR_DYNACONF", "default")

    settings = get_settings()

    assert isinstance(settings, AppSettings)
    assert settings.app_name == "TestApp Lazy"

    assert settings.performance.cache.kv_store_connection_name == "cache_db"

    assert (
        settings.database.kvstore.connections[
            "cache_db"
        ].provider.uri.get_secret_value()
        == "redis://localhost_lazy_toml:6399/2"
    )
