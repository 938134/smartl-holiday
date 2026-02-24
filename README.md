Smart Workday 智能工作日
https://img.shields.io/badge/HACS-Custom-41BDF5.svg
https://img.shields.io/badge/version-2.0.0-blue

智能工作日是一个 Home Assistant 集成，用于根据法定节假日、学校假期和自定义假期智能判断当天是否为工作日。

✨ 功能特点
多模式支持：工薪模式、学生模式、自由模式

灵活配置：通过 YAML 文件自定义假期

日历集成：在 HA 日历中显示所有假期

多实体：主传感器 + 5个二进制传感器

多语言：支持中文/英文

📦 安装
HACS 安装（推荐）
打开 HACS → 集成 → 右上角菜单 → 自定义仓库

添加仓库：https://github.com/938134/smart-workday

搜索 "Smart Workday" 并安装

手动安装
将 custom_components/smart_workday 文件夹复制到 HA 的 custom_components 目录

⚙️ 配置
首次配置
设置 → 设备与服务 → 添加集成 → 搜索 "Smart Workday"

选择假期模式：

👔 工薪模式：法定节假日 + 自定义假期（上班族）

📚 学生模式：法定节假日 + 学校假期 + 自定义假期（学生/教师）

🌟 自由模式：仅自定义假期（自由职业者）

修改配置
在集成卡片上点击"配置"，可以：

切换假期模式

编辑 calendar.yaml 自定义假期

📝 假期配置
配置文件位于：/config/custom_components/smart_workday/calendar.yaml

配置格式
yaml
# 法定节假日（工薪/学生模式生效）
holidays:
  - date: "2026-01-01"          # 单天事件
    name: "元旦"
  - start: "2026-02-17"         # 范围事件
    end: "2026-02-23"
    name: "春节"
  - date: "2026-01-04"          # 调休上班日
    name: "元旦调休"

# 自定义假期（所有模式生效）
customdays:
  - date: "2026-03-12"
    name: "植树节"

# 学校假期（仅学生模式生效）
schooldays:
  - start: "2026-07-10"
    end: "2026-08-31"
    name: "暑假"
📊 生成的实体
主传感器
实体ID：sensor.smart_workday

状态："是/否"（是否为工作日）

属性：包含所有详细信息

二进制传感器
实体ID	说明
binary_sensor.smart_workday_workday	是否为工作日
binary_sensor.smart_workday_holiday	是否为假日
binary_sensor.smart_workday_weekend	是否为周末
binary_sensor.smart_workday_special_workday	是否为调休日
binary_sensor.smart_workday_school_holiday	是否为学校假期
日历实体
实体ID：calendar.smart_workday_calendar

显示所有假期事件


📚 更新日志
v2.0.0
✨ 重构为配置流

✨ 新增日历实体

✨ 新增二进制传感器

✨ 支持多语言

✨ 内置 YAML 编辑器
