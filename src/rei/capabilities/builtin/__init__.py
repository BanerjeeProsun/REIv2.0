from rei.capabilities.registry import CapabilityRegistry
from rei.capabilities.builtin.apps import apps_open_spec, apps_open_handler, apps_close_spec, apps_close_handler
from rei.capabilities.builtin.web import web_open_url_spec, web_open_url_handler
from rei.capabilities.builtin.media import (
    media_set_volume_spec,
    media_set_volume_handler,
    media_control_spec,
    media_control_handler,
)
from rei.capabilities.builtin.system import (
    system_lock_spec,
    system_lock_handler,
    system_power_spec,
    system_power_handler,
)
from rei.capabilities.builtin.files import files_download_spec, files_download_handler


def register_builtin(registry: CapabilityRegistry) -> None:
    registry.register(apps_open_spec, apps_open_handler)
    registry.register(apps_close_spec, apps_close_handler)
    registry.register(web_open_url_spec, web_open_url_handler)
    registry.register(media_set_volume_spec, media_set_volume_handler)
    registry.register(media_control_spec, media_control_handler)
    registry.register(system_lock_spec, system_lock_handler)
    registry.register(system_power_spec, system_power_handler)
    registry.register(files_download_spec, files_download_handler)


__all__ = ["register_builtin"]
