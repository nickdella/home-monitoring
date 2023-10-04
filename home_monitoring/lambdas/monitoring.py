import boto3
import os
from home_monitoring import logger
from home_monitoring.monitoring.alarm import AlarmRunner
from home_monitoring.monitoring import configs
from home_monitoring.monitoring.timestream_query import TimestreamQueryRunner


logger = logger.get(__name__)


def lambda_handler(event, context):
    env = os.environ["ENVIRONMENT"]
    alarm_topic_arn = os.environ["ALARM_TOPIC_ARN"]
    schedule = event["schedule"]

    sns_client = boto3.client("sns", region_name="us-west-2")
    timestream_client = boto3.client("timestream-query", region_name="us-west-2")
    runner = AlarmRunner(
        sns_client=sns_client,
        sns_topic_arn=alarm_topic_arn,
        query_runner=TimestreamQueryRunner(timestream_client),
        env=env,
    )

    for conf in (
        configs.HOURLY_CONFIGS if schedule == "hourly" else configs.DAILY_CONFIGS
    ):
        runner.maybe_alarm(conf)
