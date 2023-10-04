from unittest.mock import MagicMock, patch

import arrow

from home_monitoring.scrapers.yolink import YolinkScraper


class TestYolinkScraper:
    @patch("requests.post")
    def test_scrape_metrics(self, requests_post):
        ts = arrow.now().int_timestamp

        access_token_response = MagicMock()
        access_token_response.json.return_value = {
            "access_token": "FAKE_TOKEN",
        }
        get_devices_response = MagicMock()
        get_devices_response.json.return_value = {
            "code": "000000",
            "time": 1695185303367,
            "msgid": 1695185303367,
            "method": "Home.getDeviceList",
            "desc": "Success",
            "data": {
                "devices": [
                    {
                        "deviceId": "d88b4c0100063b11",
                        "deviceUDID": "f48c0771dd754d219ccd2a3831c97faa",
                        "name": "Chicken brooder",
                        "token": "74FA15215C75D1676568C4B3EE88F432",
                        "type": "THSensor",
                        "parentDeviceId": None,
                        "modelName": "YS8003-UC",
                    },
                    {
                        "deviceId": "d88b4c0100073c55",
                        "deviceUDID": "8bb1388e0121428b8cacfe2fa2b2bfd4",
                        "name": "Chicken water leak sensor",
                        "token": "DE3AC7DB6336178EC7C7C55E6C521189",
                        "type": "LeakSensor",
                        "parentDeviceId": None,
                        "modelName": "YS7904-UC",
                    },
                ]
            },
        }

        get_device_state_response1 = MagicMock()
        get_device_state_response1.json.return_value = {
            "code": "000000",
            "time": 1695185303477,
            "msgid": 1695185303477,
            "method": "THSensor.getState",
            "desc": "Success",
            "data": {
                "online": True,
                "state": {
                    "alarm": {
                        "lowBattery": False,
                        "lowTemp": False,
                        "highTemp": False,
                        "lowHumidity": False,
                        "highHumidity": False,
                        "period": False,
                        "code": 0,
                    },
                    "battery": 4,
                    "humidity": 65.5,
                    "humidityCorrection": 0,
                    "humidityLimit": {"max": 100, "min": 0},
                    "interval": 0,
                    "mode": "f",
                    "state": "normal",
                    "tempCorrection": 0,
                    "tempLimit": {"max": 75.8, "min": -14.2},
                    "temperature": 19.6,
                    "version": "0398",
                },
                "deviceId": "d88b4c0100063b11",
                "reportAt": "2023-09-20T04:30:58.724Z",
            },
        }

        get_device_state_response2 = MagicMock()
        get_device_state_response2.json.return_value = {
            "code": "000000",
            "time": 1695185303598,
            "msgid": 1695185303598,
            "method": "LeakSensor.getState",
            "desc": "Success",
            "data": {
                "online": False,
                "state": {
                    "battery": 1,
                    "beep": False,
                    "devTemperature": 15,
                    "interval": 30,
                    "sensorMode": "WaterPeak",
                    "state": "dry",
                    "stateChangedAt": 1682985390593,
                    "supportChangeMode": True,
                    "version": "0462",
                    "sensitivity": "low",
                },
                "deviceId": "d88b4c0200064deb",
                # this is too old and will be filtered out
                "reportAt": "2023-05-02T07:26:29.376Z",
            },
        }

        requests_post.side_effect = [
            access_token_response,
            get_devices_response,
            get_device_state_response1,
            get_device_state_response2,
        ]

        scraper = YolinkScraper(env="dev")
        metric_records = scraper.scrape_metrics()

        assert requests_post.call_count == 4
        call_args_list = requests_post.call_args_list

        expected_urls_and_methods = [
            ("https://api.yosmart.com/open/yolink/token", None),
            ("https://api.yosmart.com/open/yolink/v2/api", "Home.getDeviceList"),
            ("https://api.yosmart.com/open/yolink/v2/api", "THSensor.getState"),
            ("https://api.yosmart.com/open/yolink/v2/api", "LeakSensor.getState"),
        ]

        for idx, call in enumerate(call_args_list):
            assert call[0][0] == expected_urls_and_methods[idx][0]
            method = expected_urls_and_methods[idx][1]
            if method:
                assert call[1]["json"]["method"] == method

        assert len(metric_records) == 1
        assert metric_records[0].name == "temperature"
        assert metric_records[0].dimensions[0]["Name"] == "name"
        assert metric_records[0].dimensions[0]["Value"] == "Chicken brooder"
