"""Sensor platform for Vikunja Home Assistant integration."""
from __future__ import annotations
import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_URL,
    CONF_API_TOKEN,
    SAVED_FILTERS,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vikunja sensors based on a config entry."""
    url = entry.data[CONF_URL].rstrip("/")
    api_token = entry.data[CONF_API_TOKEN]
    session = async_get_clientsession(hass)

    coordinator = VikunjaDataCoordinator(hass, session, url, api_token)
    await coordinator.async_config_entry_first_refresh()

    sensors = []
    for filter_id, filter_name in SAVED_FILTERS.items():
        sensors.append(VikunjaTaskSensor(coordinator, filter_id, filter_name))

    async_add_entities(sensors)


class VikunjaDataCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch Vikunja task data for all saved filters."""

    def __init__(
        self,
        hass: HomeAssistant,
        session,
        url: str,
        api_token: str,
    ) -> None:
        """Initialize coordinator."""
        self._url = url
        self._headers = {"Authorization": f"Bearer {api_token}"}
        self._session = session

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[int, list[dict]]:
        """Fetch data for all saved filters in parallel."""
        import asyncio

        async def fetch_filter(filter_id: int) -> tuple[int, list[dict]]:
            try:
                resp = await self._session.get(
                    f"{self._url}/api/v1/tasks",
                    headers=self._headers,
                    params={"page": 1, "per_page": 50, "project_id": filter_id},
                    timeout=15,
                )
                if resp.status != 200:
                    return filter_id, []
                data = await resp.json()
                return filter_id, data if isinstance(data, list) else []
            except Exception as exc:
                _LOGGER.warning("Failed to fetch filter %s: %s", filter_id, exc)
                return filter_id, []

        results = await asyncio.gather(
            *[fetch_filter(fid) for fid in SAVED_FILTERS]
        )
        return dict(results)


class VikunjaTaskSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing a Vikunja saved filter."""

    def __init__(
        self,
        coordinator: VikunjaDataCoordinator,
        filter_id: int,
        filter_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._filter_id = filter_id
        self._attr_unique_id = f"vikunja_{filter_name.lower().replace(' ', '_')}"
        self._attr_name = f"Vikunja {filter_name}"
        self._attr_icon = "mdi:checkbox-marked-outline"

    @property
    def native_value(self) -> int:
        """Return the task count."""
        tasks = self.coordinator.data.get(self._filter_id, [])
        return len(tasks)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return tasks as a structured attribute."""
        tasks = self.coordinator.data.get(self._filter_id, [])
        return {
            "tasks": [
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "due_date": t.get("due_date"),
                    "priority": t.get("priority", 0),
                    "done": t.get("done", False),
                }
                for t in tasks[:20]
            ],
            "filter_id": self._filter_id,
            "filter_name": self._attr_name.replace("Vikunja ", ""),
        }
