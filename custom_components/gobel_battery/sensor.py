"""Sensor platform for the Gobel Battery Monitor integration."""
import logging
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Predefined metadata for overall and pack sensors
SENSOR_METADATA = {
    "voltage": {
        "name": "Voltage",
        "unit": "V",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave"
    },
    "current": {
        "name": "Current",
        "unit": "A",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc"
    },
    "power": {
        "name": "Power",
        "unit": "kW",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging"
    },
    "soc": {
        "name": "SOC",
        "unit": "%",
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-70"
    },
    "soh": {
        "name": "SOH",
        "unit": "%",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-plus-variant"
    },
    "remain_capacity": {
        "name": "Remaining Capacity",
        "unit": "Ah",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-clock"
    },
    "full_capacity": {
        "name": "Full Capacity",
        "unit": "Ah",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high"
    },
    "cycle_number": {
        "name": "Cycle Count",
        "unit": "cycles",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-sync"
    },
    "balance_current": {
        "name": "Balance Current",
        "unit": "A",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:scale-balance"
    },
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the sensor platform from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    initial_entities = []

    # 1. Register Overall Battery Bank Sensors
    overall_sensors = [
        # key, name, unit, device_class, state_class, icon
        ("packs_count", "Packs Count", "packs", None, SensorStateClass.MEASUREMENT, "mdi:database"),
        ("total_full_capacity", "Total Full Capacity", "Ah", None, SensorStateClass.MEASUREMENT, "mdi:battery-high"),
        ("total_remain_capacity", "Total Remaining Capacity", "Ah", None, SensorStateClass.MEASUREMENT, "mdi:battery-clock"),
        ("total_current", "Total Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "mdi:current-dc"),
        ("total_soc", "Total SOC", "%", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, "mdi:battery-70"),
        ("total_voltage", "Total Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:sine-wave"),
        ("total_power", "Total Power", "kW", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:battery-charging"),
        ("total_cell_voltage_max", "Max Cell Voltage", "mV", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:align-vertical-top"),
        ("total_cell_voltage_min", "Min Cell Voltage", "mV", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:align-vertical-bottom"),
        ("total_cell_voltage_diff", "Cell Voltage Delta", "mV", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:format-align-middle"),
    ]

    for key, name, unit, dev_class, state_class, icon in overall_sensors:
        initial_entities.append(GobelBatteryOverallSensor(coordinator, key, name, unit, dev_class, state_class, icon))

    # Track registered pack IDs
    registered_packs = set()

    @callback
    def async_add_pack_sensors():
        """Add sensors for newly discovered packs."""
        data = coordinator.data
        analog_packs = data.get("analog", []) if data else []
        
        # Default to pack 0 if no packs are detected yet so entities are visible
        if not analog_packs and not registered_packs:
            pack_ids_to_add = [0]
        else:
            pack_ids_to_add = [p.get("pack_id", 0) for p in analog_packs if p.get("pack_id", 0) not in registered_packs]

        new_entities = []
        for pack_id in pack_ids_to_add:
            if pack_id in registered_packs:
                continue
                
            num_cells = 16
            num_temps = 4
            
            # Count cells and temps from matching pack data if available
            pack_data = next((p for p in analog_packs if p.get("pack_id") == pack_id), None)
            if pack_data:
                num_cells = len(pack_data.get("cell_voltages", []))
                num_temps = len(pack_data.get("temperatures", []))

            # Add predefined metrics (SOC, SOH, Voltage, Current, Cycle Count, etc.)
            for metric, meta in SENSOR_METADATA.items():
                new_entities.append(
                    GobelBatteryPackSensor(
                        coordinator,
                        pack_id,
                        metric,
                        meta["name"],
                        meta["unit"],
                        meta["device_class"],
                        meta["state_class"],
                        meta["icon"],
                    )
                )

            # Add cell voltage sensors (Cell 01 Voltage ... Cell N Voltage)
            for cell_idx in range(1, num_cells + 1):
                new_entities.append(
                    GobelBatteryCellVoltageSensor(coordinator, pack_id, cell_idx)
                )

            # Add temperature sensors (Temperature 01 ... Temperature N)
            for temp_idx in range(1, num_temps + 1):
                new_entities.append(
                    GobelBatteryTemperatureSensor(coordinator, pack_id, temp_idx)
                )
                
            registered_packs.add(pack_id)

        if new_entities:
            async_add_entities(new_entities, update_before_add=True)

    # Register initial overall sensors + any initially detected packs
    async_add_entities(initial_entities, update_before_add=True)
    async_add_pack_sensors()

    # Listen for future updates
    entry.async_on_unload(
        coordinator.async_add_listener(async_add_pack_sensors)
    )

class GobelBatteryOverallSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing aggregate battery bank metrics."""

    def __init__(self, coordinator, key, name, unit, device_class, state_class, icon):
        """Initialize overall sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"{coordinator.device_name} {name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_total_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon

    @property
    def device_info(self):
        """Return device info for overall bank device."""
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.entry.entry_id}_total")},
            "name": f"{self.coordinator.device_name} (Total)",
            "manufacturer": "Gobel Power",
            "model": f"{self.coordinator.bms_type} Bank",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        data = self.coordinator.data
        if not data:
            return False
        return len(data.get("analog", [])) > 0

    @property
    def native_value(self):
        """Calculate and return the native value of the aggregate sensor."""
        data = self.coordinator.data
        if not data:
            return None
        analog_packs = data.get("analog", [])
        if not analog_packs:
            return None

        total_packs_num = len(analog_packs)

        if self._key == "packs_count":
            return total_packs_num
        elif self._key == "total_full_capacity":
            return round(sum(d.get("view_full_capacity", 0) for d in analog_packs), 2)
        elif self._key == "total_remain_capacity":
            return round(sum(d.get("view_remain_capacity", 0) for d in analog_packs), 2)
        elif self._key == "total_current":
            return round(sum(d.get("view_current", 0) for d in analog_packs), 2)
        elif self._key == "total_soc":
            total_full = sum(d.get("view_full_capacity", 0) for d in analog_packs)
            total_remain = sum(d.get("view_remain_capacity", 0) for d in analog_packs)
            return round(total_remain / total_full * 100, 1) if total_full > 0 else 0
        elif self._key == "total_voltage":
            return round(sum(d.get("view_voltage", 0) for d in analog_packs) / total_packs_num, 2)
        elif self._key == "total_power":
            return round(sum(d.get("view_power", 0) for d in analog_packs), 2)
        
        # Cell Voltages aggregate
        all_cell_voltages = [v for d in analog_packs for v in d.get("cell_voltages", [])]
        if not all_cell_voltages:
            return None

        if self._key == "total_cell_voltage_max":
            return max(all_cell_voltages)
        elif self._key == "total_cell_voltage_min":
            return min(all_cell_voltages)
        elif self._key == "total_cell_voltage_diff":
            return max(all_cell_voltages) - min(all_cell_voltages)

        return None

class GobelBatteryPackSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing a specific battery pack metric."""

    def __init__(self, coordinator, pack_id, metric, name, unit, device_class, state_class, icon):
        """Initialize pack sensor."""
        super().__init__(coordinator)
        self.pack_id = pack_id
        self._metric = metric
        display_pack = pack_id + (0 if coordinator.jk_display_index_start == "00" else 1)
        
        self._attr_name = f"{coordinator.device_name} Pack {display_pack:02d} {name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_pack_{pack_id}_{metric}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon

    @property
    def device_info(self):
        """Return device info for individual pack child device."""
        display_pack = self.pack_id + (0 if self.coordinator.jk_display_index_start == "00" else 1)
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.entry.entry_id}_pack_{self.pack_id}")},
            "name": f"{self.coordinator.device_name} Pack {display_pack:02d}",
            "via_device": (DOMAIN, f"{self.coordinator.entry.entry_id}_total"),
            "manufacturer": "Gobel Power",
            "model": self.coordinator.bms_type,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        data = self.coordinator.data
        if not data:
            return False
        analog_packs = data.get("analog", [])
        return any(p.get("pack_id") == self.pack_id for p in analog_packs)

    @property
    def native_value(self):
        """Return value of pack metric."""
        data = self.coordinator.data
        if not data:
            return None
        analog_packs = data.get("analog", [])
        
        # Find pack data matching self.pack_id
        pack_data = next((p for p in analog_packs if p.get("pack_id") == self.pack_id), None)
        if not pack_data:
            return None
        
        # Map metric keys
        if self._metric == "voltage":
            return pack_data.get("view_voltage")
        elif self._metric == "current":
            return pack_data.get("view_current")
        elif self._metric == "power":
            return pack_data.get("view_power")
        elif self._metric == "soc":
            return pack_data.get("view_SOC")
        elif self._metric == "soh":
            return pack_data.get("view_SOH")
        elif self._metric == "remain_capacity":
            return pack_data.get("view_remain_capacity")
        elif self._metric == "full_capacity":
            return pack_data.get("view_full_capacity")
        elif self._metric == "cycle_number":
            return pack_data.get("view_cycle_number")
        elif self._metric == "balance_current":
            return pack_data.get("view_balance_current")

        return None

class GobelBatteryCellVoltageSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing voltage of a single cell inside a battery pack."""

    def __init__(self, coordinator, pack_id, cell_index):
        """Initialize cell voltage sensor."""
        super().__init__(coordinator)
        self.pack_id = pack_id
        self.cell_index = cell_index
        display_pack = pack_id + (0 if coordinator.jk_display_index_start == "00" else 1)

        self._attr_name = f"{coordinator.device_name} Pack {display_pack:02d} Cell {cell_index:02d} Voltage"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_pack_{pack_id}_cell_{cell_index}_voltage"
        self._attr_native_unit_of_measurement = "mV"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:sine-wave"

    @property
    def device_info(self):
        """Return device info for individual pack child device."""
        display_pack = self.pack_id + (0 if self.coordinator.jk_display_index_start == "00" else 1)
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.entry.entry_id}_pack_{self.pack_id}")},
            "name": f"{self.coordinator.device_name} Pack {display_pack:02d}",
            "via_device": (DOMAIN, f"{self.coordinator.entry.entry_id}_total"),
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        data = self.coordinator.data
        if not data:
            return False
        analog_packs = data.get("analog", [])
        return any(p.get("pack_id") == self.pack_id for p in analog_packs)

    @property
    def native_value(self):
        """Return cell voltage."""
        data = self.coordinator.data
        if not data:
            return None
        analog_packs = data.get("analog", [])
        
        pack_data = next((p for p in analog_packs if p.get("pack_id") == self.pack_id), None)
        if not pack_data:
            return None

        voltages = pack_data.get("cell_voltages", [])
        if self.cell_index - 1 < len(voltages):
            return voltages[self.cell_index - 1]

        return None

class GobelBatteryTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing temperature of a single probe inside a battery pack."""

    def __init__(self, coordinator, pack_id, temp_index):
        """Initialize temperature sensor."""
        super().__init__(coordinator)
        self.pack_id = pack_id
        self.temp_index = temp_index
        display_pack = pack_id + (0 if coordinator.jk_display_index_start == "00" else 1)

        self._attr_name = f"{coordinator.device_name} Pack {display_pack:02d} Temperature {temp_index:02d}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_pack_{pack_id}_temp_{temp_index}"
        self._attr_native_unit_of_measurement = "°C"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:thermometer"

    @property
    def device_info(self):
        """Return device info for individual pack child device."""
        display_pack = self.pack_id + (0 if self.coordinator.jk_display_index_start == "00" else 1)
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.entry.entry_id}_pack_{self.pack_id}")},
            "name": f"{self.coordinator.device_name} Pack {display_pack:02d}",
            "via_device": (DOMAIN, f"{self.coordinator.entry.entry_id}_total"),
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        data = self.coordinator.data
        if not data:
            return False
        analog_packs = data.get("analog", [])
        return any(p.get("pack_id") == self.pack_id for p in analog_packs)

    @property
    def native_value(self):
        """Return temperature."""
        data = self.coordinator.data
        if not data:
            return None
        analog_packs = data.get("analog", [])
        
        pack_data = next((p for p in analog_packs if p.get("pack_id") == self.pack_id), None)
        if not pack_data:
            return None

        temps = pack_data.get("temperatures", [])
        if self.temp_index - 1 < len(temps):
            return temps[self.temp_index - 1]

        return None
