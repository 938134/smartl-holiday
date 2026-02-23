"""Sensor platform for Smart Holiday."""

import logging
import yaml
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, List

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt

from .const import (
    ATTR_TODAY_EVENTS,
    ATTR_EVENT_NAMES,
    ATTR_EVENT_TYPES,
    ATTR_PRIMARY_EVENT,
    ATTR_IS_HOLIDAY,
    ATTR_IS_WORKDAY_SPECIAL,
    ATTR_UPCOMING,
    DEFAULT_NAME,
    DOMAIN,
    STATE_WORKDAY,
    STATE_WORKDAY_SPECIAL,
    STATE_HOLIDAY,
    STATE_HOLIDAY_CUSTOM,
    STATE_WEEKEND,
    EVENT_TYPE_NATIONAL,
    EVENT_TYPE_CUSTOM,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor and calendar platforms."""
    name = DEFAULT_NAME
    
    # 使用组件目录下的 calendar.yaml
    component_dir = os.path.dirname(__file__)
    calendar_path = os.path.join(component_dir, "calendar.yaml")
    
    async_add_entities([
        SmartHolidaySensor(name, calendar_path, hass),
        SmartHolidayCalendar(name, calendar_path, hass)
    ], True)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor and calendar platforms from config entry."""
    name = DEFAULT_NAME
    
    # 使用组件目录下的 calendar.yaml
    component_dir = os.path.dirname(__file__)
    calendar_path = os.path.join(component_dir, "calendar.yaml")
    
    async_add_entities([
        SmartHolidaySensor(name, calendar_path, hass),
        SmartHolidayCalendar(name, calendar_path, hass)
    ], True)


class SmartHolidaySensor(SensorEntity):
    """Representation of a Smart Holiday Sensor."""

    def __init__(self, name: str, calendar_path: str, hass: HomeAssistant) -> None:
        """Initialize the sensor."""
        self._attr_name = name
        self._calendar_path = calendar_path
        self._hass = hass
        self._attr_unique_id = f"smart_holiday_{name}"
        self._attr_native_value = STATE_WORKDAY
        self._attr_extra_state_attributes = {}
        self._attr_icon = "mdi:calendar"

    def _load_calendar_data(self) -> Dict:
        """Load calendar data from YAML file."""
        try:
            with open(self._calendar_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data or {}
        except Exception as e:
            _LOGGER.error("Failed to load calendar file %s: %s", self._calendar_path, e)
            return {}

    def _is_match(self, check_date: date, item: Any) -> bool:
        """Check if date matches the item."""
        if isinstance(item, dict):
            # 单天事件
            if "date" in item:
                return item["date"] == check_date.isoformat()
            # 范围事件
            elif "start" in item and "end" in item:
                start = datetime.strptime(item["start"], "%Y-%m-%d").date()
                end = datetime.strptime(item["end"], "%Y-%m-%d").date()
                return start <= check_date <= end
        return False

    def _get_upcoming_days(self, data: Dict, start_date: date, days: int = 7) -> List:
        """Get upcoming events for next N days."""
        upcoming = []
        
        for i in range(1, days + 1):
            future_date = start_date + timedelta(days=i)
            future_events = []
            
            # 检查 holidays
            for item in data.get("holidays", []):
                if self._is_match(future_date, item):
                    future_events.append({
                        "name": item.get("name", "节假日"),
                        "source": "holidays"
                    })
            
            # 检查 customdays
            for item in data.get("customdays", []):
                if self._is_match(future_date, item):
                    future_events.append({
                        "name": item.get("name", "自定义假期"),
                        "source": "customdays"
                    })
            
            if future_events:
                upcoming.append({
                    "date": future_date.isoformat(),
                    "events": [e["name"] for e in future_events]
                })
        
        return upcoming

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        today = dt.now().date()
        data = self._load_calendar_data()
        
        today_events = []
        event_names = []
        event_types = []
        
        # 优先级：holidays > customdays
        final_state = None
        
        # 1. 检查法定节假日（包含调休）
        for item in data.get("holidays", []):
            if self._is_match(today, item):
                event_name = item.get("name", "节假日")
                event = {
                    "name": event_name,
                    "source": "holidays",
                    "type": EVENT_TYPE_NATIONAL
                }
                today_events.append(event)
                event_names.append(event_name)
                event_types.append(EVENT_TYPE_NATIONAL)
                
                # 判断是节假日还是调休
                if "调休" in event_name:
                    final_state = STATE_WORKDAY_SPECIAL
                else:
                    final_state = STATE_HOLIDAY
        
        # 2. 检查自定义节假日（学校假期、佛诞等）
        for item in data.get("customdays", []):
            if self._is_match(today, item):
                event_name = item.get("name", "自定义假期")
                event = {
                    "name": event_name,
                    "source": "customdays",
                    "type": EVENT_TYPE_CUSTOM
                }
                today_events.append(event)
                event_names.append(event_name)
                event_types.append(EVENT_TYPE_CUSTOM)
                
                # 如果没有更高级别的事件，才设置为 holiday_custom
                if not final_state:
                    final_state = STATE_HOLIDAY_CUSTOM
        
        # 3. 如果没有特殊事件，根据星期判断
        if not final_state:
            final_state = STATE_WORKDAY if today.weekday() < 5 else STATE_WEEKEND
        
        # 去重保留顺序
        unique_names = []
        for name in event_names:
            if name not in unique_names:
                unique_names.append(name)
        
        unique_types = []
        for t in event_types:
            if t not in unique_types:
                unique_types.append(t)
        
        # 更新属性
        self._attr_native_value = final_state
        self._attr_extra_state_attributes = {
            ATTR_TODAY_EVENTS: today_events,
            ATTR_EVENT_NAMES: unique_names,
            ATTR_EVENT_TYPES: unique_types,
            ATTR_PRIMARY_EVENT: unique_names[0] if unique_names else "",
            ATTR_IS_HOLIDAY: final_state in [STATE_HOLIDAY, STATE_HOLIDAY_CUSTOM],
            ATTR_IS_WORKDAY_SPECIAL: final_state == STATE_WORKDAY_SPECIAL,
            ATTR_UPCOMING: self._get_upcoming_days(data, today),
            "today_date": today.isoformat(),
            "weekday": today.weekday(),
            "is_weekend": today.weekday() >= 5,
        }


class SmartHolidayCalendar(CalendarEntity):
    """Representation of a Smart Holiday Calendar."""

    def __init__(self, name: str, calendar_path: str, hass: HomeAssistant) -> None:
        """Initialize the calendar."""
        self._attr_name = f"{name} Calendar"
        self._calendar_path = calendar_path
        self._hass = hass
        self._attr_unique_id = f"smart_holiday_calendar_{name}"
        self._attr_icon = "mdi:calendar-month"

    def _load_calendar_data(self) -> Dict:
        """Load calendar data from YAML file."""
        try:
            with open(self._calendar_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data or {}
        except Exception as e:
            _LOGGER.error("Failed to load calendar file %s: %s", self._calendar_path, e)
            return {}

    def _create_event(self, start_date: date, end_date: date, name: str, source: str) -> CalendarEvent:
        """Create a calendar event with appropriate color."""
        # 调休上班日特殊处理
        if "调休" in name:
            description = "调休上班日"
        else:
            description = f"来源: {source}"
        
        return CalendarEvent(
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date + timedelta(days=1), datetime.min.time()),
            summary=name,
            description=description,
            location="",
            uid=f"{start_date}_{name}",
        )

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Get all events in a specific time frame."""
        events = []
        data = self._load_calendar_data()
        
        current = start_date.date()
        end = end_date.date()
        
        # 遍历日期范围
        while current <= end:
            # 检查 holidays
            for item in data.get("holidays", []):
                if isinstance(item, dict):
                    # 单天事件
                    if "date" in item and item["date"] == current.isoformat():
                        events.append(self._create_event(
                            current, current,
                            item.get("name", "节假日"),
                            "holidays"
                        ))
                    # 范围事件
                    elif "start" in item and "end" in item:
                        start = datetime.strptime(item["start"], "%Y-%m-%d").date()
                        end_date_range = datetime.strptime(item["end"], "%Y-%m-%d").date()
                        if start <= current <= end_date_range:
                            # 只在范围的开始日创建一个事件（全天事件会自动跨天）
                            if current == start:
                                events.append(self._create_event(
                                    start, end_date_range,
                                    item.get("name", "节假日"),
                                    "holidays"
                                ))
            
            # 检查 customdays
            for item in data.get("customdays", []):
                if isinstance(item, dict):
                    # 单天事件
                    if "date" in item and item["date"] == current.isoformat():
                        events.append(self._create_event(
                            current, current,
                            item.get("name", "自定义假期"),
                            "customdays"
                        ))
                    # 范围事件
                    elif "start" in item and "end" in item:
                        start = datetime.strptime(item["start"], "%Y-%m-%d").date()
                        end_date_range = datetime.strptime(item["end"], "%Y-%m-%d").date()
                        if start <= current <= end_date_range:
                            if current == start:
                                events.append(self._create_event(
                                    start, end_date_range,
                                    item.get("name", "自定义假期"),
                                    "customdays"
                                ))
            
            current += timedelta(days=1)
        
        return events

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""
        return None