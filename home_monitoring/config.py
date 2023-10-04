def get_bucket_name(env: str) -> str:
    return f"nickdella-home-monitoring-{env}"


class EcowittConfig:
    ECOWITT_BASE_URL = "https://api.ecowitt.net/api/v3"
    ECOWITT_MAC_ADDRESS = "C4:5B:BE:6D:9E:80"

    SOIL_SENSOR_NAMES = {
        "soil_ch1": "lower_bank",
        "soil_ch2": "vineyard",
        "soil_ch3": "patio_fern",
        "soil_ch4": "side_garden",
        "soil_ch5": "front_yard_tree",
        "soil_ch6": "garden_tomato_soil",
        # "soil_ch7": "bamboo_forest_soil",
    }


class EnphaseConfig:
    ENPHASE_BASE_URL = "https://api.enphaseenergy.com"
    ENPHASE_OAUTH_REDIRECT_URI = "https://api.enphaseenergy.com/oauth/redirect_uri"
    ENPHASE_SYSTEM_ID = 2215569


class FlumeConfig:
    FLUME_BASE_URL = "https://api.flumewater.com"
    # For efficiency, we've prefetched our user_id (via access token) and
    # device_id (via Fetch User's Devices API). If we ever get a new
    # device, we'll need to re-fetch
    FLUME_USER_ID = 69740
    FLUME_DEVICE_ID = "6872060761719913970"
    LOCATION_NAME = "primary_residence"


class YolinkConfig:
    YOLINK_BASE_URL = "https://api.yosmart.com/open/yolink"

    DEVICE_MAPPING = {
        "d88b4c0100070866": {
            "name": "Pool temp",
            "type": "temperature",
            "state_handler": lambda state: float(state["temperature"]),
        },
        "d88b4c0100046963": {
            "name": "well_water_tank",
            "type": "leak_sensor",
            "state_handler": lambda state: int("full" == state["state"]),
        },
        "d88b4c0100073c55": {
            "name": "chicken_water_sensor",
            "type": "leak_sensor",
            "state_handler": lambda state: int("full" == state["state"]),
        },
        "d88b4c01000631cf": {
            "name": "Freezer temp",
            "type": "temperature",
            "state_handler": lambda state: float(state["temperature"]),
        },
        "d88b4c0100063535": {
            "name": "Fridge temp",
            "type": "temperature",
            "state_handler": lambda state: float(state["temperature"]),
        },
        "d88b4c0100076f54": {
            "name": "Office temp",
            "type": "temperature",
            "state_handler": lambda state: float(state["temperature"]),
        },
        "d88b4c0100063b11": {
            "name": "Chicken brooder",
            "type": "temperature",
            "state_handler": lambda state: float(state["temperature"]),
        },
    }
