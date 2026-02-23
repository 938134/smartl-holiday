"""Constants for SmartL Holiday integration."""

DOMAIN = "smartl_holiday"
DEFAULT_NAME = "SmartL Holiday"
DEFAULT_SCAN_INTERVAL = 3600

# 配置项
CONF_CALENDAR_FILE = "calendar_file"

# 状态值
STATE_WORKDAY = "workday"
STATE_WORKDAY_SPECIAL = "workday_special"
STATE_HOLIDAY = "holiday"
STATE_HOLIDAY_CUSTOM = "holiday_custom"
STATE_WEEKEND = "weekend"

# 事件类型
EVENT_TYPE_NATIONAL = "national"
EVENT_TYPE_CUSTOM = "custom"

# 属性名
ATTR_TODAY_EVENTS = "today_events"
ATTR_EVENT_NAMES = "event_names"
ATTR_EVENT_TYPES = "event_types"
ATTR_PRIMARY_EVENT = "primary_event"
ATTR_IS_HOLIDAY = "is_holiday"
ATTR_IS_WORKDAY_SPECIAL = "is_workday_special"
ATTR_UPCOMING = "upcoming_days"