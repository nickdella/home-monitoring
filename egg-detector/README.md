## Egg Detector app

Run from an on-premise machine, this app connects to a camera on the local network, takes
a snapshot, runs image detection and writes results to various cloud datastores. The results are
rendered on the default Grafana dashboard, as well as the Latest Egg Detector Results page (see
endpoint in API Gateway console).

This application is isolated from the main `home-monitoring` app because it depends on reolinkapi,
opencv and ultralytics (yolo), which have heavyweight dependencies (both Python and machine
packages).

## Run locally on Mac

```
make test
make run-mac
```

## Deploy to on-prem server

To deploy to the on-prem server:

```
make deploy
```

Note that any changes to [cron schedules](../etc/crontab) need to be copied separately.
See [home-monitoring README](../README.md#on-premise-server-configuration-and-deployment) for
machine setup.

## Notes

As of Sept 2023, `reolinkapi-py` depends on an older version of `opencv-python` which is
incompatible with Apple Silicon. We also found a bug in the `get_snapshot` REST API code. The
project doesn't seem to be actively maintained, so in order to mitigate, we pull `reolinkapi-py`
source in our Docker build and patch both issues using [this patch file](reolinkapipy-fixes.patch).
