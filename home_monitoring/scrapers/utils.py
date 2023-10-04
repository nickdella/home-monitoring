import arrow
from botocore.client import BaseClient

from home_monitoring import logger


logger = logger.get(__name__)


def get_previous_hour_dt() -> arrow.Arrow:
    dt = arrow.now("US/Pacific")
    dt = dt.replace(minute=0, second=0, microsecond=0)
    return dt.shift(hours=-1)


def find_first_instance_in_asg(
    asg_name: str, asg_client: BaseClient, ec2_client: BaseClient
) -> dict:
    """Finds the first EC2 instance in the autoscaling group.

    :param asg_name: the autoscaling group
    :param asg_client: boto3 client
    :param ec2_client: boto3 client
    :returns: The EC2 instance object or None if the ASG does not exist or if
        ASG has no InService instances
    """
    groups = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
    if groups["AutoScalingGroups"]:
        asg = groups["AutoScalingGroups"][0]
        if len(asg["Instances"]) == 1:
            instance = asg["Instances"][0]
            if instance["LifecycleState"] == "InService":
                instance_id = instance["InstanceId"]
                logger.info(f"Found running instance {instance_id}")
                instance = ec2_client.describe_instances(InstanceIds=[instance_id])

                return instance["Reservations"][0]["Instances"][0]

    return None
