# SmartL Holiday 智能假期

[![HACS Custom][hacs-shield]][hacs]
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]

[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs]: https://hacs.xyz/
[releases-shield]: https://img.shields.io/github/v/release/你的用户名/smartl-holiday
[releases]: https://github.com/你的用户名/smartl-holiday/releases
[license-shield]: https://img.shields.io/github/license/你的用户名/smartl-holiday
[license]: https://github.com/你的用户名/smartl-holiday/blob/main/LICENSE

支持中国法定节假日、调休、寒暑假、秋假等自定义假期的 Home Assistant 集成。

## 功能特点

- ✅ **法定节假日**：自动识别国家法定节假日
- ✅ **调休上班日**：正确处理周末调休上班
- ✅ **学校假期**：支持寒假、暑假、秋假等
- ✅ **自定义节日**：记录但不影响工作日判断
- ✅ **灵活配置**：通过 YAML 文件自由定义
- ✅ **HACS 支持**：可通过 HACS 一键安装
- ✅ **本地化**：支持中英文界面

## 安装方法

### 方法一：HACS 安装（推荐）
1. 打开 HACS → 右上角菜单 → "自定义仓库"
2. 仓库地址：`https://github.com/你的用户名/smartl-holiday`
3. 类别：Integration
4. 点击 "ADD"
5. 搜索 "SmartL Holiday" 并安装
6. 重启 Home Assistant

### 方法二：手动安装
1. 下载最新 [Release](https://github.com/你的用户名/smartl-holiday/releases)
2. 解压到 `custom_components/smartl_holiday`
3. 重启 Home Assistant

## 配置方法

### 1. 创建日历配置文件
在 Home Assistant 配置目录下创建 `calendar.yaml`：

```yaml
# 法定节假日（支持单天和范围）
holidays:
  - { start: "2026-01-01", end: "2026-01-03", name: "元旦" }
  - { start: "2026-02-17", end: "2026-02-23", name: "春节" }
  - { start: "2026-04-04", end: "2026-04-06", name: "清明节" }
  - { start: "2026-05-01", end: "2026-05-05", name: "劳动节" }
  - { start: "2026-06-19", end: "2026-06-21", name: "端午节" }
  - { start: "2026-09-25", end: "2026-09-27", name: "中秋节" }
  - { start: "2026-10-01", end: "2026-10-07", name: "国庆节" }

# 学校假期（寒暑假、秋假等）
school_holidays:
  - { start: "2026-01-20", end: "2026-02-15", name: "寒假" }
  - { start: "2026-07-10", end: "2026-08-31", name: "暑假" }
  - { start: "2026-10-20", end: "2026-10-24", name: "秋假" }

# 调休上班日
workdays_special:
  - { date: "2026-01-04", name: "元旦调休" }
  - { date: "2026-02-14", name: "春节调休" }
  - { date: "2026-02-28", name: "春节调休" }
  - { date: "2026-05-09", name: "劳动节调休" }
  - { date: "2026-09-20", name: "中秋节调休" }
  - { date: "2026-10-10", name: "国庆节调休" }

# 自定义节日（仅记录，不影响工作日判断）
customdays:
  - { date: "2026-01-05", name: "阿弥陀佛诞" }
  - { date: "2026-03-12", name: "孙中山逝世（植树节）" }
  - { date: "2026-05-10", name: "母亲节" }