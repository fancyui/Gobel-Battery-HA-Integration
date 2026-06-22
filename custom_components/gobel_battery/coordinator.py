"""DataUpdateCoordinator for the Gobel Battery Monitor integration."""
import logging
import asyncio
from datetime import timedelta
import async_timeout

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

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
    BMS_TYPE_PACE_LV,
    BMS_TYPE_PACE_LV_WIFI,
    BMS_TYPE_JK_PB,
    BMS_TYPE_TDT,
)

from .bms_comm import BMSCommunication
from .pacebms_rs232 import PACEBMS232
from .pacebms_rs485 import PACEBMS485
from .pacebms_wifi import PACEBMSWIFI
from .jkbms_rs485 import JKBMS485
from .tdtbms_rs232 import TDTBMS232

_LOGGER = logging.getLogger(__name__)

class DummyHAComm:
    """Mock class to satisfy driver dependencies on HA_MQTT without publishing."""
    def __init__(self, *args, **kwargs):
        pass
    def publish_sensor_state(self, *args, **kwargs):
        pass
    def publish_sensor_discovery(self, *args, **kwargs):
        pass
    def publish_warn_state(self, *args, **kwargs):
        pass
    def publish_warn_discovery(self, *args, **kwargs):
        pass
    def publish_binary_sensor_state(self, *args, **kwargs):
        pass
    def publish_binary_sensor_discovery(self, *args, **kwargs):
        pass
    def connect(self, *args, **kwargs):
        return True

class GobelBatteryUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Gobel BMS battery data."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.device_name = entry.data.get("device_name", "Gobel Battery")
        self.bms_type = entry.data.get(CONF_BMS_TYPE)
        self.connection_type = entry.data.get(CONF_CONNECTION_TYPE)
        self.battery_port = entry.data.get(CONF_BATTERY_PORT)
        self.ip_address = entry.data.get(CONF_IP_ADDRESS)
        self.ip_port = entry.data.get(CONF_IP_PORT)
        self.usb_port = entry.data.get(CONF_USB_PORT)
        self.baud_rate = entry.data.get(CONF_BAUD_RATE)
        self.max_parallel = entry.data.get(CONF_MAX_PARALLEL, 16)
        self.jk_display_index_start = entry.data.get(CONF_JK_DISPLAY_INDEX_START, "01")
        
        poll_interval = entry.data.get(CONF_POLL_INTERVAL, 5)
        super().__init__(
            hass,
            _LOGGER,
            name=f"Gobel Battery {self.device_name}",
            update_interval=timedelta(seconds=poll_interval),
        )

        self.bms_comm = None
        self.bms = None
        self.dummy_ha = DummyHAComm()

        self.pack_cache = {}
        self.pack_failures = {}
        self.max_failures = 3

    def _setup_bms_sync(self):
        """Synchronous setup of the BMS communication and driver."""
        _LOGGER.info("Initializing BMS connection for: %s", self.device_name)
        self.bms_comm = BMSCommunication(
            interface=self.connection_type,
            serial_port=self.usb_port,
            baud_rate=self.baud_rate,
            ethernet_ip=self.ip_address,
            ethernet_port=self.ip_port,
            buffer_size=1024,
            debug=0
        )
        if not self.bms_comm.connect():
            raise Exception("Failed to connect to BMS communication port")

        # Initialize specific protocol class
        if self.bms_type == BMS_TYPE_PACE_LV:
            if self.battery_port == "rs232":
                self.bms = PACEBMS232(
                    bms_comm=self.bms_comm,
                    ha_comm=self.dummy_ha,
                    bms_type=self.bms_type,
                    data_refresh_interval=self.update_interval.total_seconds(),
                    debug=0,
                    if_random=0
                )
            elif self.battery_port == "rs485":
                self.bms = PACEBMS485(
                    bms_comm=self.bms_comm,
                    ha_comm=self.dummy_ha,
                    data_refresh_interval=self.update_interval.total_seconds(),
                    debug=0,
                    if_random=0
                )
        elif self.bms_type == BMS_TYPE_PACE_LV_WIFI:
            self.bms = PACEBMSWIFI(
                bms_comm=self.bms_comm,
                ha_comm=self.dummy_ha,
                bms_type=self.bms_type,
                data_refresh_interval=self.update_interval.total_seconds(),
                debug=0,
                if_random=0
            )
        elif self.bms_type == BMS_TYPE_JK_PB:
            jk_pack_index_start = 0 if self.jk_display_index_start in ["0", "00"] else 1
            self.bms = JKBMS485(
                bms_comm=self.bms_comm,
                ha_comm=self.dummy_ha,
                bms_type=self.bms_type,
                data_refresh_interval=self.update_interval.total_seconds(),
                debug=0,
                if_random=0,
                ha_comm_jk=None,
                pack_index_start=jk_pack_index_start
            )
        elif self.bms_type == BMS_TYPE_TDT:
            self.bms = TDTBMS232(
                bms_comm=self.bms_comm,
                ha_comm=self.dummy_ha,
                data_refresh_interval=self.update_interval.total_seconds(),
                debug=0,
                if_random=0
            )
        else:
            raise Exception(f"Unsupported BMS type: {self.bms_type}")

    async def async_setup(self):
        """Set up the connection."""
        try:
            await self.hass.async_add_executor_job(self._setup_bms_sync)
            return True
        except Exception as err:
            _LOGGER.error("Failed to set up BMS coordinator for %s: %s", self.device_name, err)
            return False

    def _fetch_data_sync(self):
        """Synchronous update call running inside thread executor."""
        if not self.bms:
            raise UpdateFailed("BMS driver is not set up")

        # Determine pack indices to query
        pack_list = []
        if self.bms_type == BMS_TYPE_PACE_LV and self.battery_port == "rs485":
            for pack_number in range(0, self.max_parallel + 1):
                try:
                    result = self.bms.get_pack_num_data(pack_number)
                    if result == pack_number:
                        pack_list.append(pack_number)
                except Exception:
                    pass
            if not pack_list:
                pack_list = [0]
        elif self.bms_type == BMS_TYPE_TDT:
            try:
                pack_quantity = self.bms.get_pack_quantity_data()
                pack_list = list(range(1, pack_quantity + 1))
            except Exception:
                pack_list = [1]
        else:
            pack_list = [None]

        analog_data = []
        warning_data = []

        if self.bms_type == BMS_TYPE_JK_PB:
            # JK BMS reads frame caches populated by its background listener thread
            analog_data = self.bms.get_analog_data()
            warning_data = self.bms.get_warning_data()
        else:
            for p in pack_list:
                try:
                    analog_pack = self.bms.get_analog_data(p)
                    warning_pack = self.bms.get_warning_data(p)
                    p_id = p if p is not None else 0
                    if analog_pack:
                        if isinstance(analog_pack, list):
                            for idx, item in enumerate(analog_pack):
                                if "pack_id" not in item:
                                    item["pack_id"] = item.get("pack_index", idx)
                            analog_data.extend(analog_pack)
                        else:
                            if "pack_id" not in analog_pack:
                                analog_pack["pack_id"] = analog_pack.get("pack_index", p_id)
                            analog_data.append(analog_pack)
                    if warning_pack:
                        if isinstance(warning_pack, list):
                            for idx, item in enumerate(warning_pack):
                                if "pack_id" not in item:
                                    item["pack_id"] = item.get("pack_index", idx)
                            warning_data.extend(warning_pack)
                        else:
                            if "pack_id" not in warning_pack:
                                warning_pack["pack_id"] = warning_pack.get("pack_index", p_id)
                            warning_data.append(warning_pack)
                except Exception as ex:
                    _LOGGER.error("Error polling pack %s: %s", p, ex)

        # Reconcile with cache to hold old data on occasional read failures
        seen_analog_packs = {item.get("pack_id", i): item for i, item in enumerate(analog_data)}
        seen_warning_packs = {item.get("pack_id", i): item for i, item in enumerate(warning_data)}
        
        final_analog_data = []
        final_warning_data = []
        
        all_pack_ids = set(seen_analog_packs.keys()) | set(seen_warning_packs.keys()) | set(self.pack_cache.keys())
        
        for p_id in all_pack_ids:
            if p_id in seen_analog_packs:
                # Read successful
                self.pack_failures[p_id] = 0
                if p_id not in self.pack_cache:
                    self.pack_cache[p_id] = {}
                self.pack_cache[p_id]['analog'] = seen_analog_packs[p_id]
                if p_id in seen_warning_packs:
                    self.pack_cache[p_id]['warning'] = seen_warning_packs[p_id]
                
                final_analog_data.append(seen_analog_packs[p_id])
                if p_id in seen_warning_packs:
                    final_warning_data.append(seen_warning_packs[p_id])
            else:
                # Read failed
                self.pack_failures[p_id] = self.pack_failures.get(p_id, 0) + 1
                failures = self.pack_failures[p_id]
                
                if failures <= self.max_failures and p_id in self.pack_cache:
                    _LOGGER.debug("Using cached data for pack %s (failure %s/%s)", p_id, failures, self.max_failures)
                    if 'analog' in self.pack_cache[p_id]:
                        final_analog_data.append(self.pack_cache[p_id]['analog'])
                    if 'warning' in self.pack_cache[p_id]:
                        final_warning_data.append(self.pack_cache[p_id]['warning'])
                else:
                    if failures == self.max_failures + 1:
                        _LOGGER.warning("Pack %s data unavailable after %s consecutive failures", p_id, failures)

        return {
            "analog": final_analog_data,
            "warning": final_warning_data,
        }

    async def _async_update_data(self):
        """Fetch data from BMS."""
        # First fetch needs more time for pack discovery (up to 15s wait + processing)
        timeout_seconds = 30 if not getattr(self, '_first_fetch_done', False) else 15
        async with async_timeout.timeout(timeout_seconds):
            try:
                data = await self.hass.async_add_executor_job(self._fetch_data_sync)
                self._first_fetch_done = True
                return data
            except Exception as err:
                raise UpdateFailed(f"BMS communication error: {err}") from err

    def shutdown(self):
        """Release bms sockets and threads."""
        _LOGGER.info("Closing BMS connection for: %s", self.device_name)
        if self.bms and hasattr(self.bms, "stop"):
            try:
                self.bms.stop()
            except Exception as e:
                _LOGGER.error("Error stopping BMS background thread: %s", e)
        if self.bms_comm:
            try:
                self.bms_comm.disconnect()
            except Exception as e:
                _LOGGER.error("Error closing BMS port: %s", e)
