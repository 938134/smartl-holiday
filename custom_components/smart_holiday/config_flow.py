"""Config flow for Smart Holiday integration."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DEFAULT_NAME, DOMAIN

class SmartHolidayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Holiday."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={}
            )

        # 直接显示确认界面，无需任何配置
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({})  # 空表单
        )