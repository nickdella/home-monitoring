from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from botocore.exceptions import ClientError

from egg_detector import logger
from egg_detector.egg_detector import NestingBoxState

logger = logger.get(__name__)


# TODO Properly share this code from the home-monitoring project
@dataclass
class MetricRecord:
    name: str
    time: int
    value: float
    dimensions: List[dict[str, str]] = field(default_factory=list)

    def add_dimension(self, name, value):
        self.dimensions.append({"Name": name, "Value": str(value)})
        return self


class CacheWriter:
    DYNAMO_CACHE_TABLE_NAME = "egg_detector_cache"

    def __init__(self, s3_client, bucket_name, dynamodb):
        self.s3_client = s3_client
        self.bucket_name = bucket_name
        self.dynamodb = dynamodb

    def write(self, state: NestingBoxState):
        try:
            table = self.dynamodb.Table(CacheWriter.DYNAMO_CACHE_TABLE_NAME)
            table.update_item(
                Key={"nesting_box": f"box_{state.box_num}"},
                UpdateExpression="SET egg_count_blob = :val1,"
                "egg_count_yolo = :val2, "
                "ts = :val3",
                ExpressionAttributeValues={
                    ":val1": state.egg_count_blob,
                    ":val2": state.egg_count_yolo,
                    ":val3": state.ts,
                },
                ReturnValues="UPDATED_NEW",
            )
        except ClientError as err:
            logger.error(
                f"Couldn't update {CacheWriter.DYNAMO_CACHE_TABLE_NAME}",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

        self._upload_file(
            f"egg-detector/images/box-{state.box_num}-blob.jpg",
            state.egg_count_blob_img_path,
        )
        self._upload_file(
            f"egg-detector/images/box-{state.box_num}-yolo.jpg",
            state.egg_count_yolo_img_path,
        )

    def _upload_file(self, key, file_path):
        self.s3_client.upload_file(
            file_path, self.bucket_name, key, ExtraArgs={"ACL": "public-read"}
        )


class TimestreamMetricsStore:
    def __init__(self, client, database_name):
        self.client = client
        self.database_name = database_name

    def write_metric(self, record: MetricRecord):
        return self.write_metrics([record])

    def write_metrics(self, table_name: str, records: List[MetricRecord]):
        try:
            timestream_records = list(map(self.to_timestream_record, records))
            logger.info(timestream_records)

            # implements "last writer wins" semantics
            # See https://docs.aws.amazon.com/timestream/latest/developerguide/code-samples.write.html#code-samples.write.upserts  # noqa
            common_attributes = {"Version": int(datetime.now().timestamp())}

            result = self.client.write_records(
                DatabaseName=self.database_name,
                TableName=table_name,
                Records=timestream_records,
                CommonAttributes=common_attributes,
            )
            logger.info(
                "WriteRecords Status: [%s]"
                % result["ResponseMetadata"]["HTTPStatusCode"]
            )
        except self.client.exceptions.RejectedRecordsException as err:
            self._print_rejected_records_exceptions(err)
        except Exception as err:
            # TODO Configure logger
            logger.info("Error writing metrics:", err)

    @staticmethod
    def _print_rejected_records_exceptions(err):
        logger.info("RejectedRecords: ", err)
        for rr in err.response["RejectedRecords"]:
            logger.info(f"Rejected Index {rr['RecordIndex']}: {rr['Reason']}")
            if "ExistingVersion" in rr:
                logger.info(
                    f"Rejected record existing version: {rr['ExistingVersion']}"
                )

    @staticmethod
    def to_timestream_record(record: MetricRecord):
        return {
            "Dimensions": record.dimensions,
            "MeasureName": record.name,
            "MeasureValue": str(record.value),
            "MeasureValueType": "DOUBLE",
            "Time": str(record.time),
            "TimeUnit": "SECONDS",
        }
