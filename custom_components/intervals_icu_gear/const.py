DOMAIN = "intervals_icu_gear"
CONF_API_KEY = "api_key"
CONF_ATHLETE_ID = "athlete_id"
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN

CONF_ATHLETE_ID = "athlete_id"

class IntervalsICUGearConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Intervals.icu Gear."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Intervals.icu Gear", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_ATHLETE_ID): str,
            }),
            errors=errors,
        )

