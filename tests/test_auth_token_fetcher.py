from unittest.mock import patch

import arrow

from home_monitoring.scrapers.auth_token_fetcher import AuthTokenFetcher, AuthTokens
from home_monitoring import secrets


class TestAuthTokenFetcher:
    @patch(
        "home_monitoring.scrapers.auth_token_fetcher.AuthTokenFetcher._get_dynamo_table"
    )
    def test_get_access_token(self, get_dynamo_table):
        get_dynamo_table.return_value.query.return_value = {
            "Items": [{"access_token": "FAKE_TOKEN"}]
        }

        fetcher = AuthTokenFetcher(env="dev")
        token = fetcher.get_access_token("foo")

        get_dynamo_table.assert_called_once()
        assert token == "FAKE_TOKEN"

    @patch(
        "home_monitoring.scrapers.auth_token_fetcher.AuthTokenFetcher._get_dynamo_table"
    )
    @patch(
        "home_monitoring.scrapers.auth_token_fetcher.AuthTokenFetcher._enphase_token_refresh"
    )
    @patch(
        "home_monitoring.scrapers.auth_token_fetcher.AuthTokenFetcher._upsert_auth_tokens"
    )
    def test_refresh_tokens_bootstrap(
        self, upsert_auth_tokens, enphase_token_refresh, get_dynamo_table
    ):
        now = arrow.now()
        app_name = "foo"
        get_dynamo_table.return_value.query.return_value = {"Items": []}
        auth_tokens = AuthTokens(
            token_type="bearer",
            access_token="FAKE_ACCESS_TOKEN",
            refresh_token="FAKE_REFRESH_TOKEN",
            expiration_ts=now.int_timestamp,
        )
        enphase_token_refresh.return_value = auth_tokens

        fetcher = AuthTokenFetcher(env="dev")
        token = fetcher.refresh_tokens(app_name)

        enphase_token_refresh.assert_called_once_with(
            "refresh_token", secrets.ENPHASE_DEV_BOOTSTRAP_REFRESH_TOKEN, None
        )
        upsert_auth_tokens.assert_called_once_with(app_name, auth_tokens)
        assert token == auth_tokens

    @patch(
        "home_monitoring.scrapers.auth_token_fetcher.AuthTokenFetcher._get_dynamo_table"
    )
    @patch(
        "home_monitoring.scrapers.auth_token_fetcher.AuthTokenFetcher._enphase_token_refresh"
    )
    @patch(
        "home_monitoring.scrapers.auth_token_fetcher.AuthTokenFetcher._upsert_auth_tokens"
    )
    def test_refresh_tokens_refresh(
        self, upsert_auth_tokens, enphase_token_refresh, get_dynamo_table
    ):
        now = arrow.now()
        app_name = "foo"
        get_dynamo_table.return_value.query.return_value = {
            "Items": [
                {
                    "access_token": "FAKE_ACCESS_TOKEN",
                    "refresh_token": "FAKE_REFRESH_TOKEN",
                }
            ]
        }
        auth_tokens = AuthTokens(
            token_type="bearer",
            access_token="FAKE_NEW_ACCESS_TOKEN",
            refresh_token="FAKE_NEW_REFRESH_TOKEN",
            expiration_ts=now.int_timestamp,
        )
        enphase_token_refresh.return_value = auth_tokens

        fetcher = AuthTokenFetcher(env="dev")
        token = fetcher.refresh_tokens(app_name)

        enphase_token_refresh.assert_called_once_with(
            "refresh_token", "FAKE_REFRESH_TOKEN", None
        )
        upsert_auth_tokens.assert_called_once_with(app_name, auth_tokens)
        assert token == auth_tokens
