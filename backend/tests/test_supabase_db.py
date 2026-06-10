from unittest.mock import MagicMock
from distill.supabase_db import SupabaseDb


def _chain_returning(rows):
    """Build a Supabase query-builder mock whose execute() returns rows."""
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.execute.return_value = MagicMock(data=rows)
    return chain


def test_get_settings_selects_timezone():
    chain = _chain_returning(
        [{"delivery_time": "07:00", "device_token": None, "timezone": "America/New_York"}]
    )
    client = MagicMock()
    client.table.return_value = chain

    settings = SupabaseDb(client).get_settings("user-1")

    chain.select.assert_called_once_with("delivery_time, device_token, timezone")
    assert settings["timezone"] == "America/New_York"
