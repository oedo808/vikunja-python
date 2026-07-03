"""Constants for the Vikunja Home Assistant integration."""
DOMAIN = "vikunja"
DEFAULT_URL = "https://vikunja.ok9.io"
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

# Saved filters available in the Vikunja UI
SAVED_FILTERS = {
    -2: "Due in 3 Days",
    -3: "Overdue",
    -4: "Due Today",
}

# Config flow keys
CONF_URL = "url"
CONF_API_TOKEN = "api_token"
CONF_FILTERS = "filters"
CONF_SCAN_INTERVAL = "scan_interval"
