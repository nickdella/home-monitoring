from typing import Dict, List

from botocore.client import BaseClient

from home_monitoring import logger
from home_monitoring.monitoring.timestream_query import TimestreamQueryRunner
from home_monitoring.monitoring.configs import MonitoringConfig

logger = logger.get(__name__)


class AlarmRunner:
    def __init__(
        self,
        sns_client: BaseClient,
        sns_topic_arn: str,
        query_runner: TimestreamQueryRunner,
        env: str,
    ):
        self.query_runner: TimestreamQueryRunner = query_runner
        self.sns_client = sns_client
        self.sns_topic_arn = sns_topic_arn
        self.env = env

    def maybe_alarm(self, config: MonitoringConfig) -> None:
        """Interprets the MonitoringConfig to executes the monitoring query, perform
        the test and alarm if the threshold is breached"""
        logger.info(f"Executing maybe_alarm for config: {config}")
        rows = self.query_runner.query_for_config(config)

        # query should always return results
        if not rows:
            logger.warning("  Alarm: No rows returned from query")
            self._public_no_results_sns(config)
            return

        exceeding_rows = []

        for row in rows:
            val = row["value"]
            exceeds = False

            match config.comparison_operator:
                case "gt":
                    exceeds = val > config.threshold
                case "lt":
                    exceeds = val < config.threshold
                case _:
                    raise Exception(
                        f"Comparison operator '{config.comparison_operator}' "
                        f"not supported"
                    )

            logger.info(
                f"  Testing: {val} {config.comparison_operator} "
                f"{config.threshold} => {exceeds}"
            )
            if exceeds:
                exceeding_rows.append(row)
                if len(exceeding_rows) >= config.datapoints_to_alarm:
                    logger.info(
                        f"  Alarm: {len(exceeding_rows)} data points exceeded threshold"
                    )
                    self._publish_alarm_sns(config, exceeding_rows)
                    break

        if len(exceeding_rows) < config.datapoints_to_alarm:
            logger.info("  Did not alarm")

    def _public_no_results_sns(self, config: MonitoringConfig) -> None:
        subject = (
            f"Alarm triggered for {config.alarm_name} in {self.env}: "
            "no query results returned"
        )
        message = "No query results returned. Perhaps the metrics importer is failing?"

        self.sns_client.publish(
            TopicArn=self.sns_topic_arn, Subject=subject, Message=message
        )

    def _publish_alarm_sns(
        self, config: MonitoringConfig, exceeding_rows: List[Dict]
    ) -> None:
        exceeding_rows = exceeding_rows[:3]
        subject = (
            f"Alarm triggered for {config.alarm_name} in {self.env}: threshold exceeded"
        )
        message = (
            f"At least {config.datapoints_to_alarm} data points exceeded "
            f"the threshold '{config.comparison_operator} {config.threshold}' \n\n"
            f"Sample rows: {exceeding_rows}"
        )

        self.sns_client.publish(
            TopicArn=self.sns_topic_arn, Subject=subject, Message=message
        )


if __name__ == "__main__":
    import boto3
    from home_monitoring.monitoring.configs import CONFIGS

    sns_client = boto3.client("sns", region_name="us-west-2")
    timestream_client = boto3.client("timestream-query", region_name="us-west-2")
    runner = AlarmRunner(
        sns_client=sns_client,
        sns_topic_arn="arn:aws:sns:us-west-2:599598955234:alarms_topic",
        query_runner=TimestreamQueryRunner(timestream_client),
        env="dev",
    )

    # for conf in CONFIGS:
    #     runner.maybe_alarm(conf)
    runner.maybe_alarm(CONFIGS[8])
