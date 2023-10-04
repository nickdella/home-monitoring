from datetime import datetime
from typing import List

from botocore.client import BaseClient

from home_monitoring import logger
from home_monitoring.store.metrics_store import MetricsStore, MetricRecord


logger = logger.get(__name__)


class TimestreamMetricsStore(MetricsStore):
    def __init__(self, client: BaseClient, database_name: str):
        self.client = client
        self.database_name = database_name

    def write_metric(self, record: MetricRecord) -> None:
        self.write_metrics([record])

    def write_metrics(self, table_name: str, records: List[MetricRecord]) -> None:
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
            logger.error("Error writing metrics:", err)

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
    def to_timestream_record(record: MetricRecord) -> dict:
        return {
            "Dimensions": record.dimensions,
            "MeasureName": record.name,
            "MeasureValue": str(record.value),
            "MeasureValueType": "DOUBLE",
            "Time": str(record.time),
            "TimeUnit": "SECONDS",
        }
