"""Config flow for Vikunja Home Assistant integration."""
from __future__ import annotations
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_URL, CONF_API_TOKEN, DEFAULT_URL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default=DEFAULT_URL): str,
        vol.Required(CONF_API_TOKEN): str,
    }
)


async def validate_input(data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input by hitting the Vikunja API info endpoint."""
    session = async_get_clientsession()
    url = data[CONF_URL].rstrip("/")
    headers = {"Authorization": f"Bearer {data[CONF_API_TOKEN]}"}

    try:
        resp = await session.get(f"{url}/api/v1/info", headers=headers, timeout=10)
        if resp.status == 200:
            info = await resp.json()
            return {"title": info.get("vikunja_version", "Vikunja")}
        if resp.status == 401:
            raise ValueError("Invalid API token — check your Vikunja settings")
        resp.raise_for_status()
    except ValueError:
        raise
    except Exception as exc:
        _LOGGER.exception("Failed to connect to Vikunja")
        raise CannotConnect from exc

    raise CannotConnect


class VikunjaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vikunja."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(user_input)
                await self.async_set_unique_id(info["title"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except ValueError as e:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""
