from typing import List

import arrow
import requests

from home_monitoring import logger, secrets
from home_monitoring.config import YolinkConfig
from home_monitoring.models.metrics import MetricRecord
from home_monitoring.scrapers.base_scraper import BaseScraper

logger = logger.get(__name__)


class YolinkScraper(BaseScraper):
    def scrape_metrics(self) -> List[MetricRecord]:
        records = []

        minimum_ingest_ts = arrow.now().shift(days=-30).int_timestamp
        logger.info(f"minimum_ingest_ts: {minimum_ingest_ts}")

        # get devices + tokens
        response_json = self.make_yolink_request("Home.getDeviceList")
        try:
            for device in response_json["data"]["devices"]:
                device_id = device["deviceId"]
                logger.info(device)

                if device_id in YolinkConfig.DEVICE_MAPPING:
                    device_token = device["token"]
                    device_type = device["type"]
                    state_handler = YolinkConfig.DEVICE_MAPPING[device_id][
                        "state_handler"
                    ]

                    (ts, value) = self.get_device_state(
                        device_type, device_id, device_token, state_handler
                    )
                    metric_name = YolinkConfig.DEVICE_MAPPING[device_id]["type"]
                    logger.info(f"{metric_name}, {ts}, {value}")
                    if ts > minimum_ingest_ts:
                        record = MetricRecord(
                            metric_name,
                            ts,
                            value,
                        )
                        record.add_dimension(
                            "name", YolinkConfig.DEVICE_MAPPING[device_id]["name"]
                        )
                        records.append(record)
                    else:
                        logger.info(
                            f"Timestamp for {metric_name} too old, skipping: "
                            f"{arrow.get(ts)}"
                        )

            return records
        except Exception as e:
            logger.error(f"Response: {response_json}")
            raise e

    def get_device_state(self, device_type, device_id, device_token, state_handler):
        response = self.make_yolink_request(
            f"{device_type}.getState",
            params={
                "targetDevice": device_id,
                "token": device_token,
            },
        )

        date = arrow.get(response["data"]["reportAt"])
        ts = date.int_timestamp
        value = state_handler(response["data"]["state"])
        return ts, value

    def make_yolink_request(self, method, params={}):
        if self.access_token is None:
            self.access_token = self.get_token()

        url = f"{YolinkConfig.YOLINK_BASE_URL}/v2/api"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        post_body = {
            "method": method,
        }
        post_body.update(params)

        return requests.post(url, json=post_body, headers=headers).json()

    def get_token(self):
        response = requests.post(
            f"{YolinkConfig.YOLINK_BASE_URL}/token",
            data={
                "grant_type": "client_credentials",
                "client_id": secrets.YOLINK_UAID,
                "client_secret": secrets.YOLINK_SECRET_KEY,
            },
        )
        return response.json()["access_token"]


# Run this module to print out the full device list and IDs for inclusion in
# home_monitoring.config
if __name__ == "__main__":
    scraper = YolinkScraper(env="dev")
    response_json = scraper.make_yolink_request("Home.getDeviceList")

    import json
    print(json.dumps(response_json, indent=2))

    result = scraper.scrape_metrics()
