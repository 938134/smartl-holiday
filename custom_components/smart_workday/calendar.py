"""Calendar platform for Smart Workday."""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt

from .const import DOMAIN
from .coordinator import SmartWorkdayCoordinator

_LOGGER = logging.getLogger(__name__)


class SmartWorkdayCalendar(CoordinatorEntity, CalendarEntity):
    """日历实体 - 显示所有假期"""
    
    def __init__(self, coordinator: SmartWorkdayCoordinator, device_info: DeviceInfo):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry_id}_calendar"
        self._attr_name = "智能工作日日历"
        self._attr_icon = "mdi:calendar-month"
        self._attr_device_info = device_info
        self._event_list: List[CalendarEvent] = []

    def _generate_event_id(self, start, name, source) -> str:
        """生成唯一事件ID"""
        return hashlib.md5(f"{start}_{name}_{source}".encode()).hexdigest()

    def _create_event(self, start_date, end_date, name, source) -> CalendarEvent:
        """创建日历事件"""
        # 解析开始日期
        if isinstance(start_date, str):
            start = dt.parse_date(start_date)
            if not start:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start = start_date
            
        # 解析结束日期
        if isinstance(end_date, str):
            end = dt.parse_date(end_date)
            if not end:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end = end_date
        
        # 转换为datetime
        event_start = datetime.combine(start, datetime.min.time())
        event_end = datetime.combine(end + timedelta(days=1), datetime.min.time())
        
        # 添加时区
        if event_start.tzinfo is None:
            event_start = event_start.replace(tzinfo=dt.DEFAULT_TIME_ZONE)
        if event_end.tzinfo is None:
            event_end = event_end.replace(tzinfo=dt.DEFAULT_TIME_ZONE)
        
        return CalendarEvent(
            start=event_start,
            end=event_end,
            summary=name,
            description="调休上班日" if "调休" in name else f"来源: {source}",
            uid=self._generate_event_id(start_date, name, source),
        )

    def _generate_events(self) -> List[CalendarEvent]:
        """生成所有事件"""
        events = []
        data = self.coordinator.data_manager.get_calendar_events()
        
        # 处理所有来源
        for source in ["holidays", "customdays", "schooldays"]:
            for item in data.get(source, []):
                if "date" in item:
                    events.append(self._create_event(
                        item["date"], item["date"], item["name"], source
                    ))
                elif "start" in item and "end" in item:
                    events.append(self._create_event(
                        item["start"], item["end"], item["name"], source
                    ))
        
        _LOGGER.debug("生成了 %d 个日历事件", len(events))
        return events

    async def async_get_events(self, hass, start_date, end_date) -> List[CalendarEvent]:
        """获取时间段内的事件"""
        # 确保日期有时区
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=dt.DEFAULT_TIME_ZONE)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=dt.DEFAULT_TIME_ZONE)
        
        # 在executor中生成事件
        all_events = await hass.async_add_executor_job(self._generate_events)
        
        # 过滤时间范围
        return [
            e for e in all_events 
            if e.start <= end_date and e.end >= start_date
        ]

    @property
    def event(self) -> Optional[CalendarEvent]:
        """返回下一个即将发生的事件"""
        if not self._event_list:
            return None
        
        now = dt.now()
        future = [e for e in self._event_list if e.start > now]
        return min(future, key=lambda e: e.start) if future else None

    async def async_update(self) -> None:
        """更新日历事件"""
        try:
            self._event_list = await self.hass.async_add_executor_job(self._generate_events)
            _LOGGER.debug("日历更新完成，共 %d 个事件", len(self._event_list))
        except Exception as e:
            _LOGGER.error("更新日历失败: %s", e)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置日历实体"""
    _LOGGER.debug("设置日历: %s", entry.entry_id)
    
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get("name", "智能工作日"),
        manufacturer="Smart Workday",
        model="工作日传感器",
        sw_version="2.0.0",
    )
    
    calendar = SmartWorkdayCalendar(coordinator, device_info)
    async_add_entities([calendar])
    _LOGGER.info("已添加日历实体")