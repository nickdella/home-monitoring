import arrow
from home_monitoring.scrapers.flume import FlumeScraper
from unittest.mock import ANY
from unittest.mock import MagicMock

# Set to False for integration testing against the live API
USE_MOCK = True
SINCE_DATE = "2023-08-21 09:00:00"
UNTIL_DATE = "2023-08-21 10:00:00"


class TestFlumeScraper:
    def test_access_token(self):
        scraper = FlumeScraper()
        if USE_MOCK:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"data": [{"access_token": "FAKE_TOKEN"}]}
            self._mock_make_request(scraper, response)

        scraper.get_tokens()
        print(scraper.access_token)
        assert scraper.access_token is not None

    def test_scrape_metrics(self):
        scraper = FlumeScraper()
        if USE_MOCK:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {
                "data": [
                    {
                        "fake_request_id": [
                            {
                                "datetime": SINCE_DATE,
                                "value": 9.99,
                            }
                        ]
                    }
                ]
            }
            self._mock_make_request(scraper, response)

        records = scraper.scrape_metrics()
        assert records is not None
        assert len(records) == 1
        record = records[0]
        assert record.name == "household_water_usage"
        if USE_MOCK:
            assert record.time == arrow.get(SINCE_DATE, tzinfo="local").timestamp()
            assert record.value == 9.99

    def test_query_device(self):
        scraper = FlumeScraper()
        make_request_mock = None
        if USE_MOCK:
            make_request_mock = self._mock_make_request(scraper, {})

        since = arrow.get(SINCE_DATE).replace(minute=0, second=0, microsecond=0)
        until = since.shift(hours=1)

        scraper.query_device(since, until)
        expected_params = {
            "queries": [
                {
                    "request_id": ANY,
                    "bucket": "HR",
                    "since_datetime": SINCE_DATE,
                    "until_datetime": UNTIL_DATE,
                },
            ]
        }
        make_request_mock.assert_called_once_with(
            "/users/{user_id}/devices/{device_id}/query",
            method="POST",
            path_params={
                "user_id": 69740,
                "device_id": "6872060761719913970",
            },
            params=expected_params,
        )

    def _mock_make_request(self, scraper, response):
        mock = MagicMock()
        mock.return_value = response
        scraper._make_flume_request = mock
        return mock
