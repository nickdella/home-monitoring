import subprocess
from typing import List

import arrow

from home_monitoring import logger
from home_monitoring.scrapers.base_scraper import BaseScraper
from home_monitoring.models.metrics import MetricRecord

logger = logger.get(__name__)


class PingScraper(BaseScraper):
    def scrape_metrics(self) -> List[MetricRecord]:
        records = []

        now = int(arrow.utcnow().timestamp())
        result = subprocess.run(["ping", "-c", "10", "8.8.8.8"], stdout=subprocess.PIPE)
        if result.returncode != 0:
            logger.error(f"ping command returned exit code {result.returncode}:")
            logger.error(result.stdout)
            return records

        output_lines = result.stdout.splitlines()
        rtt_stats_line = output_lines[-1].decode("utf-8")
        packet_stats_line = output_lines[-2].decode("utf-8")

        min, avg, max, mdev = rtt_stats_line.split("=")[1].strip().split("/")
        packet_loss_pct = int(packet_stats_line.split(",")[2].split("%")[0])
        data = {
            "ping_min": float(min),
            "ping_avg": float(avg),
            "ping_max": float(max),
            "ping_packet_loss_pct": float(packet_loss_pct),
        }

        for metric_name, value in data.items():
            record = MetricRecord(
                metric_name,
                now,
                value,
            )
            record.add_dimension("location", "primary_residence")
            records.append(record)

        return records


# PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
# 64 bytes from 8.8.8.8: icmp_seq=1 ttl=57 time=10.2 ms
# 64 bytes from 8.8.8.8: icmp_seq=2 ttl=57 time=11.9 ms
# ...
# 64 bytes from 8.8.8.8: icmp_seq=10 ttl=57 time=20.0 ms
#
# --- 8.8.8.8 ping statistics ---
# 10 packets transmitted, 10 received, 0% packet loss, time 9016ms
# rtt min/avg/max/mdev = 10.094/13.744/20.540/3.631 ms
