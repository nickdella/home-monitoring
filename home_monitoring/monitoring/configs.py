from dataclasses import dataclass


@dataclass
class MonitoringConfig:
    measure_name: str
    device_name: str
    threshold: float
    comparison_operator: str
    interval_min: int = 30
    ago_min: int = 180
    datapoints_to_alarm: int = 1
    aggregation_operator: str = "AVG"
    schedule: str = "hourly"

    @property
    def alarm_name(self):
        if self.device_name:
            return f"{self.measure_name}_{self.device_name}"
        else:
            return self.measure_name


CONFIGS = [
    # fridge/freezer temp checks are run hourly
    MonitoringConfig(
        measure_name="temperature",
        device_name="Fridge temp",
        # TODO Convert C to F
        threshold=7,
        comparison_operator="gt",
    ),
    MonitoringConfig(
        measure_name="temperature",
        device_name="Freezer temp",
        # TODO Convert C to F
        threshold=-12,
        comparison_operator="gt",
    ),
    # soil moisture checks are run daily at end of day
    MonitoringConfig(
        measure_name="soil_moisture",
        device_name="front_yard_tree",
        threshold=20,
        comparison_operator="lt",
        schedule="daily",
    ),
    MonitoringConfig(
        measure_name="soil_moisture",
        device_name="garden_tomato_soil",
        threshold=20,
        comparison_operator="lt",
        schedule="daily",
    ),
    MonitoringConfig(
        measure_name="soil_moisture",
        device_name="side_garden",
        threshold=20,
        comparison_operator="lt",
        schedule="daily",
    ),
    MonitoringConfig(
        measure_name="soil_moisture",
        device_name="vineyard",
        threshold=20,
        comparison_operator="lt",
        schedule="daily",
    ),
    # solar production check is run daily at end of day
    MonitoringConfig(
        measure_name="solar_energy_produced",
        device_name=None,
        threshold=5000,
        comparison_operator="lt",
        interval_min=60 * 24,
        ago_min=60 * 12,
        aggregation_operator="SUM",
        schedule="daily",
    ),
    # household water usage is run hourly
    MonitoringConfig(
        measure_name="household_water_usage",
        device_name="primary_residence",
        threshold=100,
        interval_min=60,
        ago_min=60 * 3,
        comparison_operator="gt",
        aggregation_operator="SUM",
    ),
    MonitoringConfig(
        measure_name="leak_sensor",
        device_name="well_water_tank",
        threshold=1,
        interval_min=60 * 4,
        ago_min=60 * 8,
        comparison_operator="lt",
    ),
]

HOURLY_CONFIGS = [config for config in CONFIGS if config.schedule == "hourly"]
DAILY_CONFIGS = [config for config in CONFIGS if config.schedule == "daily"]
