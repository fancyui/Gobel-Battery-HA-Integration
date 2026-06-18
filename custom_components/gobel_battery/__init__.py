"""The Gobel Battery Monitor integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import GobelBatteryUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Gobel Battery Monitor component from YAML."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Gobel Battery Monitor from a config entry."""
    coordinator = GobelBatteryUpdateCoordinator(hass, entry)
    
    # Run the synchronous driver initialization
    if not await coordinator.async_setup():
        raise ConfigEntryNotReady(f"Failed to connect to BMS for {entry.title}")

    # Fetch initial data so entities have state on startup
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to the sensor and binary_sensor platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Release socket/serial/background threads
        await hass.async_add_executor_job(coordinator.shutdown)

    return unload_ok
