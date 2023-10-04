from home_monitoring.lambdas import metrics_importer


# Simple driver class for the on-prem "ping" scraper
if __name__ == "__main__":
    event = {"scraper_class": "home_monitoring.scrapers.ping.PingScraper"}
    context = {}

    metrics_importer.lambda_handler(event, context)
