from dataclasses import dataclass
from typing import List

from botocore.exceptions import ClientError

from home_monitoring import logger
from home_monitoring import config

logger = logger.get(__name__)


@dataclass
class NestingBoxCacheRecord:
    nesting_box_id: str
    egg_count_blob: int
    egg_count_yolo: int
    ts: int

    def blob_img_url(self, env):
        return self._get_img_url(env, "blob")

    def yolo_img_url(self, env):
        return self._get_img_url(env, "yolo")

    def _get_img_url(self, env, img_type):
        bucket_name = config.get_bucket_name(env)
        s3_base_url = (
            f"https://{bucket_name}.s3.us-west-2.amazonaws.com/egg-detector/images"
        )
        id = self.nesting_box_id.replace("_", "-")
        return f"{s3_base_url}/{id}-{img_type}.jpg"


class EggDetectorCacheReader:
    def __init__(self, dynamodb):
        self.dynamodb = dynamodb

    def read(self) -> List[NestingBoxCacheRecord]:
        table_name = "egg_detector_cache"

        try:
            table = self.dynamodb.Table(table_name)
            result = table.scan()
            items = result["Items"]

            if not items:
                raise Exception(f"No egg detector cache records found")

            records = []
            for item in items:
                records.append(
                    NestingBoxCacheRecord(
                        item["nesting_box"],
                        int(item["egg_count_blob"]),
                        int(item["egg_count_yolo"]),
                        int(item["ts"]),
                    )
                )
        except ClientError as e:
            logger.error("Error reading egg detector cache", e)
            raise

        return sorted(records, key=lambda r: r.nesting_box_id)
