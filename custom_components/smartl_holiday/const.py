"""Constants for SmartL Holiday integration."""

DOMAIN = "smartl_holiday"
DEFAULT_NAME = "SmartL Holiday"
DEFAULT_SCAN_INTERVAL = 3600  # 1小时

# 配置项
CONF_CALENDAR_FILE = "calendar_file"
CONF_UPDATE_INTERVAL = "update_interval"

# 假期类型
HOLIDAY_TYPE_NATIONAL = "national"      # 法定节假日
HOLIDAY_TYPE_SCHOOL = "school"          # 学校假期
HOLIDAY_TYPE_WORKDAY_SPECIAL = "special" # 调休上班日
HOLIDAY_TYPE_CUSTOM = "custom"           # 自定义节日

# 状态值
STATE_WORKDAY = "workday"                # 工作日
STATE_HOLIDAY = "holiday"                 # 节假日
STATE_WORKDAY_SPECIAL = "workday_special" # 调休上班日
STATE_WEEKEND = "weekend"                  # 周末

# 属性名
ATTR_HOLIDAY_NAME = "holiday_name"
ATTR_HOLIDAY_TYPE = "holiday_type"
ATTR_TODAY_EVENTS = "today_events"
ATTR_UPCOMING = "upcoming_days"