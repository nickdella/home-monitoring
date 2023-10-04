from typing import List

import requests

from home_monitoring import logger, secrets
from home_monitoring.config import EnphaseConfig
from home_monitoring.models.metrics import MetricRecord
from home_monitoring.scrapers.auth_token_fetcher import AuthTokenFetcher
from home_monitoring.scrapers.base_scraper import BaseScraper
from home_monitoring.scrapers.utils import get_previous_hour_dt

logger = logger.get(__name__)


class EnphaseScraper(BaseScraper):
    """Scrapes the Enphase API for solar energy production over previous hour"""

    def scrape_metrics(self) -> List[MetricRecord]:
        logger.info("Starting Enphase API scrape")
        # Enphase API only returns internals strictly greater than start_at
        start_at_ts = get_previous_hour_dt().shift(seconds=-1).int_timestamp

        response_json = self.get_microinverter_production(start_at_ts).json()

        records = []
        dimensions = [{"Name": "location", "Value": "primary_residence"}]
        try:
            intervals = response_json["intervals"]
            for interval in intervals:
                ts = interval["end_at"]
                records.append(
                    MetricRecord(
                        "solar_avg_power_produced",
                        ts,
                        # measured in watts
                        interval["powr"],
                        dimensions=dimensions,
                    )
                )
                records.append(
                    MetricRecord(
                        "solar_energy_produced",
                        ts,
                        # measured in watt-hours
                        interval["enwh"],
                        dimensions=dimensions,
                    )
                )

            return records
        except Exception as e:
            logger.error(f"Response: {response_json}")
            raise e

    def get_microinverter_production(self, start_at_ts: int) -> requests.Response:
        if not self.access_token:
            self.access_token = self._get_access_token()

        url = (
            f"{EnphaseConfig.ENPHASE_BASE_URL}/api/v4/systems/{EnphaseConfig.ENPHASE_SYSTEM_ID}"
            f"/telemetry/production_micro"
        )

        return requests.get(
            url,
            params={
                "start_at": start_at_ts,
                "granularity": "day",
                "key": secrets.ENPHASE_PROD_API_KEY
                if self.env == "prod"
                else secrets.ENPHASE_DEV_API_KEY,
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
            },
        )

    def _get_access_token(self) -> str:
        return AuthTokenFetcher(env=self.env).get_access_token("enphase")
