"""Coordinator for Smart Workday - 共享数据管理"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt

from .const import (
    DOMAIN,
    HolidayMode,
    WorkdayState,
    ATTR_IS_WORKDAY,
    ATTR_IS_HOLIDAY,
    ATTR_IS_WEEKEND,
    ATTR_IS_SPECIAL_WORKDAY,
    ATTR_IS_STUDENT_HOLIDAY,
    WEEKDAY_NAMES,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=60)


@dataclass
class DayInfo:
    """今天的信息数据类"""
    date: str
    weekday: int
    weekday_name: str
    state: WorkdayState
    state_name: str
    is_workday: bool
    is_holiday: bool
    is_weekend: bool
    is_special_workday: bool
    is_student_holiday: bool  # 添加学生假期标志
    mode: HolidayMode
    mode_name: str
    events: List[Dict] = field(default_factory=list)
    event_names: List[str] = field(default_factory=list)
    primary_event: str = ""
    upcoming_days: List[Dict] = field(default_factory=list)


class SmartWorkdayDataManager:
    """数据管理器 - 处理所有数据加载和计算"""
    
    def __init__(self, hass: HomeAssistant, calendar_path: str):
        self.hass = hass
        self.calendar_path = calendar_path
        self._data_cache = None
        self._last_loaded = None
        self._holiday_mode = HolidayMode.WAGE
        
    def update_holiday_mode(self, mode: HolidayMode):
        """更新假期模式"""
        self._holiday_mode = mode
        
    def load_calendar_data(self, force_reload: bool = False) -> Dict:
        """加载日历数据"""
        now = dt.now()
        
        # 缓存1分钟
        if not force_reload and self._data_cache and self._last_loaded:
            if (now - self._last_loaded).total_seconds() < 60:
                return self._data_cache
        
        try:
            import yaml
            import os
            
            if not os.path.exists(self.calendar_path):
                return {"holidays": [], "customdays": [], "studentdays": []}
            
            with open(self.calendar_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                data.setdefault("holidays", [])
                data.setdefault("customdays", [])
                data.setdefault("studentdays", [])  # 从 schooldays 改为 studentdays
                
                self._data_cache = data
                self._last_loaded = now
                return data
                
        except Exception as e:
            _LOGGER.error("加载日历文件失败: %s", e)
            return {"holidays": [], "customdays": [], "studentdays": []}
    
    def get_today_events(self, check_date: Optional[date] = None) -> List[Dict]:
        """获取指定日期的所有事件"""
        if check_date is None:
            check_date = dt.now().date()
        
        data = self.load_calendar_data()
        events = []
        
        def is_match(date_obj: date, item: Dict) -> bool:
            """检查日期是否匹配事件"""
            try:
                if "date" in item:
                    return item["date"] == date_obj.isoformat()
                elif "start" in item and "end" in item:
                    start = datetime.strptime(item["start"], "%Y-%m-%d").date()
                    end = datetime.strptime(item["end"], "%Y-%m-%d").date()
                    return start <= date_obj <= end
            except Exception as e:
                _LOGGER.debug("日期匹配错误: %s", e)
            return False
        
        # 法定节假日
        for item in data.get("holidays", []):
            if is_match(check_date, item):
                events.append({
                    "name": item.get("name", "节假日"),
                    "type": "holiday" if "调休" not in item.get("name", "") else "special",
                })
        
        # 自定义假期
        for item in data.get("customdays", []):
            if is_match(check_date, item):
                events.append({
                    "name": item.get("name", "自定义假期"),
                    "type": "custom",
                })
        
        # 学生假期 - 只有学生模式才添加
        if self._holiday_mode == HolidayMode.STUDENT:
            for item in data.get("studentdays", []):  # 从 schooldays 改为 studentdays
                if is_match(check_date, item):
                    events.append({
                        "name": item.get("name", "学生假期"),
                        "type": "student",  # 改为 student
                    })
        
        return events
    
    def analyze_day(self, today: date, events: List[Dict]) -> DayInfo:
        """分析一天的状态"""
        flags = {
            "holiday": False,
            "special": False,
            "custom": False,
            "student": False,  # 改为 student
        }
        
        event_names = []
        
        for e in events:
            event_names.append(e["name"])
            
            if e["type"] == "holiday":
                flags["holiday"] = True
            elif e["type"] == "special":
                flags["special"] = True
            elif e["type"] == "custom":
                flags["custom"] = True
            elif e["type"] == "student":  # 改为 student
                flags["student"] = True
        
        is_weekend = today.weekday() >= 5
        
        # 确定状态
        if flags["special"]:
            state = WorkdayState.WORKDAY_SPECIAL
            is_workday = True
        else:
            has_holiday = False
            
            if self._holiday_mode == HolidayMode.WAGE:
                has_holiday = flags["holiday"] or flags["custom"]
            elif self._holiday_mode == HolidayMode.STUDENT:
                has_holiday = flags["holiday"] or flags["student"] or flags["custom"]  # 改为 student
            elif self._holiday_mode == HolidayMode.FREE:
                has_holiday = flags["custom"]
            
            if has_holiday:
                state = WorkdayState.HOLIDAY_CUSTOM if flags["custom"] else WorkdayState.HOLIDAY
                is_workday = False
            elif is_weekend:
                state = WorkdayState.WEEKEND
                is_workday = False
            else:
                state = WorkdayState.WORKDAY
                is_workday = True
        
        # 生成显示名称
        if is_workday:
            if flags["special"]:
                day_name = f"{'、'.join(event_names)}上班"
            else:
                day_name = "工作日"
        else:
            if event_names:
                day_name = f"{'、'.join(event_names)}放假"
            elif is_weekend:
                day_name = "周末"
            else:
                day_name = "休息"
        
        return DayInfo(
            date=today.isoformat(),
            weekday=today.weekday(),
            weekday_name=WEEKDAY_NAMES[today.weekday()],
            state=state,
            state_name=state.display_name,
            is_workday=is_workday,
            is_holiday=state in [WorkdayState.HOLIDAY, WorkdayState.HOLIDAY_CUSTOM],
            is_weekend=state == WorkdayState.WEEKEND,
            is_special_workday=state == WorkdayState.WORKDAY_SPECIAL,
            is_student_holiday=flags["student"],  # 添加学生假期标志
            mode=self._holiday_mode,
            mode_name=self._holiday_mode.display_name,
            events=events,
            event_names=list(dict.fromkeys(event_names)),
            primary_event=event_names[0] if event_names else "",
        )
    
    def get_upcoming_days(self, today: date, days: int = 7) -> List[Dict]:
        """获取未来几天信息"""
        upcoming = []
        for i in range(1, days + 1):
            future = today + timedelta(days=i)
            events = self.get_today_events(future)
            if events:
                upcoming.append({
                    "date": future.isoformat(),
                    "events": [e["name"] for e in events]
                })
        return upcoming
    
    def get_calendar_events(self) -> Dict:
        """获取所有日历事件（用于日历实体）"""
        return self.load_calendar_data(force_reload=True)


class SmartWorkdayCoordinator(DataUpdateCoordinator):
    """协调器 - 管理数据更新"""
    
    def __init__(self, hass: HomeAssistant, entry_id: str, data_manager: SmartWorkdayDataManager):
        super().__init__(
            hass,
            _LOGGER,
            name=f"Smart Workday {entry_id}",
            update_interval=SCAN_INTERVAL,
        )
        self.entry_id = entry_id
        self.data_manager = data_manager

    async def _async_update_data(self) -> Dict[str, Any]:
        """更新数据"""
        try:
            today = dt.now().date()
            
            # 获取当天事件
            events = await self.hass.async_add_executor_job(
                self.data_manager.get_today_events, today
            )
            
            # 分析当天
            day_info = await self.hass.async_add_executor_job(
                self.data_manager.analyze_day, today, events
            )
            
            # 获取未来事件
            upcoming = await self.hass.async_add_executor_job(
                self.data_manager.get_upcoming_days, today
            )
            
            # 构建返回数据
            data = {
                # 核心状态
                "state": day_info.state.value,
                "state_name": day_info.state_name,
                
                # 日期信息
                "date": day_info.date,
                "weekday": day_info.weekday,
                "weekday_name": day_info.weekday_name,
                
                # 布尔标志 - 这些都会成为二进制传感器
                ATTR_IS_WORKDAY: day_info.is_workday,
                ATTR_IS_HOLIDAY: day_info.is_holiday,
                ATTR_IS_WEEKEND: day_info.is_weekend,
                ATTR_IS_SPECIAL_WORKDAY: day_info.is_special_workday,
                ATTR_IS_STUDENT_HOLIDAY: day_info.is_student_holiday,
                
                # 模式信息
                "mode": day_info.mode.value,
                "mode_name": day_info.mode_name,
                
                # 事件信息
                "events": day_info.events,
                "event_names": day_info.event_names,
                "primary_event": day_info.primary_event,
                
                # 未来事件
                "upcoming": upcoming,
            }
            
            return data
            
        except Exception as err:
            _LOGGER.error("更新数据失败: %s", err)
            raise UpdateFailed(f"更新失败: {err}")