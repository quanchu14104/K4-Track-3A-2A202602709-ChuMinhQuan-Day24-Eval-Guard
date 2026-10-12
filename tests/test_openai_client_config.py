from types import ModuleType
from unittest.mock import Mock

import pytest

from src import m5_enrichment
from src.experiment_support import create_openai_client


def test_openai_client_uses_configured_compatible_endpoint(monkeypatch):
    import config

    client = Mock()
    constructor = Mock(return_value=client)
    openai_module = ModuleType("openai")
    openai_module.OpenAI = constructor
    monkeypatch.setitem(__import__("sys").modules, "openai", openai_module)
    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(config, "OPENAI_ENDPOINT_URL", "https://api.example.test/v1")

    assert create_openai_client(timeout=4.0) is client
    constructor.assert_called_once_with(
        api_key="test-key",
        base_url="https://api.example.test/v1",
        timeout=4.0,
    )


def test_enrichment_raises_when_credential_validation_fails(monkeypatch):
    m5_enrichment._openai_auth_valid = None
    monkeypatch.setattr(m5_enrichment, "OPENAI_API_KEY", "test-key")
    client = Mock()
    client.models.list.side_effect = PermissionError("invalid credentials")
    monkeypatch.setattr(m5_enrichment, "create_openai_client", Mock(return_value=client))

    with pytest.raises(RuntimeError, match="credentials and endpoint") as error:
        m5_enrichment._is_openai_ready()

    assert isinstance(error.value.__cause__, PermissionError)
    assert m5_enrichment._openai_auth_valid is None
    m5_enrichment._openai_auth_valid = None
