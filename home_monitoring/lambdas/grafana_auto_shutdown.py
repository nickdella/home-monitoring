import os

import arrow
import boto3

from home_monitoring import logger
from home_monitoring.scrapers import utils


logger = logger.get(__name__)

asg_client = boto3.client("autoscaling", region_name="us-west-2")
ec2_client = boto3.client("ec2", region_name="us-west-2")

INSTANCE_TTL_SECONDS = 30 * 60


def lambda_handler(event, context):
    asg_name = os.environ["ASG_NAME"]

    logger.info("Checking for long-running Grafana instances...")
    instance = utils.find_first_instance_in_asg(asg_name, asg_client, ec2_client)

    if instance:
        launch_time = arrow.get(instance["LaunchTime"])
        delta = arrow.now() - launch_time
        logger.info(f"Instance has been running for {delta.seconds} seconds")
        if delta.seconds > INSTANCE_TTL_SECONDS:
            logger.info(
                f"Instance has been running for {delta.seconds} > "
                f"{INSTANCE_TTL_SECONDS} seconds => terminating"
            )
            asg_client.set_desired_capacity(
                AutoScalingGroupName=asg_name, DesiredCapacity=0
            )
    else:
        logger.info("Grafana EC2 instance is not running")


if __name__ == "__main__":
    lambda_handler(None, None)
