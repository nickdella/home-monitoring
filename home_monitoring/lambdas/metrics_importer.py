import boto3
import importlib
import os

from home_monitoring import logger
from home_monitoring.scrapers.base_scraper import BaseScraper
from home_monitoring.store.timestream import TimestreamMetricsStore


logger = logger.get(__name__)


def lambda_handler(event, context):
    env = os.environ["ENVIRONMENT"]

    timestream_client = boto3.client("timestream-write", region_name="us-west-2")
    # TODO Pull database name from context
    store = TimestreamMetricsStore(timestream_client, "home_monitoring")

    scraper_class_name = event["scraper_class"]
    module_name = ".".join(scraper_class_name.split(".")[:-1])
    class_name = scraper_class_name.split(".")[-1]
    module = importlib.import_module(module_name)
    class_ = getattr(module, class_name)
    scraper: BaseScraper = class_(env=env)

    logger.info(f"Running {class_name}")
    records = scraper.scrape_metrics()

    if records:
        store.write_metrics("metrics", records)
    else:
        logger.info(f"No records returned for {class_name}")
