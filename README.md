# Smart Holiday 智能假期

[![HACS Custom][hacs-shield]][hacs]
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]

[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs]: https://hacs.xyz/
[releases-shield]: https://img.shields.io/github/v/release/你的用户名/smart-holiday
[releases]: https://github.com/你的用户名/smart-holiday/releases
[license-shield]: https://img.shields.io/github/license/你的用户名/smart-holiday
[license]: https://github.com/你的用户名/smart-holiday/blob/main/LICENSE

支持中国法定节假日、调休、学校假期、自定义节日的 Home Assistant 集成。

## 功能特点

- ✅ **法定节假日**：自动识别国家法定节假日
- ✅ **调休上班日**：正确处理周末调休上班
- ✅ **自定义假期**：学校假期、佛诞、纪念日等
- ✅ **双实体设计**：传感器用于自动化，日历用于可视化
- ✅ **彩色日历**：不同类型假期不同颜色显示
- ✅ **未来预告**：查看未来7天假期安排
- ✅ **即装即用**：内置默认日历文件，无需额外配置

## 安装方法

### HACS 安装（推荐）
1. 打开 HACS → 右上角菜单 → "自定义仓库"
2. 仓库地址：`https://github.com/你的用户名/smart-holiday`
3. 类别：Integration
4. 点击 "ADD"
5. 搜索 "Smart Holiday" 并安装
6. 重启 Home Assistant

### 手动安装
1. 下载最新 Release
2. 解压到 `custom_components/smart_holiday`
3. 重启 Home Assistant

## 配置方法

### 直接添加集成
1. 设置 → 设备与服务 → 添加集成
2. 搜索 "Smart Holiday"
3. 点击提交，无需任何配置
4. 系统自动使用内置的 `calendar.yaml` 文件

### 自定义日历文件（可选）
如果你想修改假期数据，可以直接编辑：
`/config/custom_components/smart_holiday/calendar.yaml`

## 实体说明

### 传感器 `sensor.smart_holiday`
用于自动化判断：

| 状态 | 含义 | 闹钟规则 |
|------|------|----------|
| `workday` | 普通工作日 | ✅ 响 |
| `workday_special` | 调休上班日 | ✅ 响 |
| `holiday` | 法定节假日 | ❌ 不响 |
| `holiday_custom` | 自定义假期 | ❌ 不响 |
| `weekend` | 普通周末 | ❌ 不响 |

### 日历 `calendar.smart_holiday`
用于可视化展示：

| 事件类型 | 颜色 | 示例 |
|---------|------|------|
| 法定节假日 | 🔴 红色 | "国庆节" |
| 调休上班日 | 🟢 绿色 | "元旦调休" |
| 自定义假期 | 🔵 蓝色 | "寒假" |

## 自动化示例

```yaml
alias: 7点10起床闹钟
triggers:
  - at: "07:10:00"
    trigger: time
conditions:
  # 工作日或调休上班日才响
  - condition: template
    value_template: >
      {{ states('sensor.smart_holiday') in ['workday', 'workday_special'] }}
actions:
  # 主卧小爱：正常播报
  - action: script.小爱音箱控制
    data:
      speaker_name: 主卧小爱同学
      scene_preset: 起床
      repeat_times: 1
      custom_text: >
        {% set names = state_attr('sensor.smart_holiday', 'event_names') %}
        {% if names and names|length > 0 %}
          今天是{{ names|join('、') }}，早上好
        {% else %}
          早上好
        {% endif %}
  
  # 小乐小爱：只在没有自定义假期时响
  - if:
      - condition: template
        value_template: >
          {% set types = state_attr('sensor.smart_holiday', 'event_types') %}
          {{ 'custom' not in types }}
    then:
      - action: script.小爱音箱控制
        data:
          speaker_name: 小乐小爱同学
          scene_preset: 起床
          repeat_times: 1
mode: single