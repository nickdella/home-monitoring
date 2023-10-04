import asyncio
import os
import platform

import arrow
import boto3

from egg_detector import logger, utils
from egg_detector.image_capture import ImageCapture
from egg_detector.egg_detector import EggDetector
from egg_detector.store import (
    CacheWriter,
    MetricRecord,
    TimestreamMetricsStore,
)


logger = logger.get(__name__)


async def main():
    start_time = arrow.now().int_timestamp

    camera_ip = os.environ["CAMERA_IP"]
    lights_plug_ip = os.environ["LIGHTS_PLUG_IP"]
    lights_plug_port = int(os.environ["LIGHTS_PLUG_PORT"])
    environment = os.environ.get("ENVIRONMENT", "prod")

    image_capture = ImageCapture(camera_ip, lights_plug_ip, lights_plug_port)
    img = await image_capture.capture(use_flash=True)
    return

    # Photo size: 2560 x 1920
    # Nesting box 1: (100, 850), (600, 1350)
    # Nesting box 2: (800, 850), (1700, 1350)
    # Nesting box 3: (1750, 850), (2500, 1400)
    nesting_box_regions = [
        ((100, 850), (700, 1350)),
        ((800, 850), (1700, 1350)),
        # Ignore 3rd nesting box. The chickens never use it
        # ((1750, 850), (2500, 1400)),
    ]
    nesting_box_images = utils.splice(img, regions_of_interest=nesting_box_regions)

    egg_detector = EggDetector(output_dir="output")
    nesting_box_states = []
    for box_num, nesting_box_image in enumerate(nesting_box_images):
        logger.info(f"Analyzing nesting box #{box_num}")
        nesting_box_state = egg_detector.analyze_nesting_box(nesting_box_image, box_num)
        logger.info(nesting_box_state)
        nesting_box_states.append(nesting_box_state)

    timestream_client = boto3.client("timestream-write", region_name="us-west-2")
    s3_client = boto3.client("s3", region_name="us-west-2")
    dynamo_client = boto3.resource("dynamodb", region_name="us-west-2")

    store = TimestreamMetricsStore(timestream_client, "home_monitoring")
    bucket = f"nickdella-home-monitoring-{'dev' if environment == 'dev' else 'prod'}"
    cache = CacheWriter(s3_client, bucket, dynamo_client)

    records = []
    for state in nesting_box_states:
        records.append(
            MetricRecord(
                "chicken_count_yolo", start_time, state.chicken_count_yolo
            ).add_dimension("nesting_box", state.box_num)
        )

        # if chicken detected, then don't write out egg count metrics:
        #   the chicken is very likely obscuring some/all of the eggs
        if state.chicken_count_yolo == 0:
            cache.write(state)

            records += [
                MetricRecord(
                    "egg_count_blob", start_time, state.egg_count_blob
                ).add_dimension("nesting_box", state.box_num),
                MetricRecord(
                    "egg_count_yolo", start_time, state.egg_count_yolo
                ).add_dimension("nesting_box", state.box_num),
            ]

    store.write_metrics("metrics", records)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
