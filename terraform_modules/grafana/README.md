# Grafana module

This module configures:

- a Grafana server running on EC2
  - The server is provisioned/scaled dynamically to save on costs
  - The grafana instance is auto-provisioned from source files: [etc/grafana.ini](../../etc/grafana.ini) and [dashboads/main_dashboard.json](../../dashboards/main_dashboard.json)
- Simple control plane Lambda functions to launch the instance and auto-destroy it after a timeout
- 