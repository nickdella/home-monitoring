import os
from unittest.mock import patch

import arrow

from home_monitoring.lambdas import egg_detector
from home_monitoring.store.egg_detector_cache import NestingBoxCacheRecord


class TestEggDetectorLambda:
    @patch("home_monitoring.lambdas.egg_detector.dynamodb")
    def test_render(self, dynamodb):
        now = arrow.now()
        dynamodb.Table.return_value.scan.return_value = {
            "Items": [
                {
                    "nesting_box": "box_1",
                    "egg_count_yolo": 3,
                    "egg_count_blob": 2,
                    "ts": now.int_timestamp,
                },
                {
                    "nesting_box": "box_2",
                    "egg_count_yolo": 4,
                    "egg_count_blob": 3,
                    "ts": now.int_timestamp,
                },
            ]
        }

        with patch.dict(os.environ, {"ENVIRONMENT": "dev"}, clear=True):
            result = egg_detector.lambda_handler({}, {})
            assert result["statusCode"] == 200
            body = result["body"]
            assert body.startswith("<html>")
            assert "Nesting Box #1" in body
            assert "Nesting Box #2" in body

    def test_image_urls(self):
        now = arrow.now()
        record = NestingBoxCacheRecord("box_1", 3, 2, now.int_timestamp)
        assert (
            record.blob_img_url("dev")
            == "https://nickdella-home-monitoring-dev.s3.us-west-2.amazonaws.com/egg-detector/images/box-1-blob.jpg"
        )
        assert (
            record.yolo_img_url("dev")
            == "https://nickdella-home-monitoring-dev.s3.us-west-2.amazonaws.com/egg-detector/images/box-1-yolo.jpg"
        )
