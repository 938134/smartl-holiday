"""Sensor platform for SmartL Holiday."""

import logging
import yaml
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt

from .const import (
    ATTR_HOLIDAY_NAME,
    ATTR_HOLIDAY_TYPE,
    ATTR_TODAY_EVENTS,
    ATTR_UPCOMING,
    CONF_CALENDAR_FILE,
    DEFAULT_NAME,
    DOMAIN,
    HOLIDAY_TYPE_CUSTOM,
    HOLIDAY_TYPE_NATIONAL,
    HOLIDAY_TYPE_SCHOOL,
    HOLIDAY_TYPE_WORKDAY_SPECIAL,
    STATE_HOLIDAY,
    STATE_WEEKEND,
    STATE_WORKDAY,
    STATE_WORKDAY_SPECIAL,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    name = config.get(CONF_NAME, DEFAULT_NAME)
    calendar_file = config.get(CONF_CALENDAR_FILE)
    
    async_add_entities([SmartLHolidaySensor(name, calendar_file, hass)], True)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform from config entry."""
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    calendar_file = entry.data.get(CONF_CALENDAR_FILE)
    
    async_add_entities([SmartLHolidaySensor(name, calendar_file, hass)], True)


class SmartLHolidaySensor(SensorEntity):
    """Representation of a SmartL Holiday Sensor."""

    def __init__(self, name: str, calendar_file: str, hass: HomeAssistant) -> None:
        """Initialize the sensor."""
        self._attr_name = name
        self._calendar_file = calendar_file
        self._hass = hass
        self._attr_unique_id = f"smartl_holiday_{name}"
        self._attr_native_value = STATE_WORKDAY
        self._attr_extra_state_attributes = {}
        self._calendar_data = {
            "holidays": [],
            "school_holidays": [],
            "workdays_special": [],
            "customdays": []
        }

    def _load_calendar_data(self) -> Dict:
        """Load calendar data from YAML file."""
        try:
            with open(self._calendar_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data or {}
        except Exception as e:
            _LOGGER.error("Failed to load calendar file %s: %s", self._calendar_file, e)
            return {}

    def _parse_date_range(self, date_str: str) -> date:
        """Parse date string to date object."""
        if isinstance(date_str, date):
            return date_str
        if isinstance(date_str, datetime):
            return date_str.date()
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    def _is_in_range(self, check_date: date, start: str, end: str = None) -> bool:
        """Check if date is in range."""
        start_date = self._parse_date_range(start)
        if end:
            end_date = self._parse_date_range(end)
            return start_date <= check_date <= end_date
        return check_date == start_date

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        today = dt.now().date()
        data = self._load_calendar_data()
        
        if not data:
            self._attr_native_value = STATE_WORKDAY if today.weekday() < 5 else STATE_WEEKEND
            return

        # 初始化
        today_events = []
        holiday_type = None
        holiday_name = None
        found = False

        # 1. 检查调休上班日（优先级最高）
        for item in data.get("workdays_special", []):
            if isinstance(item, dict):
                if item.get("date") == today.isoformat():
                    self._attr_native_value = STATE_WORKDAY_SPECIAL
                    holiday_name = item.get("name", "调休上班")
                    holiday_type = HOLIDAY_TYPE_WORKDAY_SPECIAL
                    today_events.append(holiday_name)
                    found = True
                    break
            elif isinstance(item, str) and item == today.isoformat():
                self._attr_native_value = STATE_WORKDAY_SPECIAL
                holiday_name = "调休上班"
                holiday_type = HOLIDAY_TYPE_WORKDAY_SPECIAL
                today_events.append(holiday_name)
                found = True
                break

        # 2. 检查法定节假日
        if not found:
            for item in data.get("holidays", []):
                if isinstance(item, dict):
                    if "start" in item and "end" in item:
                        if self._is_in_range(today, item["start"], item["end"]):
                            self._attr_native_value = STATE_HOLIDAY
                            holiday_name = item.get("name", "节假日")
                            holiday_type = HOLIDAY_TYPE_NATIONAL
                            today_events.append(holiday_name)
                            found = True
                            break
                    elif "date" in item and item["date"] == today.isoformat():
                        self._attr_native_value = STATE_HOLIDAY
                        holiday_name = item.get("name", "节假日")
                        holiday_type = HOLIDAY_TYPE_NATIONAL
                        today_events.append(holiday_name)
                        found = True
                        break
                elif isinstance(item, str) and item == today.isoformat():
                    self._attr_native_value = STATE_HOLIDAY
                    holiday_name = "法定节假日"
                    holiday_type = HOLIDAY_TYPE_NATIONAL
                    today_events.append(holiday_name)
                    found = True
                    break

        # 3. 检查学校假期
        if not found:
            for item in data.get("school_holidays", []):
                if isinstance(item, dict) and "start" in item and "end" in item:
                    if self._is_in_range(today, item["start"], item["end"]):
                        self._attr_native_value = STATE_HOLIDAY
                        holiday_name = item.get("name", "学校假期")
                        holiday_type = HOLIDAY_TYPE_SCHOOL
                        today_events.append(holiday_name)
                        found = True
                        break

        # 4. 检查自定义节日（不影响状态）
        for item in data.get("customdays", []):
            if isinstance(item, dict):
                if item.get("date") == today.isoformat():
                    custom_name = item.get("name", "自定义节日")
                    today_events.append(custom_name)
                    if not holiday_name:
                        holiday_name = custom_name
                        holiday_type = HOLIDAY_TYPE_CUSTOM
            elif isinstance(item, str) and item == today.isoformat():
                today_events.append("自定义节日")
                if not holiday_name:
                    holiday_name = "自定义节日"
                    holiday_type = HOLIDAY_TYPE_CUSTOM

        # 5. 如果没有特殊日子，根据星期判断
        if not found:
            self._attr_native_value = STATE_WORKDAY if today.weekday() < 5 else STATE_WEEKEND

        # 6. 计算未来假期
        upcoming = []
        for i in range(1, 8):
            future_date = today + timedelta(days=i)
            future_events = []
            
            # 检查未来几天的假期
            for item in data.get("holidays", []):
                if isinstance(item, dict) and "start" in item and "end" in item:
                    if self._is_in_range(future_date, item["start"], item["end"]):
                        future_events.append(item.get("name", "节假日"))
            
            for item in data.get("school_holidays", []):
                if isinstance(item, dict) and "start" in item and "end" in item:
                    if self._is_in_range(future_date, item["start"], item["end"]):
                        future_events.append(item.get("name", "学校假期"))
            
            for item in data.get("workdays_special", []):
                if isinstance(item, dict) and item.get("date") == future_date.isoformat():
                    future_events.append(item.get("name", "调休上班"))
            
            if future_events:
                upcoming.append({
                    "date": future_date.isoformat(),
                    "events": future_events
                })

        # 更新属性
        self._attr_extra_state_attributes = {
            ATTR_HOLIDAY_NAME: holiday_name or "",
            ATTR_HOLIDAY_TYPE: holiday_type or "",
            ATTR_TODAY_EVENTS: today_events,
            ATTR_UPCOMING: upcoming,
            "today_date": today.isoformat(),
            "weekday": today.weekday(),
            "is_weekend": today.weekday() >= 5,
        }