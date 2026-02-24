"""Constants for Smart Workday."""

from enum import Enum
from typing import Final, Dict, List

DOMAIN: Final = "smart_workday"
DEFAULT_NAME: Final = "智能工作日"


class HolidayMode(str, Enum):
    """假期模式"""
    WAGE = "wage"      # 工薪模式：法定+自定义
    STUDENT = "student"  # 学生模式：法定+学生+自定义
    FREE = "free"      # 自由模式：只有自定义

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        return _MODE_NAMES[self]

    @property
    def description(self) -> str:
        """获取模式描述"""
        return _MODE_DESCRIPTIONS[self]

    @property
    def icon(self) -> str:
        """获取模式图标"""
        return _MODE_ICONS[self]


# 模式名称映射
_MODE_NAMES: Dict[HolidayMode, str] = {
    HolidayMode.WAGE: "工薪模式",
    HolidayMode.STUDENT: "学生模式",
    HolidayMode.FREE: "自由模式",
}

# 模式描述映射
_MODE_DESCRIPTIONS: Dict[HolidayMode, str] = {
    HolidayMode.WAGE: "法定节假日 + 自定义假期",
    HolidayMode.STUDENT: "法定节假日 + 学生假期 + 自定义假期",
    HolidayMode.FREE: "只有自定义假期算放假",
}

# 模式图标映射
_MODE_ICONS: Dict[HolidayMode, str] = {
    HolidayMode.WAGE: "👔",
    HolidayMode.STUDENT: "📚",
    HolidayMode.FREE: "🌟",
}


class WorkdayState(str, Enum):
    """工作日状态"""
    WORKDAY = "workday"
    WORKDAY_SPECIAL = "workday_special"
    HOLIDAY = "holiday"
    HOLIDAY_CUSTOM = "holiday_custom"
    WEEKEND = "weekend"

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        return _STATE_NAMES[self]


# 状态中文名称
_STATE_NAMES: Dict[WorkdayState, str] = {
    WorkdayState.WORKDAY: "工作日",
    WorkdayState.WORKDAY_SPECIAL: "调休日",
    WorkdayState.HOLIDAY: "假日",
    WorkdayState.HOLIDAY_CUSTOM: "自定义假日",
    WorkdayState.WEEKEND: "双休日",
}


# 属性常量
ATTR_IS_WORKDAY: Final = "is_workday"
ATTR_IS_HOLIDAY: Final = "is_holiday"
ATTR_IS_WEEKEND: Final = "is_weekend"
ATTR_IS_SPECIAL_WORKDAY: Final = "is_special_workday"
ATTR_IS_STUDENT_HOLIDAY: Final = "is_student_holiday"


# 二进制传感器配置 - 修改 device_class 让所有传感器都显示"开启"/"关闭"
BINARY_SENSOR_TYPES: Dict[str, Dict[str, str]] = {
    ATTR_IS_WORKDAY: {
        "name": "工作日",
        "icon": "mdi:briefcase",
        "device_class": None,  # 设为 None 显示"开启"/"关闭"
    },
    ATTR_IS_HOLIDAY: {
        "name": "假日",
        "icon": "mdi:party-popper",
        "device_class": None,  # 设为 None 显示"开启"/"关闭"
    },
    ATTR_IS_WEEKEND: {
        "name": "双休日",
        "icon": "mdi:weather-sunny",
        "device_class": None,  # 设为 None 显示"开启"/"关闭"
    },
    ATTR_IS_SPECIAL_WORKDAY: {
        "name": "调休日",
        "icon": "mdi:alert",
        "device_class": None,  # 设为 None 显示"开启"/"关闭"
    },
    ATTR_IS_STUDENT_HOLIDAY: {
        "name": "学生假期",
        "icon": "mdi:school",
        "device_class": None,  # 设为 None 显示"开启"/"关闭"
    },
}

# 星期名称
WEEKDAY_NAMES: Final[List[str]] = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 默认YAML模板
DEFAULT_YAML_TEMPLATE: Final = """# 法定节假日（包含调休）
holidays:
  # 单天事件格式
  # - date: "2026-01-01"
  #   name: "元旦"
  # 范围事件格式
  # - start: "2026-02-17"
  #   end: "2026-02-23"
  #   name: "春节"

# 通用自定义假期（所有模式都生效）
customdays:
  # - date: "2026-03-12"
  #   name: "植树节"

# 学生假期（仅学生模式生效）
studentdays:
  # - start: "2026-01-20"
  #   end: "2026-02-15"
  #   name: "寒假"
"""

# 配置错误
class ConfigError(Exception):
    """配置错误基类"""
    pass


class YAMLValidationError(ConfigError):
    """YAML验证错误"""
    pass