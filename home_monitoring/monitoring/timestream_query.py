from typing import Dict, List

import arrow
from botocore.client import BaseClient

from home_monitoring import logger
from home_monitoring.monitoring.configs import MonitoringConfig

logger = logger.get(__name__)


class TimestreamQueryRunner:
    def __init__(self, timestream_client: BaseClient):
        self.client = timestream_client

    def query_for_config(self, config: MonitoringConfig) -> List[Dict]:
        """Formulates and executes the monitoring query based on the
        input MonitoringConfig"""
        name_clause = (
            f"""name = '{config.device_name}' """
            if config.device_name
            else """ name is NULL """
        )
        sql = (
            f"""SELECT name, """
            f"""       bin(time, {config.interval_min}m) as ts, """
            f"""       {config.aggregation_operator}("measure_value::double") as value """  # noqa
            f""" FROM "home_monitoring"."metrics" """
            f""" WHERE time > ago({config.ago_min}m) """
            f"""   AND measure_name = '{config.measure_name}' """
            f"""   AND {name_clause} """
            f""" GROUP BY name, bin(time, {config.interval_min}m) """
            f""" ORDER BY name, bin(time, {config.interval_min}m) DESC """
        )
        logger.info(f"Query: {sql}")
        return self.query(sql)

    def query(self, sql: str) -> List[Dict]:
        """Executes Timestream SQL query and converts to a more Pythonic form
        :param sql The SQL query. Column names must be aliased, only limited
                   ScalarTypes supported
        :returns an array of row dicts"""

        try:
            response = self.client.query(QueryString=sql, MaxRows=100)
            column_info = response["ColumnInfo"]

            rows = response["Rows"]
            parsed_rows = []
            for row in [r["Data"] for r in rows]:
                parsed_row = {}
                for idx, col in enumerate(row):
                    col_info = column_info[idx]
                    if col.get("NullValue"):
                        col_value = None
                    else:
                        col_value = col["ScalarValue"]
                        match col_info["Type"]["ScalarType"]:
                            case "VARCHAR":
                                # already string type
                                pass
                            case "TIMESTAMP":
                                col_value = arrow.get(col_value)
                            case "DOUBLE":
                                col_value = float(col_value)
                            case _:
                                col_type = col_info["Type"]["ScalarType"]
                                raise Exception(f"Type {col_type} not supported")

                    parsed_row[col_info["Name"]] = col_value
                parsed_rows.append(parsed_row)

            return parsed_rows
        except Exception as e:
            logger.error(f"Failed to execute/parse query:\n {sql}")
            if rows:
                logger.error(f"Result: {rows}")
            raise e
