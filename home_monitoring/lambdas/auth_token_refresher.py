import os
from home_monitoring.scrapers.auth_token_fetcher import AuthTokenFetcher
from home_monitoring import logger

logger = logger.get(__name__)


def lambda_handler(event, context):
    env = os.environ["ENVIRONMENT"]

    app_name = "enphase"
    logger.info(f"Running AuthTokenFetcher for app_name={app_name}")
    fetcher = AuthTokenFetcher(env=env)
    auth_tokens = fetcher.refresh_tokens(app_name)
    access_token_prefix = auth_tokens.access_token_payload()[:8]
    logger.info(f"Updated tokens. Access token={access_token_prefix}...")
