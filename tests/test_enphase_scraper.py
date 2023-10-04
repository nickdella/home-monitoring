from home_monitoring.scrapers.enphase import EnphaseScraper
from home_monitoring.scrapers.utils import get_previous_hour_dt
from home_monitoring import secrets
from unittest.mock import MagicMock
from unittest.mock import patch

SINCE_DATE = "2023-08-21 09:00:00"
UNTIL_DATE = "2023-08-21 10:00:00"


class TestEnphaseScraper:
    @patch("home_monitoring.scrapers.enphase.EnphaseScraper._get_access_token")
    @patch("requests.get")
    def test_get_microinverter_production(self, requests_get, get_access_token):
        get_access_token.return_value = "FAKE_TOKEN"

        scraper = EnphaseScraper(env="dev")
        now = get_previous_hour_dt().int_timestamp
        scraper.get_microinverter_production(now)
        requests_get.assert_called_once()
        requests_get.assert_called_with(
            "https://api.enphaseenergy.com/api/v4/systems/2215569/telemetry/production_micro",  # noqa
            params={
                "start_at": now,
                "granularity": "day",
                "key": secrets.ENPHASE_DEV_API_KEY,
            },
            headers={
                "Authorization": "Bearer FAKE_TOKEN",
            },
        )

    @patch(
        "home_monitoring.scrapers.enphase.EnphaseScraper.get_microinverter_production"
    )
    def test_scrape_metrics(self, get_microinverter_production):
        scraper = EnphaseScraper()
        response = MagicMock()
        response.json.return_value = {
            "system_id": 1,
            "granularity": "day",
            "total_devices": 9,
            "start_at": 1496526300,
            "end_at": 1496528300,
            "items": "intervals",
            "intervals": [
                {"end_at": 1384122700, "devices_reporting": 1, "powr": 30, "enwh": 40},
                {"end_at": 1384123600, "devices_reporting": 1, "powr": 20, "enwh": 40},
            ],
            "meta": {
                "status": "normal",
                "last_report_at": 1445619615,
                "last_energy_at": 1445619033,
                "operational_at": 1357023600,
            },
        }
        get_microinverter_production.return_value = response

        result = scraper.scrape_metrics()
        print(result)
        assert len(result) == 4
        record = result[0]
        assert record.name == "solar_avg_power_produced"
        assert record.value == 30
        record = result[1]
        assert record.name == "solar_energy_produced"
        assert record.value == 40
