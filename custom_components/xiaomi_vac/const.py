"""Constants for the Xiaomi Vacuum integration."""
from __future__ import annotations

DOMAIN = "xiaomi_vac"

CONF_HOST = "host"
CONF_TOKEN = "token"
CONF_MODEL = "model"
CONF_MAC = "mac"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SERVER = "server"
CONF_USER_ID = "user_id"
CONF_DEVICE_ID = "device_id"
CONF_WIFI_SN = "wifi_sn"
CONF_SSECURITY = "ssecurity"
CONF_SERVICE_TOKEN = "service_token"
CONF_PASS_TOKEN = "pass_token"
CONF_OAUTH_ACCESS_TOKEN = "oauth_access_token"
CONF_OAUTH_REFRESH_TOKEN = "oauth_refresh_token"
CONF_OAUTH_EXPIRES_TS = "oauth_expires_ts"
CONF_OAUTH_REGION = "oauth_region"
CONF_OAUTH_DEVICE_ID = "oauth_device_id"
CONF_OAUTH_REDIRECT_URI = "oauth_redirect_uri"

DEFAULT_SCAN_INTERVAL = 10  # seconds, local MIoT polling
# Cloud map refresh. The interval is only re-tuned at the start of an update,
# so the idle value is also the worst-case lag before a just-started clean
# switches to the fast cadence: keep it short enough that the live map appears
# promptly (transient cloud errors are served from cache, so extra polls are
# cheap). See map_coordinator._tune_interval.
MAP_SCAN_INTERVAL = 10      # seconds, cloud map refresh while cleaning
MAP_IDLE_INTERVAL = 60      # seconds, cloud map refresh while docked/idle

# Servers accepted by the Xiaomi cloud.
SERVERS = ["cn", "de", "us", "ru", "tw", "sg", "in", "i2"]
