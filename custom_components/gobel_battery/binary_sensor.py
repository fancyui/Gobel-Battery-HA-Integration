"""Binary sensor platform for the Gobel Battery Monitor integration."""
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Metadata defining the sub-dictionary, key, entity name suffix, and device class
BINARY_SENSORS_METADATA = {
    "protect_state_1": {
        "protect_short_circuit": ("Short Circuit Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_high_discharge_current": ("Discharge Overcurrent Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_high_charge_current": ("Charge Overcurrent Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_low_total_voltage": ("Total Under-Voltage Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_high_total_voltage": ("Total Over-Voltage Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_low_cell_voltage": ("Cell Under-Voltage Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_high_cell_voltage": ("Cell Over-Voltage Protection", BinarySensorDeviceClass.PROBLEM),
    },
    "protect_state_2": {
        "protect_low_charge_temp": ("Charge Low Temp Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_high_charge_temp": ("Charge High Temp Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_high_MOS_temp": ("MOS High Temp Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_high_discharge_temp": ("Discharge High Temp Protection", BinarySensorDeviceClass.PROBLEM),
        "status_fully_charged": ("Fully Charged Status", None),
        "protect_low_env_temp": ("Low Env Temp Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_high_env_temp": ("High Env Temp Protection", BinarySensorDeviceClass.PROBLEM),
        "protect_low_discharge_temp": ("Discharge Low Temp Protection", BinarySensorDeviceClass.PROBLEM),
    },
    "fault_state": {
        "fault_sampling": ("Sampling Fault", BinarySensorDeviceClass.PROBLEM),
        "fault_cell": ("Cell Count Mismatch/Fault", BinarySensorDeviceClass.PROBLEM),
        "fault_NTC": ("Temperature Sensor Fault", BinarySensorDeviceClass.PROBLEM),
        "fault_discharge_MOS": ("Discharge MOS Fault", BinarySensorDeviceClass.PROBLEM),
        "fault_charge_MOS": ("Charge MOS Fault", BinarySensorDeviceClass.PROBLEM),
    },
    "instruction_state": {
        "status_heating": ("Heating Switch Active", BinarySensorDeviceClass.HEAT),
        "status_charger_avaliable": ("Charger Available", BinarySensorDeviceClass.PLUG),
        "status_reverse_connected": ("Reverse Connected Alert", BinarySensorDeviceClass.PROBLEM),
        "status_discharge_enabled": ("Discharge Enabled Status", BinarySensorDeviceClass.POWER),
        "status_charge_enabled": ("Charge Enabled Status", BinarySensorDeviceClass.POWER),
        "status_current_limit_enabled": ("Current Limiter Active", BinarySensorDeviceClass.POWER),
    }
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the binary sensor platform from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Get latest data
    data = coordinator.data
    warning_packs = data.get("warning", []) if data else []
    
    # Default to creating entities for pack 1 if no data is present yet
    packs_to_create = len(warning_packs) if len(warning_packs) > 0 else 1

    for pack_idx in range(packs_to_create):
        for sub_dict, sensors in BINARY_SENSORS_METADATA.items():
            for key, (name, device_class) in sensors.items():
                entities.append(
                    GobelBatteryBinarySensor(
                        coordinator, pack_idx, sub_dict, key, name, device_class
                    )
                )

    async_add_entities(entities, update_before_add=True)

class GobelBatteryBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor representing a BMS alarm, warning or status state."""

    def __init__(self, coordinator, pack_index, sub_dict, key, name, device_class):
        """Initialize binary sensor."""
        super().__init__(coordinator)
        self.pack_index = pack_index
        self._sub_dict = sub_dict
        self._key = key
        display_pack = pack_index + (0 if coordinator.jk_display_index_start == "00" else 1)

        self._attr_name = f"{coordinator.device_name} Pack {display_pack:02d} {name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_pack_{pack_index}_{sub_dict}_{key}"
        self._attr_device_class = device_class

    @property
    def device_info(self):
        """Return device info for individual pack child device."""
        display_pack = self.pack_index + (0 if self.coordinator.jk_display_index_start == "00" else 1)
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.entry.entry_id}_pack_{self.pack_index}")},
            "name": f"{self.coordinator.device_name} Pack {display_pack:02d}",
            "via_device": (DOMAIN, f"{self.coordinator.entry.entry_id}_total"),
        }

    @property
    def is_on(self):
        """Return True if the binary sensor is active/triggered."""
        data = self.coordinator.data
        if not data:
            return None
        warning_packs = data.get("warning", [])
        if self.pack_index >= len(warning_packs):
            return None

        pack_warnings = warning_packs[self.pack_index]
        sub_data = pack_warnings.get(self._sub_dict, {})
        
        # Return boolean value of warning/protection key
        val = sub_data.get(self._key, False)
        return bool(val)
