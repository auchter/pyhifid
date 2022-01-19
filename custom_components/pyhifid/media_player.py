"""Support for pyhifid instances"""
from __future__ import annotations

import logging
import voluptuous as vol

from pyhifid.client import Client

from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    SUPPORT_SELECT_SOUND_MODE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from homeassistant.const import CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

SUPPORT_PYHIFID = (
    SUPPORT_VOLUME_STEP
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_VOLUME_SET
    | SUPPORT_SELECT_SOUND_MODE
)

DEFAULT_NAME = "pyhifid"
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the pyhifid platform."""
    pyhifid = PyhifidDevice(config[CONF_NAME], config[CONF_HOST])
    pyhifid.update()
    add_entities([pyhifid])


class PyhifidDevice(MediaPlayerEntity):
    def __init__(self, name, url):
        self._name = name
        self._url = url
        self._client = Client(url)

        self._volume = None
        self._output = None
        self._outputs = None
        self._muted = None
        self._power = None

    def update(self):
        self._volume = self._client.get_volume()
        self._output = self._client.get_output()
        self._outputs = self._client.get_outputs()
        self._muted = self._client.muted()
        self._power = self._client.is_on()

        return True

    def turn_on(self):
        self._client.turn_on()

    def turn_off(self):
        self._client.turn_off()

    def mute_volume(self, mute):
        self._client.mute(mute)

    def set_volume_level(self, volume):
        volume *= 255.0
        self._client.set_volume(volume)

    def volume_up(self):
        self._client.adjust_volume(1)

    def volume_down(self):
        self._client.adjust_volume(-1)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        if self._power:
            return STATE_ON
        return STATE_OFF

    @property
    def is_volume_muted(self):
        return self._muted

    @property
    def volume_level(self):
        return self._volume / 255.0

    @property
    def supported_features(self):
        return SUPPORT_PYHIFID

    @property
    def sound_mode(self):
        return self._output

    @property
    def sound_mode_list(self):
        return self._outputs

    def select_sound_mode(self, sound_mode):
        self._client.set_output(sound_mode)
