import json
import time
import os

import boto3
from botocore.exceptions import ClientError
import requests
from requests.exceptions import RequestException

from home_monitoring import logger, secrets
from home_monitoring.scrapers import utils


logger = logger.get(__name__)

POLLING_INTERVAL_SECONDS = 5
# The Grafana instance usually initializes in under 2 minutes
POLLING_DURATION_SECONDS = 25

asg_client = boto3.client("autoscaling", region_name="us-west-2")
ec2_client = boto3.client("ec2", region_name="us-west-2")


def lambda_handler(event, context):
    params = event["queryStringParameters"]
    env = os.environ["ENVIRONMENT"]

    input_token = params.get("token")
    token = (
        secrets.GRAFANA_LAUNCHER_DEV_SECRET
        if env == "dev"
        else secrets.GRAFANA_LAUNCHER_PROD_SECRET
    )
    if input_token != token:
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Authentication error"}),
        }

    action = params.get("action")
    if action == "start" or action == "stop":
        print("Adjusting ASG size")
        return adjust_asg_size(1 if action == "start" else 0, event)
    elif action == "check":
        print("Running health check")
        return check(event)


def adjust_asg_size(desired_capacity, event):
    try:
        asg_name = os.environ["ASG_NAME"]
        logger.info(f"Setting {asg_name} desired capacity to {desired_capacity}")
        asg_client.set_desired_capacity(
            AutoScalingGroupName=asg_name, DesiredCapacity=desired_capacity
        )
        if desired_capacity == 1:
            return check(event)
        else:
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Instance stopped"}),
            }
    except ClientError as err:
        logger.error(
            f"Error starting Grafana instance in ASG '{asg_name}': ",
            err.response["Error"]["Code"],
            err.response["Error"]["Message"],
        )
        raise


def check(event):
    instance_available = False
    url = None

    asg_name = os.environ["ASG_NAME"]
    # wait for instance to be in service
    instance_public_ip = get_instance_public_ip(asg_name)

    if instance_public_ip:
        instance_available = True
        logger.info("Running health check on Grafana instance")
        is_healthy, url = get_grafana_url_if_healthy(instance_public_ip)
        if is_healthy:
            logger.info(f"Grafana instance is healthy. " f"Redirecting to {url}")
            response = {
                "statusCode": 302,
                "headers": {"Location": url},
                "body": json.dumps({}),
            }
            return response

    check_url = "/".join(
        [
            event["headers"]["Host"],
            event["requestContext"]["stage"],
            "grafana",
        ]
    )
    token = event["queryStringParameters"].get("token")
    check_url = f"https://{check_url}?action=check&token={token}"

    if instance_available:
        message = f"Grafana instance at {url} is not ready yet. Retrying..."
    else:
        message = "Grafana instance is not running yet. Retrying..."

    response = {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": f"""
<html>
  <head>
    <meta http-equiv="refresh" content="3;URL='{check_url}'">
  </head>
  <body>
    {message}
  </body>
</html>""",
    }
    return response


def get_instance_public_ip(asg_name):
    instance = utils.find_first_instance_in_asg(asg_name, asg_client, ec2_client)
    if instance:
        return instance["PublicIpAddress"]
    else:
        logger.info(f"No instances running in ASG '{asg_name}'. Retrying...")
        return None


def get_grafana_url_if_healthy(public_ip):
    url = f"https://{public_ip}:3000/login"
    logger.info(f"Checking Grafana health at {url}")
    try:
        response = requests.get(
            url,
            timeout=POLLING_INTERVAL_SECONDS,
            verify=False,
        )
        if response.status_code == 200:
            return True, url
    except RequestException as re:
        logger.info(f"{re.__class__.__name__} while polling Grafana URL, will retry")
        return False, url


if __name__ == "__main__":
    import sys

    # export ENVIRONMENT=dev
    # export ASG_NAME=grafana_asg
    action = sys.argv[1]
    token = input("Enter auth token for grafana launcher: ")
    res = lambda_handler(
        # mock out event
        {
            "queryStringParameters": {"action": action, "token": token},
            "headers": {
                "Host": "localhost",
            },
            "requestContext": {
                "stage": "default",
            },
        },
        None,
    )
    logger.info(res)
