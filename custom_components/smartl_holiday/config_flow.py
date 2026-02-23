"""Config flow for SmartL Holiday integration."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .const import CONF_CALENDAR_FILE, DEFAULT_NAME, DOMAIN

class SmartLHolidayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartL Holiday."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("name", DEFAULT_NAME),
                data=user_input
            )

        # 获取可用的YAML文件列表
        yaml_files = await self._get_yaml_files()
        
        data_schema = vol.Schema({
            vol.Required("name", default=DEFAULT_NAME): selector.TextSelector(),
            vol.Required(CONF_CALENDAR_FILE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=yaml_files,
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),
            vol.Optional("update_interval", default=3600): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=60,
                    max=86400,
                    unit_of_measurement="秒",
                    mode=selector.NumberSelectorMode.BOX
                )
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    async def _get_yaml_files(self) -> list:
        """Get list of YAML files in config directory."""
        import os
        from homeassistant.config import YAML_CONFIG_FILE
        
        config_dir = os.path.dirname(self.hass.config.path(YAML_CONFIG_FILE))
        yaml_files = []
        
        try:
            for file in os.listdir(config_dir):
                if file.endswith(('.yaml', '.yml')):
                    yaml_files.append(file)
        except Exception:
            pass
            
        return yaml_files or ["calendar.yaml"]