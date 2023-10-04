import os

import arrow
import boto3
from jinja2 import Environment, PackageLoader, select_autoescape

from home_monitoring import logger
from home_monitoring.store.egg_detector_cache import EggDetectorCacheReader

logger = logger.get(__name__)

jinja_env = Environment(
    loader=PackageLoader("home_monitoring"),
    autoescape=select_autoescape(),
)

dynamodb = boto3.resource("dynamodb", region_name="us-west-2")


def lambda_handler(event, context):
    env = os.environ["ENVIRONMENT"]

    cache_reader = EggDetectorCacheReader(dynamodb)
    records = cache_reader.read()

    total_eggs = sum(map(lambda r: r.egg_count_blob, records))
    nesting_boxes = []
    for record in records:
        d = record.__dict__
        d["blob_img_url"] = record.blob_img_url(env)
        d["yolo_img_url"] = record.yolo_img_url(env)
        nesting_boxes.append(d)

    last_updated = arrow.get(records[0].ts).to("US/Pacific")

    results_template = jinja_env.get_template("egg_detector.html")
    html = results_template.render(
        {
            "egg_count": total_eggs,
            "last_updated": last_updated,
            "nesting_boxes": nesting_boxes,
        }
    )
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html",
        },
        "body": html,
    }


if __name__ == "__main__":
    os.environ["ENVIRONMENT"] = "dev"
    print(lambda_handler(None, None))
