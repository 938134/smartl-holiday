"""Config flow for Smart Workday."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
import logging
import yaml
import os
import aiofiles
from typing import Any, Dict, Optional

from .const import (
    DOMAIN, 
    DEFAULT_NAME, 
    HolidayMode,
    DEFAULT_YAML_TEMPLATE,
)

_LOGGER = logging.getLogger(__name__)


class SmartWorkdayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """配置流 - 处理首次添加集成"""
    
    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """第一步：输入名称和选择模式"""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("name", DEFAULT_NAME),
                data={
                    "name": user_input.get("name", DEFAULT_NAME),
                    "holiday_mode": user_input.get("holiday_mode", HolidayMode.WAGE.value),
                    "calendar_file": "calendar.yaml",
                }
            )

        # 模式选项
        mode_options = [
            selector.SelectOptionDict(
                value=mode.value, 
                label=f"{mode.icon} {mode.display_name}"
            )
            for mode in HolidayMode
        ]

        # 构建紧凑的模式说明
        mode_description = self._build_mode_description()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name", default=DEFAULT_NAME): selector.TextSelector(),
                vol.Required("holiday_mode", default=HolidayMode.WAGE.value): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=mode_options,
                        mode="dropdown",
                    )
                ),
            }),
            description_placeholders={"mode_description": mode_description}
        )

    def _build_mode_description(self) -> str:
        """构建紧凑的模式说明"""
        lines = []
        lines.append("📌 **假期模式**")
        for mode in HolidayMode:
            lines.append(f"  • {mode.icon} {mode.display_name}：{mode.description}")
        return "\n".join(lines)

    @staticmethod
    def async_get_options_flow(config_entry):
        """获取选项流"""
        return SmartWorkdayOptionsFlow(config_entry)


class SmartWorkdayOptionsFlow(config_entries.OptionsFlow):
    """选项流 - 处理配置修改"""
    
    def __init__(self, config_entry):
        """初始化"""
        self._config_entry = config_entry
        self._calendar_path = None
        self._yaml_content = None

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None):
        """第一步：模式选择和YAML编辑"""
        # 获取日历文件路径
        calendar_file = self._config_entry.data.get("calendar_file", "calendar.yaml")
        self._calendar_path = self.hass.config.path(
            "custom_components", DOMAIN, calendar_file
        )
        
        # 读取当前YAML内容
        if not self._yaml_content:
            self._yaml_content = await self._read_yaml_file()
        
        if user_input is not None:
            return await self._handle_user_input(user_input)
        
        return await self._show_form({})

    async def _read_yaml_file(self) -> str:
        """读取YAML文件内容"""
        try:
            if os.path.exists(self._calendar_path):
                async with aiofiles.open(self._calendar_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    return content if content.strip() else DEFAULT_YAML_TEMPLATE
            else:
                # 文件不存在，创建默认文件
                async with aiofiles.open(self._calendar_path, 'w', encoding='utf-8') as f:
                    await f.write(DEFAULT_YAML_TEMPLATE)
                return DEFAULT_YAML_TEMPLATE
        except Exception as e:
            _LOGGER.error("读取YAML文件失败: %s", e)
            return DEFAULT_YAML_TEMPLATE

    def _build_sections_text(self) -> str:
        """构建紧凑的假期类型说明"""
        lines = []
        lines.append("📋 **假期类型**")
        lines.append("  • **holidays**：法定节假日(含调休) - 工薪/学生模式生效")
        lines.append("  • **customdays**：自定义假期 - 所有模式生效")
        lines.append("  • **studentdays**：学生假期 - 仅学生模式生效")  # 修改这里
        lines.append("")
        lines.append(f"📁 **配置文件**：`{self._calendar_path}`")
        return "\n".join(lines)

    async def _handle_user_input(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户输入"""
        errors = {}
        
        try:
            # 获取模式
            mode_value = user_input.get("holiday_mode")
            holiday_mode = HolidayMode(mode_value)
            
            # 获取YAML内容
            yaml_content = user_input.get("yaml_content", "").strip()
            
            # 验证非空
            if not yaml_content:
                errors["yaml_content"] = "empty_content"
                return await self._show_form(errors)
            
            # 验证YAML格式
            try:
                data = yaml.safe_load(yaml_content)
                if not isinstance(data, dict):
                    errors["yaml_content"] = "invalid_yaml_structure"
                    return await self._show_form(errors)
                
                # 确保必要的键存在
                data.setdefault("holidays", [])
                data.setdefault("customdays", [])
                data.setdefault("schooldays", [])
                
                # 验证数据结构
                for key in ["holidays", "customdays", "schooldays"]:
                    if not isinstance(data[key], list):
                        errors["yaml_content"] = "invalid_yaml_structure"
                        return await self._show_form(errors)
                
            except yaml.YAMLError as e:
                _LOGGER.error("YAML解析错误: %s", e)
                errors["yaml_content"] = "invalid_yaml"
                return await self._show_form(errors)
            
            # 保存YAML文件
            try:
                async with aiofiles.open(self._calendar_path, 'w', encoding='utf-8') as f:
                    await f.write(yaml_content)
                _LOGGER.info("YAML文件保存成功: %s", self._calendar_path)
            except Exception as e:
                _LOGGER.error("保存YAML文件失败: %s", e)
                errors["base"] = "save_failed"
                return await self._show_form(errors)
            
            # 更新配置中的模式
            new_data = dict(self._config_entry.data)
            new_data["holiday_mode"] = holiday_mode.value
            self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)
            
            # 触发重新加载
            await self.hass.config_entries.async_reload(self._config_entry.entry_id)
            
            return self.async_create_entry(title="", data={})
            
        except ValueError as e:
            _LOGGER.error("模式值错误: %s", e)
            errors["base"] = "unknown_error"
            return await self._show_form(errors)
        except Exception as e:
            _LOGGER.error("保存配置失败: %s", e)
            errors["base"] = "unknown_error"
            return await self._show_form(errors)

    async def _show_form(self, errors: Dict[str, str]):
        """显示配置表单"""
        current_mode = self._config_entry.data.get("holiday_mode", HolidayMode.WAGE.value)
        
        # 模式选项
        mode_options = [
            selector.SelectOptionDict(
                value=mode.value, 
                label=f"{mode.icon} {mode.display_name}"
            )
            for mode in HolidayMode
        ]
        
        # 构建紧凑的假期类型说明
        sections_text = self._build_sections_text()
        
        # 表单架构
        schema = vol.Schema({
            vol.Required("holiday_mode", default=current_mode): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=mode_options,
                    mode="dropdown",
                )
            ),
            vol.Required("yaml_content", default=self._yaml_content): selector.TemplateSelector(),
        })
        
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders={"sections": sections_text}
        )