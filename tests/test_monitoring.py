from unittest.mock import MagicMock

import arrow

from home_monitoring.monitoring.alarm import AlarmRunner
from home_monitoring.monitoring.configs import MonitoringConfig
from home_monitoring.monitoring.timestream_query import TimestreamQueryRunner

TEST_CONFIG = MonitoringConfig(
    measure_name="temperature",
    device_name="Pool temp",
    threshold=7,
    comparison_operator="gt",
)


class TestMonitoring:
    def test_maybe_alarm_no_rows_returned(self):
        runner = self._get_alarm_runner()
        runner.query_runner.query_for_config.return_value = []

        runner.maybe_alarm(TEST_CONFIG)

        runner.sns_client.publish.assert_called_once()
        call_args = runner.sns_client.publish.call_args
        assert call_args.kwargs["TopicArn"] == "FAKE_TOPIC"
        assert "no query results" in call_args.kwargs["Subject"]
        assert "No query results" in call_args.kwargs["Message"]

    def test_maybe_alarm_fired(self):
        runner = self._get_alarm_runner()

        runner.query_runner.query_for_config.return_value = [
            {"value": 1.0},
            {"value": 2.0},
            {"value": 3.0},
        ]

        runner.maybe_alarm(TEST_CONFIG)
        runner.sns_client.publish.assert_not_called()

    def test_maybe_alarm_fired(self):
        runner = self._get_alarm_runner()

        runner.query_runner.query_for_config.return_value = [
            {"value": 1.0},
            {"value": 8.0},
            {"value": 3.0},
        ]

        runner.maybe_alarm(TEST_CONFIG)

        runner.sns_client.publish.assert_called_once()
        call_args = runner.sns_client.publish.call_args
        assert call_args.kwargs["TopicArn"] == "FAKE_TOPIC"
        assert "threshold exceeded" in call_args.kwargs["Subject"]
        assert "data points exceeded" in call_args.kwargs["Message"]

    def _get_alarm_runner(self):
        sns_client = MagicMock()
        query_runner = MagicMock()
        return AlarmRunner(
            sns_client=sns_client,
            sns_topic_arn="FAKE_TOPIC",
            query_runner=query_runner,
            env="dev",
        )

    def test_query_builder(self):
        timestream_client = MagicMock()
        timestream_client.query.return_value = self._get_query_response()

        runner = TimestreamQueryRunner(timestream_client)
        config = TEST_CONFIG
        parsed_rows = runner.query_for_config(config)
        print(parsed_rows)
        assert len(parsed_rows) == 2
        row = parsed_rows[0]
        assert type(row["name"]) == str
        assert type(row["ts"]) == arrow.Arrow
        assert type(row["value"]) == float

    def _get_query_response(self):
        return {
            "QueryId": "AEDACANPCYVR6TNN23FSLX53DL7A327F6IF7TYIW4T2SLWE6PU6OITCCA7JIM2I",
            "Rows": [
                {
                    "Data": [
                        {"ScalarValue": "well_water_tank"},
                        {"ScalarValue": "2023-09-19 00:00:00.000000000"},
                        {"ScalarValue": "1.0"},
                    ]
                },
                {
                    "Data": [
                        {"ScalarValue": "well_water_tank"},
                        {"ScalarValue": "2023-09-18 20:00:00.000000000"},
                        {"ScalarValue": "1.0"},
                    ]
                },
            ],
            "ColumnInfo": [
                {"Name": "name", "Type": {"ScalarType": "VARCHAR"}},
                {"Name": "ts", "Type": {"ScalarType": "TIMESTAMP"}},
                {"Name": "value", "Type": {"ScalarType": "DOUBLE"}},
            ],
            "QueryStatus": {
                "ProgressPercentage": 100.0,
                "CumulativeBytesScanned": 78,
                "CumulativeBytesMetered": 10000000,
            },
            "ResponseMetadata": {
                "RequestId": "NGZHVK253S32KTI2TQF7HJ5TU4",
                "HTTPStatusCode": 200,
                "RetryAttempts": 0,
            },
        }
