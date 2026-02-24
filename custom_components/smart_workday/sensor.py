"""Sensor platform for Smart Workday."""

import logging
from typing import Dict, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    BINARY_SENSOR_TYPES,
    ATTR_IS_WORKDAY,
    ATTR_IS_HOLIDAY,
    ATTR_IS_WEEKEND,
    ATTR_IS_SPECIAL_WORKDAY,
    ATTR_IS_SCHOOL_HOLIDAY,
)
from .coordinator import SmartWorkdayCoordinator

_LOGGER = logging.getLogger(__name__)


class SmartWorkdayBaseEntity(CoordinatorEntity):
    """传感器基础类"""
    
    def __init__(self, coordinator: SmartWorkdayCoordinator, device_info: DeviceInfo, 
                 unique_id: str, name: str, icon: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry_id}_{unique_id}"
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_info = device_info
        self._attr_should_poll = False


class SmartWorkdayMainSensor(SmartWorkdayBaseEntity, BinarySensorEntity):
    """主传感器 - 返回是否是工作日（作为二进制传感器）"""
    
    def __init__(self, coordinator: SmartWorkdayCoordinator, device_info: DeviceInfo):
        super().__init__(coordinator, device_info, "main", "智能工作日", "mdi:calendar")
        self._attr_device_class = "workday"  # 自定义设备类

    @property
    def is_on(self) -> bool:
        """返回是否是工作日 (True=工作日, False=非工作日)"""
        return self.coordinator.data.get(ATTR_IS_WORKDAY, False) if self.coordinator.data else False

    @property
    def native_value(self) -> str:
        """返回中文状态显示"""
        return "是" if self.is_on else "否"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """返回所有属性"""
        return self.coordinator.data or {}


class SmartWorkdayBinarySensor(SmartWorkdayBaseEntity, BinarySensorEntity):
    """二进制传感器 - 各种布尔状态"""
    
    def __init__(self, coordinator: SmartWorkdayCoordinator, sensor_type: str, 
                 name: str, device_info: DeviceInfo, config: Dict[str, str]):
        super().__init__(coordinator, device_info, sensor_type, name, config["icon"])
        self._sensor_type = sensor_type
        self._attr_device_class = config["device_class"]

    @property
    def is_on(self) -> bool:
        """返回开关状态"""
        return self.coordinator.data.get(self._sensor_type, False) if self.coordinator.data else False

    @property
    def native_value(self) -> str:
        """返回中文状态显示"""
        return "是" if self.is_on else "否"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置传感器实体"""
    _LOGGER.debug("设置传感器: %s", entry.entry_id)
    
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get("name", "智能工作日"),
        manufacturer="Smart Workday",
        model="工作日传感器",
        sw_version="2.0.0",
    )
    
    entities = [SmartWorkdayMainSensor(coordinator, device_info)]
    
    # 添加所有二进制传感器
    for sensor_type, config in BINARY_SENSOR_TYPES.items():
        entities.append(SmartWorkdayBinarySensor(
            coordinator, sensor_type, config["name"], device_info, config
        ))
    
    async_add_entities(entities)
    _LOGGER.info("已添加 %d 个传感器实体", len(entities))