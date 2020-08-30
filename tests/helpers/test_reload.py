"""Tests for the reload helper."""
import logging
from os import path

import pytest

from homeassistant import config
from homeassistant.const import SERVICE_RELOAD
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.reload import (
    async_get_platform,
    async_integration_yaml_config,
    async_reload_integration_platforms,
    async_setup_reload_service,
)

from tests.async_mock import Mock, patch
from tests.common import (
    MockModule,
    MockPlatform,
    mock_entity_platform,
    mock_integration,
)

_LOGGER = logging.getLogger(__name__)
DOMAIN = "test_domain"
PLATFORM = "test_platform"


async def test_reload_platform(hass):
    """Test the polling of only updated entities."""
    component_setup = Mock(return_value=True)

    setup_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    mock_integration(hass, MockModule(DOMAIN, setup=component_setup))
    mock_integration(hass, MockModule(PLATFORM, dependencies=[DOMAIN]))

    mock_platform = MockPlatform(async_setup_platform=setup_platform)
    mock_entity_platform(hass, f"{DOMAIN}.{PLATFORM}", mock_platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await hass.async_block_till_done()
    assert component_setup.called

    assert f"{DOMAIN}.{PLATFORM}" in hass.config.components
    assert len(setup_called) == 1

    platform = async_get_platform(hass, PLATFORM, DOMAIN)
    assert platform.platform_name == PLATFORM
    assert platform.domain == DOMAIN

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "helpers/reload_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await async_reload_integration_platforms(hass, PLATFORM, [DOMAIN])

    assert len(setup_called) == 2


async def test_setup_reload_service(hass):
    """Test setting up a reload service."""
    component_setup = Mock(return_value=True)

    setup_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    mock_integration(hass, MockModule(DOMAIN, setup=component_setup))
    mock_integration(hass, MockModule(PLATFORM, dependencies=[DOMAIN]))

    mock_platform = MockPlatform(async_setup_platform=setup_platform)
    mock_entity_platform(hass, f"{DOMAIN}.{PLATFORM}", mock_platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await hass.async_block_till_done()
    assert component_setup.called

    assert f"{DOMAIN}.{PLATFORM}" in hass.config.components
    assert len(setup_called) == 1

    await async_setup_reload_service(hass, PLATFORM, [DOMAIN])

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "helpers/reload_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            PLATFORM,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert len(setup_called) == 2


async def test_async_integration_yaml_config(hass):
    """Test loading yaml config for an integration."""
    mock_integration(hass, MockModule(DOMAIN))

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        f"helpers/{DOMAIN}_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        processed_config = await async_integration_yaml_config(hass, DOMAIN)

    assert processed_config == {DOMAIN: [{"name": "one"}, {"name": "two"}]}


async def test_async_integration_missing_yaml_config(hass):
    """Test loading missing yaml config for an integration."""
    mock_integration(hass, MockModule(DOMAIN))

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "helpers/does_not_exist_configuration.yaml",
    )
    with pytest.raises(FileNotFoundError), patch.object(
        config, "YAML_CONFIG_FILE", yaml_path
    ):
        await async_integration_yaml_config(hass, DOMAIN)


def _get_fixtures_base_path():
    return path.dirname(path.dirname(__file__))
