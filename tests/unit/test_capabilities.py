import pytest
from pydantic import ValidationError
from rei.capabilities.registry import CapabilityRegistry, UnknownCapabilityError
from rei.capabilities.builtin import register_builtin
from rei.capabilities.builtin.apps import OpenAppArgs
from rei.capabilities.builtin.media import SetVolumeArgs


def test_registry_registration() -> None:
    registry = CapabilityRegistry()
    register_builtin(registry)

    specs = registry.get_all_specs()
    assert len(specs) >= 7

    # Try fetching a known spec
    spec = registry.get_spec("media.set_volume")
    assert spec.tier.value == "R1"


def test_unknown_capability_execution() -> None:
    registry = CapabilityRegistry()
    register_builtin(registry)

    with pytest.raises(UnknownCapabilityError):
        registry.execute("unknown.capability", OpenAppArgs(app="notepad"))


def test_capability_arguments_strictness() -> None:
    # Must fail because out of bounds
    with pytest.raises(ValidationError):
        SetVolumeArgs(level=150)

    # Must fail because of extra argument
    with pytest.raises(ValidationError):
        SetVolumeArgs(level=50, extra_arg="sneaky") 
