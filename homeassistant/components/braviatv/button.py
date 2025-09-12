"""Button support for Bravia TV."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BraviaTVConfigEntry, BraviaTVCoordinator
from .entity import BraviaTVEntity


@dataclass(frozen=True, kw_only=True)
class BraviaTVButtonDescription(ButtonEntityDescription):
    """Bravia TV Button description."""

    press_action: Callable[[BraviaTVCoordinator], Coroutine]


BUTTONS: tuple[BraviaTVButtonDescription, ...] = (
    BraviaTVButtonDescription(
        key="reboot",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        press_action=lambda coordinator: coordinator.async_reboot_device(),
    ),
    BraviaTVButtonDescription(
        key="terminate_apps",
        translation_key="terminate_apps",
        entity_category=EntityCategory.CONFIG,
        press_action=lambda coordinator: coordinator.async_terminate_apps(),
    ),
)


def create_button_descriptions_for_remote_command_list(
    coordinator: BraviaTVCoordinator,
) -> list[BraviaTVButtonDescription]:
    """Creates a button description for each valid remote code."""

    def make_press_action_fn(
        command: str,
    ) -> Callable[[BraviaTVCoordinator], Coroutine]:
        async def press_action_fn(coordinator: BraviaTVCoordinator) -> None:
            await coordinator.async_send_command([command], 1)

        return press_action_fn

    return [
        BraviaTVButtonDescription(
            key=command,
            name=command,
            entity_registry_enabled_default=False,
            press_action=make_press_action_fn(command),
        )
        for command in coordinator.command_list
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: BraviaTVConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Bravia TV Button entities."""

    coordinator = config_entry.runtime_data
    unique_id = config_entry.unique_id
    assert unique_id is not None

    async_add_entities(
        BraviaTVButton(coordinator, unique_id, description)
        for description in list(BUTTONS)
        + create_button_descriptions_for_remote_command_list(coordinator)
    )


class BraviaTVButton(BraviaTVEntity, ButtonEntity):
    """Representation of a Bravia TV Button."""

    entity_description: BraviaTVButtonDescription

    def __init__(
        self,
        coordinator: BraviaTVCoordinator,
        unique_id: str,
        description: BraviaTVButtonDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, unique_id)
        self._attr_unique_id = f"{unique_id}_{description.key}"
        self.entity_description = description

    async def async_press(self) -> None:
        """Trigger the button action."""
        await self.entity_description.press_action(self.coordinator)
