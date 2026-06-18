"""Config flow for Gobel Battery Monitor integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_BMS_TYPE,
    CONF_CONNECTION_TYPE,
    CONF_BATTERY_PORT,
    CONF_IP_ADDRESS,
    CONF_IP_PORT,
    CONF_USB_PORT,
    CONF_BAUD_RATE,
    CONF_POLL_INTERVAL,
    CONF_JK_DISPLAY_INDEX_START,
    CONF_MAX_PARALLEL,
    BMS_TYPES,
    CONNECTION_TYPES,
    BATTERY_PORTS,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_MAX_PARALLEL,
    DEFAULT_BAUD_RATE,
    DEFAULT_IP_PORT,
    DEFAULT_JK_DISPLAY_INDEX_START,
)

_LOGGER = logging.getLogger(__name__)

class GobelBatteryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gobel Battery."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        errors = {}
        if user_input is not None:
            self.config_data = user_input
            if user_input[CONF_CONNECTION_TYPE] in ["ethernet", "wifi"]:
                return await self.async_step_network()
            else:
                return await self.async_step_serial()

        data_schema = vol.Schema(
            {
                vol.Required("device_name", default="Gobel Battery"): str,
                vol.Required(CONF_BMS_TYPE, default=BMS_TYPES[0]): vol.In(BMS_TYPES),
                vol.Required(CONF_CONNECTION_TYPE, default=CONNECTION_TYPES[0]): vol.In(CONNECTION_TYPES),
                vol.Required(CONF_BATTERY_PORT, default=BATTERY_PORTS[0]): vol.In(BATTERY_PORTS),
                vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Optional(CONF_MAX_PARALLEL, default=DEFAULT_MAX_PARALLEL): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Optional(CONF_JK_DISPLAY_INDEX_START, default=DEFAULT_JK_DISPLAY_INDEX_START): vol.In(["00", "01"]),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_network(self, user_input=None):
        """Handle network configuration parameters (IP and port)."""
        errors = {}
        if user_input is not None:
            user_data = {**self.config_data, **user_input}
            unique_id = f"{user_data[CONF_IP_ADDRESS]}_{user_data[CONF_IP_PORT]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(title=user_data["device_name"], data=user_data)

        network_schema = vol.Schema(
            {
                vol.Required(CONF_IP_ADDRESS): str,
                vol.Required(CONF_IP_PORT, default=DEFAULT_IP_PORT): int,
            }
        )

        return self.async_show_form(
            step_id="network", data_schema=network_schema, errors=errors
        )

    async def async_step_serial(self, user_input=None):
        """Handle serial configuration parameters (Port and Baud rate)."""
        errors = {}
        if user_input is not None:
            user_data = {**self.config_data, **user_input}
            unique_id = user_data[CONF_USB_PORT]
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(title=user_data["device_name"], data=user_data)

        serial_schema = vol.Schema(
            {
                vol.Required(CONF_USB_PORT, default="/dev/ttyUSB0"): str,
                vol.Required(CONF_BAUD_RATE, default=DEFAULT_BAUD_RATE): int,
            }
        )

        return self.async_show_form(
            step_id="serial", data_schema=serial_schema, errors=errors
        )
