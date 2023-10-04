import json
from typing import List
import uuid

import arrow
import requests

from home_monitoring import logger, secrets
from home_monitoring.config import FlumeConfig
from home_monitoring.models.metrics import MetricRecord
from home_monitoring.scrapers.base_scraper import BaseScraper
from home_monitoring.scrapers.utils import get_previous_hour_dt

logger = logger.get(__name__)


class FlumeScraper(BaseScraper):
    """Scrapes the Flume API for water usage over previous hour"""

    def scrape_metrics(self) -> List[MetricRecord]:
        logger.info("Starting Flume API scrape")
        since = get_previous_hour_dt()
        until = since.shift(hours=1)
        response_json = self.query_device(since, until, "HR").json()

        try:
            # response is a nested array of query results and time series data
            # for each result. We're only fetching a single data point from
            # the previous hour
            query_results = response_json["data"][0]
            if not query_results:
                raise Exception(
                    "No query results returned from Flume API."
                    "Response is: " + json.dumps(response_json)
                )

            data_point = list(query_results.values())[0][0]
            ts = int(arrow.get(data_point["datetime"], tzinfo="US/Pacific").timestamp())
            value = float(data_point["value"])

            record = MetricRecord(
                "household_water_usage",
                ts,
                value,
            )
            record.add_dimension("name", FlumeConfig.LOCATION_NAME)
            logger.info(f"Writing metric: {record}")

            return [record]
        except Exception as e:
            logger.error(f"Response: {response_json}")
            raise e

    def query_device(
        self, since: arrow.Arrow, until: arrow.Arrow, bucket: str = "HR"
    ) -> requests.Response:
        endpoint = "/users/{user_id}/devices/{device_id}/query"
        format_str = "YYYY-MM-DD HH:mm:ss"

        query_payload = {
            "queries": [
                {
                    "request_id": uuid.uuid4().hex,
                    "bucket": bucket,
                    "since_datetime": since.format(format_str),
                    "until_datetime": until.format(format_str),
                },
            ]
        }

        return self._make_flume_request(
            endpoint,
            method="POST",
            path_params={
                "user_id": FlumeConfig.FLUME_USER_ID,
                "device_id": FlumeConfig.FLUME_DEVICE_ID,
            },
            params=query_payload,
        )

    def get_tokens(self) -> str:
        response = self._make_flume_request(
            endpoint="/oauth/token",
            method="POST",
            params={
                "grant_type": "password",
                "client_id": secrets.FLUME_CLIENT_ID,
                "client_secret": secrets.FLUME_CLIENT_SECRET,
                "username": secrets.FLUME_USERNAME,
                "password": secrets.FLUME_PASSWORD,
            },
            authenticated=False,
        )
        if response.status_code == 200:
            body = response.json()
            self.access_token = body["data"][0]["access_token"]
        else:
            raise Exception(
                "Error getting access token. Response body is: " + response.text
            )

        return self.access_token

    def _make_flume_request(
        self,
        endpoint: str,
        method: str = "GET",
        path_params: dict = None,
        params: dict = None,
        authenticated: bool = True,
    ) -> requests.Response:
        if path_params is None:
            path_params = {}
        if params is None:
            params = {}

        path = endpoint.format_map(path_params)
        url = f"{FlumeConfig.FLUME_BASE_URL}{path}"
        headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        if authenticated:
            if self.access_token is None:
                self.access_token = self.get_tokens()

            headers["Authorization"] = f"Bearer {self.access_token}"

        response = None
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=params, headers=headers)
        else:
            raise Exception(f"Method {method} not supported")

        if response.status_code < 300:
            return response
        else:
            raise Exception(
                f"Received {response.status_code} response code, body={response.text}"
            )
