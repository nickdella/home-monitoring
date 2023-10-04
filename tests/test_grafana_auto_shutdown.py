import os
from unittest.mock import patch

import arrow

from home_monitoring.lambdas import grafana_auto_shutdown


class TestGrafanaAutoShutdownLambda:
    @patch("home_monitoring.lambdas.grafana_auto_shutdown.asg_client")
    @patch("home_monitoring.lambdas.grafana_auto_shutdown.ec2_client")
    def test_instance_not_found(self, ec2_client, asg_client):
        asg_client.describe_auto_scaling_groups.return_value = {
            "AutoScalingGroups": [{"Instances": []}]
        }
        with patch.dict(os.environ, {"ASG_NAME": "grafana_asg"}, clear=True):
            res = grafana_auto_shutdown.lambda_handler({}, {})
            assert res is None
            ec2_client.describe_instances.assert_not_called()
            asg_client.set_desired_capacity.assert_not_called()

    @patch("home_monitoring.lambdas.grafana_auto_shutdown.asg_client")
    @patch("home_monitoring.lambdas.grafana_auto_shutdown.ec2_client")
    def test_not_expired(self, ec2_client, asg_client):
        now = arrow.now()
        launch_time = now.shift(minutes=-29).datetime
        asg_client.describe_auto_scaling_groups.return_value = {
            "AutoScalingGroups": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "LifecycleState": "InService",
                        }
                    ]
                }
            ]
        }
        ec2_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"LaunchTime": launch_time}]}]
        }

        with patch.dict(os.environ, {"ASG_NAME": "grafana_asg"}, clear=True):
            res = grafana_auto_shutdown.lambda_handler({}, {})
            assert res is None
            asg_client.set_desired_capacity.assert_not_called()

    @patch("home_monitoring.lambdas.grafana_auto_shutdown.asg_client")
    @patch("home_monitoring.lambdas.grafana_auto_shutdown.ec2_client")
    def test_expired(self, ec2_client, asg_client):
        now = arrow.now()
        launch_time = now.shift(minutes=-31).datetime
        asg_client.describe_auto_scaling_groups.return_value = {
            "AutoScalingGroups": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "LifecycleState": "InService",
                        }
                    ]
                }
            ]
        }
        ec2_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"LaunchTime": launch_time}]}]
        }

        asg_name = "grafana_asg"
        with patch.dict(os.environ, {"ASG_NAME": asg_name}, clear=True):
            res = grafana_auto_shutdown.lambda_handler({}, {})
            assert res is None
            asg_client.set_desired_capacity.assert_called_once_with(
                AutoScalingGroupName=asg_name, DesiredCapacity=0
            )
