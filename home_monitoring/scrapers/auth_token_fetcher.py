import base64
from dataclasses import dataclass
import sys

import arrow
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import requests

from home_monitoring import logger, secrets
from home_monitoring.config import EnphaseConfig

logger = logger.get(__name__)


@dataclass
class AuthTokens:
    token_type: str
    access_token: str
    refresh_token: str
    expiration_ts: int

    def access_token_payload(self):
        return self.access_token.split(".")[1]


class AuthTokenFetcher:
    def __init__(self, env="prod"):
        self.env = env

    def homeowner_authorization(self):
        """Automates the homeowner authorization web flow that grants the app an
        auth token, which in turn is used to fetch the access token. This
        bootstrapping procedure should only need to be run one time, after which
        the refresh token can be used for perpetual re-auth.
        See https://developer-v4.enphase.com/docs/quickstart.html#step_6"""

        # requires session/cookies, CSRF and multiple requests. We're just going
        # to bootstrap and update the authorization code manually for now
        raise NotImplementedError("homeowner_authorization is not implemented yet")

    def get_access_token(self, app_name: str) -> str:
        """Loads the latest access token from the database

        :param app_name: the Enphase app name"""
        table = self._get_dynamo_table()
        result = table.query(KeyConditionExpression=Key("app_name").eq(app_name))
        items = result["Items"]
        if not items:
            raise Exception(f"No access token found for app={app_name}")
        else:
            return items[0]["access_token"]

    def refresh_tokens(
        self, app_name, grant_type="refresh_token", authorization_code=None
    ) -> AuthTokens:
        """Refreshes access/refresh tokens and stores them in the database.

        :param app_name: The Enphcase app name
        :param grant_type: the OAuth grant type
        :param authorization_code: The authorization code granted by the homeowner.
            Only required if refresh token has expired."""
        refresh_token = None
        if grant_type == "refresh_token":
            # get existing tokens
            table = self._get_dynamo_table()
            result = table.query(KeyConditionExpression=Key("app_name").eq(app_name))
            items = result["Items"]

            if not items:
                # use bootstrap refresh token
                refresh_token = (
                    secrets.ENPHASE_PROD_BOOTSTRAP_REFRESH_TOKEN
                    if self.env == "prod"
                    else secrets.ENPHASE_DEV_BOOTSTRAP_REFRESH_TOKEN
                )
            else:
                # The token expires every 24 hours, so we just always refresh
                item = items[0]
                refresh_token = item["refresh_token"]

        auth_tokens = self._enphase_token_refresh(
            grant_type, refresh_token, authorization_code
        )
        self._upsert_auth_tokens(app_name, auth_tokens)
        return auth_tokens

    def _get_dynamo_table(self):
        # hack to write to prod table from laptop (see __main__ function below)
        import platform

        if platform.system() == "Darwin" and self.env == "prod":
            session = boto3.Session(profile_name="home-monitoring-prod")
        else:
            session = boto3.Session()

        resource = session.resource("dynamodb", region_name="us-west-2")
        table_name = "home_monitoring_auth_tokens"

        return resource.Table(table_name)

    def _enphase_token_refresh(
        self, grant_type: str, refresh_token: str = None, authorization_code: str = None
    ) -> AuthTokens:
        params = {"grant_type": grant_type}
        if grant_type == "refresh_token":
            params["refresh_token"] = refresh_token
        else:
            params["redirect_uri"] = EnphaseConfig.ENPHASE_OAUTH_REDIRECT_URI
            params["code"] = authorization_code

        authz_payload = (
            f"{secrets.ENPHASE_PROD_CLIENT_ID}:{secrets.ENPHASE_PROD_CLIENT_SECRET}"
            if self.env == "prod"
            else f"{secrets.ENPHASE_DEV_CLIENT_ID}:{secrets.ENPHASE_DEV_CLIENT_SECRET}"
        )
        authz_encoded = base64.b64encode(authz_payload.encode("ascii")).decode()
        headers = {"Authorization": f"Basic {authz_encoded}"}

        now = arrow.now("US/Pacific")
        response = requests.post(
            f"{EnphaseConfig.ENPHASE_BASE_URL}/oauth/token",
            params=params,
            headers=headers,
            allow_redirects=True,
        )
        if response.status_code <= 299:
            body = response.json()
            expires_in_seconds = int(body["expires_in"])
            expiration_ts = now.shift(seconds=expires_in_seconds)

            return AuthTokens(
                token_type=body["token_type"],
                access_token=body["access_token"],
                refresh_token=body["refresh_token"],
                expiration_ts=expiration_ts.int_timestamp,
            )
        else:
            raise Exception(
                f"{response.status_code} error getting access token. "
                f"Response body is: {response.text}"
            )

    def _upsert_auth_tokens(self, app_name, auth_tokens):
        try:
            table = self._get_dynamo_table()
            response = table.update_item(
                Key={"app_name": "enphase"},
                UpdateExpression="SET access_token = :val1,"
                "refresh_token = :val2, "
                "expiration_ts = :val3,"
                "token_type = :val4",
                ExpressionAttributeValues={
                    ":val1": auth_tokens.access_token,
                    ":val2": auth_tokens.refresh_token,
                    ":val3": auth_tokens.expiration_ts,
                    ":val4": auth_tokens.token_type,
                },
                ReturnValues="UPDATED_NEW",
            )
        except ClientError as err:
            logger.error(
                f"Couldn't update auth tokens for {app_name}",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return response["Attributes"]

    def get_enphase_authorization_url(self):
        client_id = (
            secrets.ENPHASE_PROD_CLIENT_ID
            if self.env == "prod"
            else secrets.ENPHASE_DEV_CLIENT_ID
        )
        return f"{ENPHASE_BASE_URL}/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={ENPHASE_OAUTH_REDIRECT_URI}"  # noqa


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception("Must provide 'env' program argument (dev or prod)")

    env = sys.argv[1]
    if env not in set(["dev", "prod"]):
        raise Exception(f"Got '{env}' for env argument. Must be 'dev' or 'prod'")

    print(f"Running Enphase interactive authorization helper for {env} environment")
    print(
        "  NOTE: Before proceeding, please disable EventBridge triggers for the"
        " following lambda functions: "
        "home_monitoring_scraper_enphase, home_monitoring_auth"
    )

    fetcher = AuthTokenFetcher(env)

    authorization_url = fetcher.get_enphase_authorization_url()
    print(
        "\nPaste this URL into your browser and log in using Enphase "
        "homeowner credentials: ",
        authorization_url,
    )
    print("\nPaste the Authorization code from the final screen below and hit enter:")
    authz_code = sys.stdin.readline().strip()
    print("\nFetching and writing new oauth token...")
    auth_tokens = fetcher.refresh_tokens("enphase", "authorization_code", authz_code)
    access_token_prefix = auth_tokens.access_token_payload()[:8]
    print(f"Updated tokens. Access token={access_token_prefix}...")

    print("\nRun terraform plan/apply to re-enable the lambda functions")
