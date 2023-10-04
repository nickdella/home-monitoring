from unittest.mock import ANY
from unittest.mock import patch

import arrow
import pytest

from home_monitoring.scrapers.ecowitt import EcowittScraper


class TestEcowittScraper:
    @patch("requests.get")
    def test_scrape_metrics(self, requests_get):
        ts = arrow.now().int_timestamp
        requests_get.return_value.json.return_value = {
            "msg": "success",
            "data": {
                "indoor": {"temperature": {"time": ts, "value": 72}},
                "soil_ch1": {"soilmoisture": {"time": ts, "value": 10}},
                "soil_ch2": {"soilmoisture": {"time": ts, "value": 15}},
            },
        }
        scraper = EcowittScraper(env="dev")
        metric_records = scraper.scrape_metrics()

        requests_get.assert_called_once()
        requests_get.assert_called_with(
            "https://api.ecowitt.net/api/v3//device/real_time",  # noqa
            params={
                "mac": "C4:5B:BE:6D:9E:80",
                "call_back": "all",
                "application_key": ANY,
                "api_key": ANY,
            },
        )

        assert len(metric_records) == 3
        assert metric_records[0].name == "temperature"
        assert metric_records[0].value == 72
        assert metric_records[0].time == ts
        assert metric_records[1].name == "soil_moisture"

    @patch("requests.get")
    def test_response_error(self, requests_get):
        requests_get.return_value.json.return_value = {"msg": "error", "data": {}}

        scraper = EcowittScraper(env="dev")
        with pytest.raises(Exception):
            scraper.scrape_metrics()
