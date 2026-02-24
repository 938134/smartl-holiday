"""Smart Workday integration."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, HolidayMode
from .coordinator import SmartWorkdayDataManager, SmartWorkdayCoordinator

_LOGGER = logging.getLogger(__name__)

# 使用正确的平台名称
PLATFORMS = [Platform.BINARY_SENSOR, Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置配置条目"""
    _LOGGER.debug("设置 Smart Workday: %s", entry.entry_id)
    
    # 确保模式存在
    if "holiday_mode" not in entry.data:
        new_data = dict(entry.data)
        new_data["holiday_mode"] = HolidayMode.WAGE.value
        hass.config_entries.async_update_entry(entry, data=new_data)
    
    # 初始化数据管理器
    calendar_file = entry.data.get("calendar_file", "calendar.yaml")
    calendar_path = hass.config.path("custom_components", DOMAIN, calendar_file)
    data_manager = SmartWorkdayDataManager(hass, calendar_path)
    
    # 设置假期模式
    data_manager.update_holiday_mode(HolidayMode(entry.data.get("holiday_mode", HolidayMode.WAGE.value)))
    
    # 初始化协调器
    coordinator = SmartWorkdayCoordinator(hass, entry.entry_id, data_manager)
    await coordinator.async_config_entry_first_refresh()
    
    # 存储数据
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "coordinator": coordinator,
        "data_manager": data_manager,
    }
    
    # 设置平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目"""
    _LOGGER.debug("卸载 Smart Workday: %s", entry.entry_id)
    
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    
    return False