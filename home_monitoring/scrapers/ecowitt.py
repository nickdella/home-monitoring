from typing import List

import requests

from home_monitoring import logger, secrets
from home_monitoring.config import EcowittConfig
from home_monitoring.models.metrics import MetricRecord
from home_monitoring.scrapers.base_scraper import BaseScraper

logger = logger.get(__name__)


class EcowittScraper(BaseScraper):
    def scrape_metrics(self) -> List[MetricRecord]:
        response_json = self.scrape_ecowitt_metrics()
        if response_json["msg"] != "success":
            logger.error(f"Response: {response_json}")
            raise Exception("Error fetching metrics from Ecowitt")
        else:
            return self.process_json_response(response_json)

    def process_json_response(self, response_json: dict) -> List[MetricRecord]:
        try:
            data = response_json["data"]
            indoor_temp = self.build_record(
                "temperature", "indoors", data["indoor"]["temperature"]
            )

            soil_records = []
            for key in data.keys():
                if key in EcowittConfig.SOIL_SENSOR_NAMES:
                    soil_record = self.build_record(
                        "soil_moisture",
                        EcowittConfig.SOIL_SENSOR_NAMES[key],
                        data[key]["soilmoisture"],
                    )
                    soil_records.append(soil_record)

            return [indoor_temp] + soil_records
        except Exception as e:
            logger.error(f"Response: {response_json}")
            raise e

    def scrape_ecowitt_metrics(self) -> dict:
        response = self.make_ecowitt_request(
            "/device/real_time",
            params={
                "mac": EcowittConfig.ECOWITT_MAC_ADDRESS,
                "call_back": "all",
            },
        )
        return response.json()

    def make_ecowitt_request(self, endpoint: str, params: dict) -> requests.Response:
        url = f"{EcowittConfig.ECOWITT_BASE_URL}/{endpoint}"
        all_params = dict(params)
        all_params["application_key"] = secrets.ECOWITT_APP_KEY
        all_params["api_key"] = secrets.ECOWITT_API_KEY

        return requests.get(url, params=all_params)

    def build_record(self, metric_name: str, location: str, data: dict) -> MetricRecord:
        record = MetricRecord(metric_name, int(data["time"]), float(data["value"]))
        record.add_dimension("name", location)
        return record
